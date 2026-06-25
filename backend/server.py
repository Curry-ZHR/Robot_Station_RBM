#!/usr/bin/env python3
import argparse
import copy
import json
import mimetypes
import os
import shutil
import threading
import time
from email.utils import formatdate
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

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
from modules.localization import get_localization_manager, localization_result_status
from modules.map import get_mapping_manager, mapping_result_status
from modules.navigation import get_navigation_manager, navigation_result_status
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
from modules.state_machine import get_state_machine_executor, get_state_machine_store, state_machine_result_status
from modules.self_check.disk_check.disk_space import check_disk_space
from modules.self_check.gpu_check.gpu_status import check_gpu_status
from modules.self_check.ros_check.ros_daemon import ensure_ros_daemon


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
LOGGER = get_logger()
MODEL_ASSET_CACHE_SECONDS = int(os.environ.get("ROBOT_STATION_MODEL_ASSET_CACHE_SECONDS", "86400"))
SELF_CHECK_HARD_BLOCKERS = {"ROS2 daemon", "CAN 接口", "磁盘空间"}
SELF_CHECK_CACHE_LOCK = threading.Lock()
SELF_CHECK_RUN_LOCK = threading.Lock()
SELF_CHECK_CACHE = None


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


def summarize_self_check(results):
    hard_blockers = [
        result
        for result in results
        if result.get("name") in SELF_CHECK_HARD_BLOCKERS and result.get("status") == "错误"
    ]
    warnings = [
        result
        for result in results
        if result.get("status") != "正常" and result not in hard_blockers
    ]

    if hard_blockers:
        return {
            "state": "blocked",
            "level": "danger",
            "label": "存在阻塞",
            "nextAction": hard_blockers[0].get("advice") or "请处理阻塞项后重新执行自检。",
            "blockers": [
                {
                    "name": result.get("name", ""),
                    "status": result.get("status", ""),
                    "code": result.get("code", ""),
                    "advice": result.get("advice", ""),
                }
                for result in hard_blockers
            ],
            "warnings": [
                {
                    "name": result.get("name", ""),
                    "status": result.get("status", ""),
                    "code": result.get("code", ""),
                    "advice": result.get("advice", ""),
                }
                for result in warnings
            ],
        }

    if warnings:
        return {
            "state": "warn",
            "level": "warn",
            "label": "可继续，有警告",
            "nextAction": warnings[0].get("advice") or "存在非阻塞警告，请按任务需要确认。",
            "blockers": [],
            "warnings": [
                {
                    "name": result.get("name", ""),
                    "status": result.get("status", ""),
                    "code": result.get("code", ""),
                    "advice": result.get("advice", ""),
                }
                for result in warnings
            ],
        }

    return {
        "state": "ready",
        "level": "ok",
        "label": "可继续",
        "nextAction": "放行检查已通过，可以继续后续运行。",
        "blockers": [],
        "warnings": [],
    }


def empty_self_check_status():
    return {
        "ok": True,
        "code": "SELF-CHECK-IDLE",
        "detail": "No self-check result has been cached in this backend process.",
        "ran": False,
        "ranAt": None,
        "ranAtMs": None,
        "results": [],
        "summary": {
            "state": "idle",
            "level": "idle",
            "label": "未自检",
            "nextAction": "请执行一键检查。",
            "blockers": [],
            "warnings": [],
        },
    }


def cached_self_check_status():
    with SELF_CHECK_CACHE_LOCK:
        if SELF_CHECK_CACHE is None:
            return empty_self_check_status()
        return copy.deepcopy(SELF_CHECK_CACHE)


def run_self_check(auto_activate=True):
    global SELF_CHECK_CACHE
    with SELF_CHECK_RUN_LOCK:
        ran_at_ms = int(time.time() * 1000)
        results = [
            ensure_ros_daemon(),
            check_can_interface(auto_activate=auto_activate),
            check_disk_space(),
            check_gpu_status(),
        ]
        for result in results:
            log_check_result(result)

        payload = {
            "ok": True,
            "code": "SELF-CHECK-RUN",
            "detail": "Self-check completed and cached in backend process memory.",
            "ran": True,
            "ranAt": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ran_at_ms / 1000)),
            "ranAtMs": ran_at_ms,
            "results": results,
            "summary": summarize_self_check(results),
        }
        with SELF_CHECK_CACHE_LOCK:
            SELF_CHECK_CACHE = copy.deepcopy(payload)
        return payload


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


def payload_has_nonzero_chassis_velocity(payload):
    if not isinstance(payload, dict):
        return False
    keys = (
        "linearX",
        "linear_x",
        "x",
        "forward",
        "linearY",
        "linear_y",
        "y",
        "lateral",
        "angularZ",
        "angular_z",
        "yawRate",
        "angularVelocity",
    )
    for key in keys:
        if key not in payload:
            continue
        try:
            if abs(float(payload.get(key) or 0.0)) > 1e-6:
                return True
        except (TypeError, ValueError):
            return False
    return False


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

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.write_json({"status": "ok"})
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
                camera_kind = (parse_qs(parsed.query).get("kind") or [None])[0]
                result = reader.list_images(kind=camera_kind)
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
            if mapping_tail == "maps":
                result = get_mapping_manager().list_saved_maps()
                self.write_json(result, status=mapping_result_status(result))
                return
            if mapping_tail == "map/frame":
                result = get_mapping_manager().read_map_frame()
                if not result.get("ok"):
                    self.write_json(result, status=mapping_result_status(result))
                    return
                self.write_point_cloud_frame(result)
                return
            if mapping_tail.startswith("maps/") and mapping_tail.endswith("/frame"):
                map_name = mapping_tail[len("maps/") : -len("/frame")]
                result = get_mapping_manager().read_saved_map_frame(map_name)
                if not result.get("ok"):
                    self.write_json(result, status=mapping_result_status(result))
                    return
                self.write_point_cloud_frame(result)
                return
            self.write_json(
                {
                    "ok": False,
                    "code": "MAP-ACTION",
                    "detail": (
                        "Mapping GET path must be /api/mapping/status, /api/mapping/maps, "
                        "/api/mapping/map/frame, or /api/mapping/maps/<name>/frame."
                    ),
                },
                status=404,
            )
            return
        localization_tail = api_tail(parsed.path, "/api/localization")
        if localization_tail is not None:
            if localization_tail in ("", "status"):
                result = get_localization_manager().status()
                self.write_json(result, status=localization_result_status(result))
                return
            self.write_json(
                {
                    "ok": False,
                    "code": "LOC-ACTION",
                    "detail": "Localization GET path must be /api/localization/status.",
                },
                status=404,
            )
            return
        navigation_tail = api_tail(parsed.path, "/api/navigation")
        if navigation_tail is not None:
            if navigation_tail in ("", "status"):
                result = get_navigation_manager().status()
                self.write_json(result, status=navigation_result_status(result))
                return
            self.write_json(
                {
                    "ok": False,
                    "code": "NAV-ACTION",
                    "detail": "Navigation GET path must be /api/navigation/status.",
                },
                status=404,
            )
            return
        state_machine_tail = api_tail(parsed.path, "/api/state-machine")
        if state_machine_tail is not None:
            store = get_state_machine_store()
            if state_machine_tail == "states":
                result = store.list_states()
                self.write_json(result, status=state_machine_result_status(result))
                return
            if state_machine_tail == "graphs":
                result = store.list_graphs()
                self.write_json(result, status=state_machine_result_status(result))
                return
            if state_machine_tail == "run/status":
                result = get_state_machine_executor().status()
                self.write_json(result, status=state_machine_result_status(result))
                return
            self.write_json(
                {
                    "ok": False,
                    "code": "SM-ACTION",
                    "detail": "State machine GET path must be /api/state-machine/states, /api/state-machine/graphs, or /api/state-machine/run/status.",
                },
                status=404,
            )
            return
        if parsed.path == "/api/playback/status":
            self.write_json(get_playback_manager().status())
            return
        if parsed.path == "/api/self-check/status":
            self.write_json(cached_self_check_status())
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
        if chassis_action in {"cmd_vel", "velocity", "stop"}:
            should_interrupt = chassis_action == "stop"
            if not should_interrupt:
                should_interrupt = payload_has_nonzero_chassis_velocity(payload)
            if should_interrupt:
                interrupt_result = get_navigation_manager().interrupt_for_manual_control()
                if interrupt_result:
                    log_action_result("Navigation interrupted by chassis control", interrupt_result)
        result = handler(payload)
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

    def handle_navigation(self, action):
        manager = get_navigation_manager()
        if action in ("", "status"):
            result = manager.status()
            self.write_json(result, status=navigation_result_status(result))
            return
        if action == "start":
            payload = self.read_json_body()
            result = manager.start(payload)
            log_action_result("Navigation start", result)
            self.write_json(result, status=navigation_result_status(result))
            return
        if action == "stop":
            result = manager.stop()
            log_action_result("Navigation stop", result)
            self.write_json(result, status=navigation_result_status(result))
            return
        self.write_json(
            {
                "ok": False,
                "code": "NAV-ACTION",
                "detail": f"Unsupported navigation action: {action}",
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

    def handle_localization(self, action):
        manager = get_localization_manager()
        if action in ("", "status"):
            result = manager.status()
            self.write_json(result, status=localization_result_status(result))
            return
        if action == "start":
            payload = self.read_json_body()
            result = manager.start(payload)
            log_action_result("Localization start", result)
            self.write_json(result, status=localization_result_status(result))
            return
        if action == "stop":
            result = manager.stop()
            log_action_result("Localization stop", result)
            self.write_json(result, status=localization_result_status(result))
            return
        if action == "restart":
            result = manager.restart()
            log_action_result("Localization restart", result)
            self.write_json(result, status=localization_result_status(result))
            return
        if action in ("initial-pose", "initial_pose"):
            payload = self.read_json_body()
            result = manager.publish_initial_pose(payload)
            log_action_result("Localization initial pose", result)
            self.write_json(result, status=ros_result_status(result))
            return
        self.write_json(
            {
                "ok": False,
                "code": "LOC-ACTION",
                "detail": f"Unsupported localization action: {action}",
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

    def handle_state_machine(self, action):
        store = get_state_machine_store()
        executor = get_state_machine_executor()
        handlers = {
            "states/save": store.save_state,
            "states/delete": store.delete_state,
            "graphs/save": store.save_graph,
            "graphs/delete": store.delete_graph,
            "run/start": executor.start,
            "run/stop": lambda payload: executor.stop(),
        }
        handler = handlers.get(action)
        if handler is None:
            self.write_json(
                {
                    "ok": False,
                    "code": "SM-ACTION",
                    "detail": f"Unsupported state machine action: {action}",
                },
                status=400,
            )
            return
        payload = self.read_json_body()
        result = handler(payload)
        log_action_result(f"State machine {action}", result)
        self.write_json(result, status=state_machine_result_status(result))

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/self-check/run":
            auto_activate = query_bool(parsed.query, "auto_activate", default=True)
            result = run_self_check(auto_activate=auto_activate)
            self.write_json(result)
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
        localization_action = api_tail(parsed.path, "/api/localization")
        if localization_action is not None:
            self.handle_localization(localization_action)
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
        navigation_action = api_tail(parsed.path, "/api/navigation")
        if navigation_action is not None:
            self.handle_navigation(navigation_action)
            return
        state_machine_action = api_tail(parsed.path, "/api/state-machine")
        if state_machine_action is not None:
            self.handle_state_machine(state_machine_action)
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

    def write_point_cloud_frame(self, result, status=200, headers=None):
        frame_headers = {
            "X-Robot-Station-PointCloud-Point-Count": str(result.get("pointCount", "")),
            "X-Robot-Station-PointCloud-Source-Point-Count": str(result.get("sourcePointCount", "")),
            "X-Robot-Station-PointCloud-Stride-Floats": str(result.get("strideFloats", "")),
            "X-Robot-Station-PointCloud-Fields": ",".join(result.get("fields", [])),
            "X-Robot-Station-Mapping-Map-Size-Bytes": str(result.get("sizeBytes", "")),
            "X-Robot-Station-Mapping-Map-Mtime-Ms": str(result.get("mtimeMs", "")),
        }
        if result.get("sessionId"):
            frame_headers["X-Robot-Station-Mapping-Session-Id"] = str(result.get("sessionId", ""))
        if result.get("captureCount") is not None:
            frame_headers["X-Robot-Station-Mapping-Capture-Count"] = str(result.get("captureCount", ""))
        frame_headers.update(headers or {})
        self.write_binary(result["body"], result["contentType"], status=status, headers=frame_headers)

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
        # Re-send the most recent frame periodically even when the sensor stops
        # producing new frames. Without this, a frozen feed never writes to the
        # socket, so a client disconnect is never detected and this worker thread
        # loops forever (thread leak).
        keepalive_sec = 5.0
        while True:
            if not result.get("ok"):
                time.sleep(0.2)
                result = reader.read_frame(camera, kind, timeout_sec=2.0, after_sequence=last_sequence)
                continue

            sequence = result.get("sequence")
            is_new = sequence != last_sequence
            needs_keepalive = bool(last_sent_at) and (time.monotonic() - last_sent_at) >= keepalive_sec
            if is_new or needs_keepalive:
                if is_new:
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
