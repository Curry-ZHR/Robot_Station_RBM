#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import shutil
import threading
import time
from email.utils import formatdate
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from modules.auth import get_auth_manager
from modules.control.chassis import chassis_limits, publish_chassis_velocity, reset_chassis_odometry, stop_chassis
from modules.control.lifting import (
    clear_lifting_error,
    initialize_lifting,
    jog_lifting,
    lifting_limits,
    lifting_target_height_m,
    move_lifting_to_height,
    stop_lifting,
    zero_lifting_position,
)
from modules.control.piper import publish_joint_targets
from modules.data_collection import get_action_mirror, shutdown_action_mirror, start_action_mirror
from modules.drivers.can.can_activate import activate_can
from modules.inference import get_inference_manager
from modules.logger import get_logger, setup_logger
from modules.map import get_mapping_manager, mapping_result_status
from modules.playback import load_playback_dataset, playback_result_status
from modules.playback_manager import get_playback_manager
from modules.robot_description import RobotModelError, get_model, list_models, resolve_model_asset
from modules.ros_io import (
    get_camera_image_reader,
    get_lidar_point_cloud_reader,
    get_ros_reader,
    get_ros_writer,
    shutdown_ros_io,
)
from modules.runtime import get_service_manager, shutdown_services
from modules.self_check.can_check.can_status import check_can_interface
from modules.self_check.disk_check.disk_space import check_disk_space
from modules.self_check.gpu_check.gpu_status import check_gpu_status
from modules.self_check.ros_check.ros_daemon import ensure_ros_daemon


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
LOGGER = get_logger()
AUTH_COOKIE = "robot_station_session"
MODEL_ASSET_CACHE_SECONDS = int(os.environ.get("ROBOT_STATION_MODEL_ASSET_CACHE_SECONDS", "86400"))


def env_flag(name, default=True):
    raw = os.environ.get(name)
    if raw is None:
        return default
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off", ""}:
        return False
    return default


def autostart_transforms():
    if not env_flag("ROBOT_STATION_AUTOSTART_TRANSFORMS", True):
        LOGGER.info("Static transform autostart disabled")
        return None

    manager = get_service_manager()
    status = manager.get_service("transforms")
    if not status.get("ok"):
        LOGGER.info("Static transform service not available: %s", status.get("detail", "unknown"))
        return status

    result = manager.start_service("transforms")
    log_action_result("Service transforms start", result)
    return result


def log_check_result(result):
    name = result.get("name", "unknown")
    status = result.get("status", "未知")
    code = result.get("code", "")
    detail = result.get("detail", "")
    message = f"{name} self-check: {status} {code} - {detail}"
    if status == "正常":
        LOGGER.success(message)
    elif status == "警告":
        LOGGER.warning(message)
    else:
        LOGGER.error(message)


def log_action_result(action, result):
    code = result.get("code", "")
    detail = result.get("detail", "")
    message = f"{action}: {code} - {detail}"
    if result.get("ok"):
        LOGGER.success(message)
    else:
        LOGGER.error(message)


def api_tail(path, prefix):
    if path == prefix:
        return ""
    marker = f"{prefix}/"
    if path.startswith(marker):
        return unquote(path[len(marker):])
    return None


def query_float(query, key, default=0.0, minimum=0.0, maximum=5.0):
    values = parse_qs(query).get(key)
    if not values:
        return default
    try:
        value = float(values[0])
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))


def query_int(query, key, default=None, minimum=None, maximum=None):
    values = parse_qs(query).get(key)
    if not values:
        return default
    try:
        value = int(values[0])
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def query_bool(query, key, default=False):
    values = parse_qs(query).get(key)
    if not values:
        return default
    value = str(values[0]).strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def ros_result_status(result):
    if result.get("ok"):
        return 200
    code = result.get("code", "")
    if code.endswith("UNKNOWN"):
        return 404
    if code.endswith("NODATA"):
        return 200
    if code.endswith("PAYLOAD"):
        return 400
    if code.endswith("UNAVAILABLE"):
        return 503
    return 500


def service_result_status(result):
    if result.get("ok"):
        return 200
    code = result.get("code", "")
    if code.endswith("UNKNOWN"):
        return 404
    if code.endswith("ACTION"):
        return 400
    return 500


def camera_result_status(result):
    if result.get("ok"):
        return 200
    code = result.get("code", "")
    if code.endswith("UNKNOWN"):
        return 404
    if code.endswith("NODATA"):
        return 404
    if code.endswith("UNAVAILABLE"):
        return 503
    return 500


def lidar_result_status(result):
    if result.get("ok"):
        return 200
    code = result.get("code", "")
    if code.endswith("UNKNOWN"):
        return 404
    if code.endswith("NODATA"):
        return 200
    if code.endswith("UNAVAILABLE"):
        return 503
    return 500


def inference_result_status(result):
    if result.get("ok"):
        return 200
    code = result.get("code", "")
    mapping = {
        "INFER-BUSY": 409,
        "INFER-WS-DISCONNECTED": 409,
        "INFER-NO-CHUNK": 409,
        "INFER-STOPPED": 200,
        "INFER-CHUNK-INVALID": 400,
        "INFER-WS-URL": 400,
        "INFER-WS-TIMEOUT": 504,
        "INFER-WS-CONNECT": 502,
        "INFER-WS-SEND": 502,
        "INFER-WS-RECV": 502,
        "INFER-WS-DEPENDENCY": 503,
        "INFER-OBS-CAMERA": 503,
        "INFER-OBS-JOINT": 503,
        "INFER-OBS-LIFT": 503,
        "INFER-MASK-NOFEEDBACK": 503,
    }
    return mapping.get(code, 500)


def auth_result_status(result):
    if result.get("ok"):
        return 200
    mapping = {
        "AUTH-CONFLICT": 409,
        "AUTH-INVALID": 401,
        "AUTH-REQUIRED": 401,
        "AUTH-REVOKED": 401,
    }
    return mapping.get(result.get("code", ""), 401)


def playback_control_status(result):
    if result.get("ok"):
        return 200
    code = result.get("code", "")
    mapping = {
        "PLAYBACK-BUSY": 409,
        "PLAYBACK-DISABLED": 409,
        "PLAYBACK-PATH": 400,
        "PLAYBACK-PAYLOAD": 400,
        "PLAYBACK-ACTION": 400,
        "PLAYBACK-NODATA": 400,
        "PLAYBACK-TIMESTAMP": 400,
        "PLAYBACK-UNSUPPORTED": 400,
        "PLAYBACK-NOTFOUND": 404,
        "PLAYBACK-DEPENDENCY": 503,
        "PLAYBACK-PIPER-ENABLE": 503,
    }
    return mapping.get(code, 500)


def robot_model_error_status(error):
    if error.code.endswith("UNKNOWN") or error.code.endswith("MISSING"):
        return 404
    if error.code.endswith("DENIED"):
        return 403
    if error.code.endswith("PATH"):
        return 400
    return 500


def release_operator_outputs(reason):
    """Stop running tasks and hold motion outputs during operator handoff.

    This deliberately does not publish Piper enable=false. Disabling torque can
    make the arms drop; handoff only asks existing controllers to hold/stop.
    """

    LOGGER.warning("Operator session handoff: %s", reason)
    results = {}
    try:
        results["inference"] = get_inference_manager().disconnect()
    except Exception as exc:
        results["inference"] = {"ok": False, "detail": str(exc)}
        LOGGER.error("Inference handoff stop failed: %s", exc)
    try:
        results["playback"] = get_playback_manager().stop(reason=reason)
    except Exception as exc:
        results["playback"] = {"ok": False, "detail": str(exc)}
        LOGGER.error("Playback handoff stop failed: %s", exc)
    try:
        results["piperHold"] = publish_joint_targets({"hold": True})
    except Exception as exc:
        results["piperHold"] = {"ok": False, "detail": str(exc)}
        LOGGER.error("Piper handoff hold failed: %s", exc)
    try:
        results["chassisStop"] = stop_chassis({})
    except Exception as exc:
        results["chassisStop"] = {"ok": False, "detail": str(exc)}
        LOGGER.error("Chassis handoff stop failed: %s", exc)
    try:
        results["liftingStop"] = stop_lifting({})
    except Exception as exc:
        results["liftingStop"] = {"ok": False, "detail": str(exc)}
        LOGGER.error("Lifting handoff stop failed: %s", exc)
    return results


class RobotStationHandler(SimpleHTTPRequestHandler):
    server_version = "RobotStationHTTP/0.1"

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def log_message(self, format, *args):
        return

    def has_response_header(self, name):
        prefix = f"{name}:".encode("ascii", errors="ignore").lower()
        return any(line.lower().startswith(prefix) for line in getattr(self, "_headers_buffer", []))

    def end_headers(self):
        if not self.has_response_header("Cache-Control"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def auth_token(self):
        cookie_header = self.headers.get("Cookie", "")
        if not cookie_header:
            return None
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
        except Exception:
            return None
        morsel = cookie.get(AUTH_COOKIE)
        return morsel.value if morsel is not None else None

    def auth_cookie_header(self, token=None, max_age=None):
        parts = [f"{AUTH_COOKIE}={token or ''}", "Path=/", "SameSite=Lax", "HttpOnly"]
        if max_age is not None:
            parts.append(f"Max-Age={int(max_age)}")
        return "; ".join(parts)

    def require_operator(self):
        ok, result = get_auth_manager().require_operator(self.auth_token())
        if not ok:
            self.write_json(result, status=auth_result_status(result))
            return False
        return True

    def handle_auth_get(self, action):
        if action in ("", "status", "heartbeat"):
            result = get_auth_manager().status(self.auth_token())
            self.write_json(result, status=auth_result_status(result) if not result.get("authenticated") else 200)
            return
        self.write_json({"ok": False, "code": "AUTH-ACTION", "detail": f"Unsupported auth action: {action}"}, status=404)

    def handle_auth_post(self, action):
        if action in ("status", "heartbeat"):
            result = get_auth_manager().status(self.auth_token())
            self.write_json(result, status=auth_result_status(result) if not result.get("authenticated") else 200)
            return

        if action == "login":
            payload = self.read_json_body()
            client = self.client_address[0] if self.client_address else ""
            result, token = get_auth_manager().login(
                payload.get("username"),
                payload.get("password"),
                force=bool(payload.get("force")),
                client=client,
            )
            if result.get("ok") and result.get("code") == "AUTH-FORCED":
                result["handoff"] = release_operator_outputs(f"forced login by {result.get('user')}")
            headers = {}
            if token:
                max_age = max(3600, int(result.get("timeoutSec") or 0))
                headers["Set-Cookie"] = self.auth_cookie_header(token, max_age=max_age)
            self.write_json(result, status=auth_result_status(result), headers=headers)
            return

        if action == "logout":
            status = get_auth_manager().status(self.auth_token(), touch=False)
            result = get_auth_manager().logout(self.auth_token())
            if status.get("authenticated"):
                result["handoff"] = release_operator_outputs(f"logout by {status.get('user')}")
            self.write_json(
                result,
                status=auth_result_status(result),
                headers={"Set-Cookie": self.auth_cookie_header("", max_age=0)},
            )
            return

        self.write_json({"ok": False, "code": "AUTH-ACTION", "detail": f"Unsupported auth action: {action}"}, status=404)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json({"status": "ok"})
            return
        auth_action = api_tail(parsed.path, "/api/auth")
        if auth_action is not None:
            self.handle_auth_get(auth_action)
            return
        if parsed.path == "/api/control/lifting/limits":
            self.write_json(lifting_limits())
            return
        if parsed.path == "/api/control/chassis/limits":
            self.write_json(chassis_limits())
            return
        if parsed.path == "/api/robot-models":
            try:
                self.write_json(list_models())
            except RobotModelError as exc:
                self.write_json({"ok": False, "code": exc.code, "detail": exc.detail}, status=robot_model_error_status(exc))
            return
        model_key = api_tail(parsed.path, "/api/robot-models")
        if model_key is not None:
            if not model_key or "/" in model_key:
                self.write_json(
                    {
                        "ok": False,
                        "code": "MODEL-PATH",
                        "detail": "Robot model path must be /api/robot-models/<key>.",
                    },
                    status=404,
                )
                return
            result = get_model(model_key)
            self.write_json(result, status=200 if result.get("ok") else 404)
            return
        asset_tail = api_tail(parsed.path, "/api/robot-model-assets")
        if asset_tail is not None:
            parts = [part for part in asset_tail.split("/") if part]
            if len(parts) < 3:
                self.write_json(
                    {
                        "ok": False,
                        "code": "MODEL-ASSET-PATH",
                        "detail": "Robot model asset path must be /api/robot-model-assets/<family>/<key>/<relative-path>.",
                    },
                    status=404,
                )
                return
            family, key = parts[0], parts[1]
            relative_path = "/".join(parts[2:])
            try:
                asset_path = resolve_model_asset(family, key, relative_path)
            except RobotModelError as exc:
                self.write_json({"ok": False, "code": exc.code, "detail": exc.detail}, status=robot_model_error_status(exc))
                return
            self.write_file(
                asset_path,
                self.guess_type(str(asset_path)),
                headers={"Cache-Control": f"public, max-age={MODEL_ASSET_CACHE_SECONDS}"},
            )
            return
        camera_tail = api_tail(parsed.path, "/api/sensors/cameras")
        if camera_tail is not None:
            reader = get_camera_image_reader()
            if not camera_tail:
                result = reader.list_images()
                self.write_json(result, status=camera_result_status(result))
                return
            parts = [part for part in camera_tail.split("/") if part]
            if len(parts) == 3 and parts[2] == "stream":
                fps = query_float(parsed.query, "fps", default=8.0, minimum=1.0, maximum=15.0)
                self.write_camera_stream(reader, parts[0], parts[1], fps=fps)
                return
            if len(parts) == 3 and parts[2] == "frame":
                wait_sec = query_float(parsed.query, "wait", default=0.0, minimum=0.0, maximum=2.0)
                after_sequence = query_int(parsed.query, "after", default=None, minimum=0)
                result = reader.read_frame(parts[0], parts[1], timeout_sec=wait_sec, after_sequence=after_sequence)
                if not result.get("ok"):
                    self.write_json(result, status=camera_result_status(result))
                    return
                self.write_binary(
                    result["body"],
                    result["contentType"],
                    headers={
                        "X-Robot-Station-Frame-Age-Ms": str(result.get("ageMs", "")),
                        "X-Robot-Station-Frame-Stale": "1" if result.get("stale") else "0",
                        "X-Robot-Station-Render-Mode": str(result.get("renderMode", "")),
                        "X-Robot-Station-Frame-Sequence": str(result.get("sequence", "")),
                    },
                )
                return
            self.write_json(
                {
                    "ok": False,
                    "code": "CAM-R-UNKNOWN",
                    "detail": "Camera image path must be /api/sensors/cameras, /api/sensors/cameras/<camera>/<kind>/frame, or /api/sensors/cameras/<camera>/<kind>/stream.",
                },
                status=404,
            )
            return
        lidar_tail = api_tail(parsed.path, "/api/sensors/lidar")
        if lidar_tail is not None:
            reader = get_lidar_point_cloud_reader()
            if not lidar_tail:
                result = reader.list_clouds()
                self.write_json(result, status=lidar_result_status(result))
                return
            parts = [part for part in lidar_tail.split("/") if part]
            if len(parts) == 2 and parts[1] == "frame":
                wait_sec = query_float(parsed.query, "wait", default=0.0, minimum=0.0, maximum=2.0)
                after_sequence = query_int(parsed.query, "after", default=None, minimum=0)
                max_points = query_int(parsed.query, "max_points", default=None, minimum=1000, maximum=120000)
                result = reader.read_frame(
                    parts[0],
                    timeout_sec=wait_sec,
                    after_sequence=after_sequence,
                    max_points=max_points,
                )
                if not result.get("ok"):
                    self.write_json(result, status=lidar_result_status(result))
                    return
                self.write_binary(
                    result["body"],
                    result["contentType"],
                    headers={
                        "X-Robot-Station-PointCloud-Age-Ms": str(result.get("ageMs", "")),
                        "X-Robot-Station-PointCloud-Stale": "1" if result.get("stale") else "0",
                        "X-Robot-Station-PointCloud-Sequence": str(result.get("sequence", "")),
                        "X-Robot-Station-PointCloud-Point-Count": str(result.get("pointCount", "")),
                        "X-Robot-Station-PointCloud-Source-Point-Count": str(result.get("sourcePointCount", "")),
                        "X-Robot-Station-PointCloud-Stride-Floats": str(result.get("strideFloats", "")),
                        "X-Robot-Station-PointCloud-Frame-Id": str(result.get("frameId", "")),
                        "X-Robot-Station-PointCloud-Fields": ",".join(result.get("fields", [])),
                    },
                )
                return
            self.write_json(
                {
                    "ok": False,
                    "code": "LDR-R-UNKNOWN",
                    "detail": "LiDAR point cloud path must be /api/sensors/lidar or /api/sensors/lidar/<cloud>/frame.",
                },
                status=404,
            )
            return
        service_key = api_tail(parsed.path, "/api/runtime/services")
        if service_key is not None:
            manager = get_service_manager()
            if not service_key:
                self.write_json(manager.list_services())
                return
            result = manager.get_service(service_key)
            self.write_json(result, status=service_result_status(result))
            return
        ros_topic_key = api_tail(parsed.path, "/api/ros/topics")
        if ros_topic_key is not None:
            reader = get_ros_reader()
            if not ros_topic_key:
                self.write_json(reader.list_topics())
                return
            wait_sec = query_float(parsed.query, "wait", default=0.0, minimum=0.0, maximum=2.0)
            result = reader.read(ros_topic_key, timeout_sec=wait_sec)
            self.write_json(result, status=ros_result_status(result))
            return
        if parsed.path == "/api/ros/actions":
            self.write_json(get_ros_writer().list_actions())
            return
        if parsed.path == "/api/inference/status":
            self.write_json(get_inference_manager().status())
            return
        mapping_tail = api_tail(parsed.path, "/api/mapping")
        if mapping_tail is not None:
            if mapping_tail in ("", "status"):
                result = get_mapping_manager().status()
                self.write_json(result, status=mapping_result_status(result))
                return
            if mapping_tail == "map/frame":
                result = get_mapping_manager().read_map_frame()
                if not result.get("ok"):
                    self.write_json(result, status=mapping_result_status(result))
                    return
                self.write_binary(
                    result["body"],
                    result["contentType"],
                    headers={
                        "X-Robot-Station-PointCloud-Point-Count": str(result.get("pointCount", "")),
                        "X-Robot-Station-PointCloud-Source-Point-Count": str(result.get("sourcePointCount", "")),
                        "X-Robot-Station-PointCloud-Stride-Floats": str(result.get("strideFloats", "")),
                        "X-Robot-Station-PointCloud-Fields": ",".join(result.get("fields", [])),
                        "X-Robot-Station-Mapping-Session-Id": str(result.get("sessionId", "")),
                        "X-Robot-Station-Mapping-Capture-Count": str(result.get("captureCount", "")),
                        "X-Robot-Station-Mapping-Map-Size-Bytes": str(result.get("sizeBytes", "")),
                        "X-Robot-Station-Mapping-Map-Mtime-Ms": str(result.get("mtimeMs", "")),
                    },
                )
                return
            self.write_json(
                {
                    "ok": False,
                    "code": "MAP-ACTION",
                    "detail": "Mapping GET path must be /api/mapping/status or /api/mapping/map/frame.",
                },
                status=404,
            )
            return
        if parsed.path == "/api/playback/status":
            self.write_json(get_playback_manager().status())
            return
        if parsed.path == "/api/self-check/ros-daemon":
            result = ensure_ros_daemon()
            log_check_result(result)
            self.write_json(result)
            return
        if parsed.path == "/api/self-check/can-interface":
            auto_activate = query_bool(parsed.query, "auto_activate", default=True)
            result = check_can_interface(auto_activate=auto_activate)
            log_check_result(result)
            self.write_json(result)
            return
        if parsed.path == "/api/self-check/disk-space":
            result = check_disk_space()
            log_check_result(result)
            self.write_json(result)
            return
        if parsed.path == "/api/self-check/gpu-status":
            result = check_gpu_status()
            log_check_result(result)
            self.write_json(result)
            return
        if parsed.path.startswith("/api/"):
            self.write_json({"error": "not_found", "path": parsed.path}, status=404)
            return
        super().do_GET()

    def handle_chassis_control(self, chassis_action):
        payload = self.read_json_body()
        handlers = {
            "cmd_vel": publish_chassis_velocity,
            "velocity": publish_chassis_velocity,
            "reset_odom": reset_chassis_odometry,
            "reset-odom": reset_chassis_odometry,
            "stop": stop_chassis,
        }
        handler = handlers.get(chassis_action)
        if handler is None:
            self.write_json(
                {
                    "ok": False,
                    "code": "CHASSIS-C-ACTION",
                    "detail": f"Unsupported chassis action: {chassis_action}",
                },
                status=400,
            )
            return
        result = handler(payload)
        if result.get("ok") and not result.get("stale"):
            command = result.get("command")
            if isinstance(command, dict):
                try:
                    get_action_mirror().set_chassis_action(command)
                except Exception as exc:
                    LOGGER.warning("Action mirror chassis update failed: %s", exc)
        log_action_result(f"Chassis {chassis_action}", result)
        self.write_json(result, status=ros_result_status(result))

    def handle_piper_joint_targets(self):
        payload = self.read_json_body()
        result = publish_joint_targets(payload)
        log_action_result("Piper joint targets", result)
        self.write_json(result, status=ros_result_status(result))

    def handle_lifting_control(self, lifting_action):
        payload = self.read_json_body()
        handlers = {
            "init": initialize_lifting,
            "height": move_lifting_to_height,
            "jog": jog_lifting,
            "stop": stop_lifting,
            "clear-error": clear_lifting_error,
            "zero": zero_lifting_position,
        }
        handler = handlers.get(lifting_action)
        if handler is None:
            self.write_json(
                {
                    "ok": False,
                    "code": "LIFT-C-ACTION",
                    "detail": f"Unsupported lifting action: {lifting_action}",
                },
                status=400,
            )
            return
        if lifting_action == "height":
            try:
                lift_target_height_m = lifting_target_height_m(payload)
            except Exception as exc:
                result = {
                    "ok": False,
                    "code": "LIFT-C-PAYLOAD",
                    "detail": str(exc),
                    "limits": lifting_limits().get("limits", {}),
                }
                log_action_result("Lifting height", result)
                self.write_json(result, status=400)
                return
            try:
                get_action_mirror().set_lifting_action(lift_target_height_m)
            except Exception as exc:
                LOGGER.warning("Action mirror lifting update failed: %s", exc)
        result = handler(payload)
        log_action_result(f"Lifting {lifting_action}", result)
        self.write_json(result, status=ros_result_status(result))

    def handle_inference(self, action):
        manager = get_inference_manager()
        if action == "connect":
            payload = self.read_json_body()
            result = manager.connect(payload.get("url") or payload.get("remoteUrl"))
            log_action_result("Inference connect", result)
            self.write_json(result, status=inference_result_status(result))
            return
        if action == "request-chunk":
            payload = self.read_json_body()
            result = manager.request_chunk(payload)
            log_action_result("Inference request-chunk", result)
            self.write_json(result, status=inference_result_status(result))
            return
        if action == "execute-chunk":
            payload = self.read_json_body()
            result = manager.execute_chunk(payload)
            log_action_result("Inference execute-chunk", result)
            self.write_json(result, status=inference_result_status(result))
            return
        if action == "stop":
            result = manager.stop()
            log_action_result("Inference stop", result)
            self.write_json(result, status=inference_result_status(result))
            return
        if action == "disconnect":
            result = manager.disconnect()
            log_action_result("Inference disconnect", result)
            self.write_json(result, status=inference_result_status(result))
            return
        self.write_json(
            {
                "ok": False,
                "code": "INFER-ACTION",
                "detail": f"Unsupported inference action: {action}",
            },
            status=400,
        )

    def handle_mapping(self, action):
        manager = get_mapping_manager()
        if action in ("", "status"):
            result = manager.status()
            self.write_json(result, status=mapping_result_status(result))
            return
        if action == "start":
            payload = self.read_json_body()
            result = manager.start(payload)
            log_action_result("Mapping start", result)
            self.write_json(result, status=mapping_result_status(result))
            return
        if action == "capture":
            payload = self.read_json_body()
            result = manager.capture(payload)
            log_action_result("Mapping capture", result)
            self.write_json(result, status=mapping_result_status(result))
            return
        if action == "save":
            payload = self.read_json_body()
            result = manager.save(payload)
            log_action_result("Mapping save", result)
            self.write_json(result, status=mapping_result_status(result))
            return
        if action in ("delete-last", "delete_last", "remove-last"):
            payload = self.read_json_body()
            result = manager.delete_last(payload)
            log_action_result("Mapping delete last", result)
            self.write_json(result, status=mapping_result_status(result))
            return
        if action == "reset":
            payload = self.read_json_body()
            result = manager.reset(payload)
            log_action_result("Mapping reset", result)
            self.write_json(result, status=mapping_result_status(result))
            return
        self.write_json(
            {
                "ok": False,
                "code": "MAP-ACTION",
                "detail": f"Unsupported mapping action: {action}",
            },
            status=400,
        )

    def handle_playback(self, action):
        manager = get_playback_manager()
        if action == "enable":
            payload = self.read_json_body()
            result = manager.enable_piper(payload)
            log_action_result("Playback Piper enable", result)
            self.write_json(result, status=playback_control_status(result))
            return
        if action == "start":
            payload = self.read_json_body()
            result = manager.start(payload)
            log_action_result("Playback start", result)
            self.write_json(result, status=playback_control_status(result))
            return
        if action == "stop":
            result = manager.stop()
            log_action_result("Playback stop", result)
            self.write_json(result, status=playback_control_status(result))
            return
        self.write_json(
            {
                "ok": False,
                "code": "PLAYBACK-ACTION",
                "detail": f"Unsupported playback action: {action}",
            },
            status=400,
        )

    def do_POST(self):
        parsed = urlparse(self.path)
        auth_action = api_tail(parsed.path, "/api/auth")
        if auth_action is not None:
            self.handle_auth_post(auth_action)
            return
        if parsed.path.startswith("/api/") and not self.require_operator():
            return
        if parsed.path == "/api/control/piper/joint-targets":
            self.handle_piper_joint_targets()
            return
        chassis_action = api_tail(parsed.path, "/api/control/chassis")
        if chassis_action is not None:
            self.handle_chassis_control(chassis_action)
            return
        lifting_action = api_tail(parsed.path, "/api/control/lifting")
        if lifting_action is not None:
            self.handle_lifting_control(lifting_action)
            return
        service_tail = api_tail(parsed.path, "/api/runtime/services")
        if service_tail is not None:
            parts = [part for part in service_tail.split("/") if part]
            if len(parts) != 2:
                self.write_json(
                    {
                        "ok": False,
                        "code": "SVC-ACTION",
                        "detail": "Service action path must be /api/runtime/services/<key>/<action>.",
                    },
                    status=400,
                )
                return
            service_key, action = parts
            result = get_service_manager().perform(service_key, action)
            log_action_result(f"Service {service_key} {action}", result)
            self.write_json(result, status=service_result_status(result))
            return
        ros_action_key = api_tail(parsed.path, "/api/ros/actions")
        if ros_action_key is not None:
            if not ros_action_key:
                self.write_json({"error": "missing_action"}, status=400)
                return
            payload = self.read_json_body()
            result = get_ros_writer().publish(ros_action_key, payload)
            log_action_result(f"ROS action {ros_action_key}", result)
            self.write_json(result, status=ros_result_status(result))
            return
        inference_action = api_tail(parsed.path, "/api/inference")
        if inference_action is not None:
            self.handle_inference(inference_action)
            return
        mapping_action = api_tail(parsed.path, "/api/mapping")
        if mapping_action is not None:
            self.handle_mapping(mapping_action)
            return
        if parsed.path == "/api/playback/load":
            payload = self.read_json_body()
            result = load_playback_dataset(payload)
            self.write_json(result, status=playback_result_status(result))
            return
        playback_action = api_tail(parsed.path, "/api/playback")
        if playback_action is not None:
            self.handle_playback(playback_action)
            return
        if parsed.path == "/api/actions/can/activate":
            payload = self.read_json_body()
            interface = payload.get("interface")
            try:
                bitrate = int(payload["bitrate"]) if payload.get("bitrate") is not None else None
            except (TypeError, ValueError):
                LOGGER.error("CAN activate rejected: invalid bitrate %r", payload.get("bitrate"))
                self.write_json({"ok": False, "code": "CAN-A-BITRATE", "detail": "invalid bitrate"}, status=400)
                return
            result = activate_can(interface=interface, bitrate=bitrate)
            log_action_result("CAN activate", result)
            self.write_json(result)
            return
        if parsed.path.startswith("/api/"):
            self.write_json({"error": "not_found", "path": parsed.path}, status=404)
            return
        self.write_json({"error": "method_not_allowed"}, status=405)

    def translate_path(self, path):
        parsed = urlparse(path)
        clean_path = parsed.path.lstrip("/")
        if not clean_path:
            clean_path = "index.html"
        candidate = (FRONTEND_DIR / clean_path).resolve()
        try:
            candidate.relative_to(FRONTEND_DIR.resolve())
        except ValueError:
            return str(FRONTEND_DIR / "index.html")
        if candidate.is_dir():
            return str(candidate / "index.html")
        if candidate.exists():
            return str(candidate)
        return str(FRONTEND_DIR / "index.html")

    def guess_type(self, path):
        if path.endswith(".js"):
            return "application/javascript"
        if path.endswith(".css"):
            return "text/css"
        if path.endswith(".urdf"):
            return "application/xml"
        if path.endswith(".dae"):
            return "model/vnd.collada+xml"
        if path.endswith(".stl"):
            return "model/stl"
        return mimetypes.guess_type(path)[0] or "application/octet-stream"

    def write_json(self, payload, status=200, headers=None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def write_binary(self, body, content_type, status=200, headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def write_file(self, path, content_type, status=200, headers=None):
        stat_result = path.stat()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(stat_result.st_size))
        self.send_header("Last-Modified", formatdate(stat_result.st_mtime, usegmt=True))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        with path.open("rb") as handle:
            shutil.copyfileobj(handle, self.wfile, length=1024 * 1024)

    def write_camera_stream(self, reader, camera, kind, fps=8.0):
        result = reader.read_frame(camera, kind, timeout_sec=2.0)
        if not result.get("ok"):
            self.write_json(result, status=camera_result_status(result))
            return

        boundary = "robotstationframe"
        min_interval = 1.0 / max(1.0, fps)
        self.send_response(200)
        self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={boundary}")
        self.send_header("Connection", "close")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        last_sequence = None
        last_sent_at = 0.0
        while True:
            if not result.get("ok"):
                time.sleep(0.2)
                result = reader.read_frame(camera, kind, timeout_sec=2.0, after_sequence=last_sequence)
                continue

            sequence = result.get("sequence")
            if sequence != last_sequence:
                delay = min_interval - (time.monotonic() - last_sent_at)
                if delay > 0:
                    time.sleep(delay)
                try:
                    self.write_multipart_frame(boundary, result)
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                    return
                last_sequence = sequence
                last_sent_at = time.monotonic()

            result = reader.read_frame(camera, kind, timeout_sec=2.0, after_sequence=last_sequence)

    def write_multipart_frame(self, boundary, result):
        body = result["body"]
        header = (
            f"--{boundary}\r\n"
            f"Content-Type: {result['contentType']}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"X-Robot-Station-Frame-Age-Ms: {result.get('ageMs', '')}\r\n"
            f"X-Robot-Station-Frame-Stale: {'1' if result.get('stale') else '0'}\r\n"
            f"X-Robot-Station-Render-Mode: {result.get('renderMode', '')}\r\n"
            f"X-Robot-Station-Frame-Sequence: {result.get('sequence', '')}\r\n"
            "\r\n"
        ).encode("ascii")
        self.wfile.write(header)
        self.wfile.write(body)
        self.wfile.write(b"\r\n")
        self.wfile.flush()

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        body = self.rfile.read(length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}


class ChassisControlHandler(RobotStationHandler):
    server_version = "RobotStationChassisHTTP/0.1"

    def end_headers(self):
        origin = self.headers.get("Origin") or "*"
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json({"status": "ok", "role": "chassis-control"})
            return
        if parsed.path == "/api/control/chassis/limits":
            self.write_json(chassis_limits())
            return
        self.write_json({"error": "not_found", "path": parsed.path}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/") and not self.require_operator():
            return
        chassis_action = api_tail(parsed.path, "/api/control/chassis")
        if chassis_action is None:
            self.write_json({"error": "not_found", "path": parsed.path}, status=404)
            return
        self.handle_chassis_control(chassis_action)


class LiftingControlHandler(RobotStationHandler):
    """Dedicated low-latency endpoint for lifting control.

    Served on its own port so lifting commands get a separate browser
    connection pool and never queue behind the high-volume camera/LiDAR
    long-poll requests on the main port.
    """

    server_version = "RobotStationLiftingHTTP/0.1"

    def end_headers(self):
        origin = self.headers.get("Origin") or "*"
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json({"status": "ok", "role": "lifting-control"})
            return
        if parsed.path == "/api/control/lifting/limits":
            self.write_json(lifting_limits())
            return
        self.write_json({"error": "not_found", "path": parsed.path}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/") and not self.require_operator():
            return
        lifting_action = api_tail(parsed.path, "/api/control/lifting")
        if lifting_action is None:
            self.write_json({"error": "not_found", "path": parsed.path}, status=404)
            return
        self.handle_lifting_control(lifting_action)


class PiperControlHandler(RobotStationHandler):
    """Dedicated low-latency endpoint for Piper arm joint-target commands.

    Served on its own port so arm commands get a separate browser connection
    pool and never queue behind the high-volume camera/LiDAR long-poll
    requests on the main port.
    """

    server_version = "RobotStationPiperHTTP/0.1"

    def end_headers(self):
        origin = self.headers.get("Origin") or "*"
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json({"status": "ok", "role": "piper-control"})
            return
        self.write_json({"error": "not_found", "path": parsed.path}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/") and not self.require_operator():
            return
        if parsed.path == "/api/control/piper/joint-targets":
            self.handle_piper_joint_targets()
            return
        self.write_json({"error": "not_found", "path": parsed.path}, status=404)


def main():
    setup_logger()
    parser = argparse.ArgumentParser(description="Run Robot Station local server.")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "9999")))
    parser.add_argument("--control-port", type=int, default=int(os.environ.get("CONTROL_PORT", "9998")))
    parser.add_argument("--lifting-port", type=int, default=int(os.environ.get("LIFTING_CONTROL_PORT", "9997")))
    parser.add_argument("--piper-port", type=int, default=int(os.environ.get("PIPER_CONTROL_PORT", "9996")))
    args = parser.parse_args()

    if not (FRONTEND_DIR / "index.html").exists():
        raise SystemExit("frontend/index.html not found")

    httpd = ThreadingHTTPServer((args.host, args.port), RobotStationHandler)
    control_httpd = None
    control_thread = None
    if args.control_port and args.control_port != args.port:
        control_httpd = ThreadingHTTPServer((args.host, args.control_port), ChassisControlHandler)
        control_thread = threading.Thread(
            target=control_httpd.serve_forever,
            name="chassis-control-http",
            daemon=True,
        )
        control_thread.start()
    lifting_httpd = None
    lifting_thread = None
    if args.lifting_port and args.lifting_port not in (args.port, args.control_port):
        lifting_httpd = ThreadingHTTPServer((args.host, args.lifting_port), LiftingControlHandler)
        lifting_thread = threading.Thread(
            target=lifting_httpd.serve_forever,
            name="lifting-control-http",
            daemon=True,
        )
        lifting_thread.start()
    piper_httpd = None
    piper_thread = None
    if args.piper_port and args.piper_port not in (args.port, args.control_port, args.lifting_port):
        piper_httpd = ThreadingHTTPServer((args.host, args.piper_port), PiperControlHandler)
        piper_thread = threading.Thread(
            target=piper_httpd.serve_forever,
            name="piper-control-http",
            daemon=True,
        )
        piper_thread.start()
    LOGGER.info("Robot Station starting")
    LOGGER.info("Serving frontend: %s", FRONTEND_DIR)
    LOGGER.info("URL: http://%s:%s", args.host, args.port)
    if control_httpd is not None:
        LOGGER.info("Chassis control URL: http://%s:%s", args.host, args.control_port)
    if lifting_httpd is not None:
        LOGGER.info("Lifting control URL: http://%s:%s", args.host, args.lifting_port)
    if piper_httpd is not None:
        LOGGER.info("Piper control URL: http://%s:%s", args.host, args.piper_port)
    autostart_transforms()
    start_action_mirror()
    LOGGER.info("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Stopping Robot Station")
    finally:
        if piper_httpd is not None:
            piper_httpd.shutdown()
            if piper_thread is not None:
                piper_thread.join(timeout=2.0)
            piper_httpd.server_close()
        if lifting_httpd is not None:
            lifting_httpd.shutdown()
            if lifting_thread is not None:
                lifting_thread.join(timeout=2.0)
            lifting_httpd.server_close()
        if control_httpd is not None:
            control_httpd.shutdown()
            if control_thread is not None:
                control_thread.join(timeout=2.0)
            control_httpd.server_close()
        get_inference_manager().disconnect()
        shutdown_action_mirror()
        shutdown_services()
        shutdown_ros_io()
        httpd.server_close()


if __name__ == "__main__":
    main()
