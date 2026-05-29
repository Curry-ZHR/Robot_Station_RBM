#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from modules.control.chassis import chassis_limits, publish_chassis_velocity, stop_chassis
from modules.control.lifting import (
    clear_lifting_error,
    initialize_lifting,
    jog_lifting,
    lifting_limits,
    move_lifting_to_height,
    stop_lifting,
    zero_lifting_position,
)
from modules.control.piper import publish_joint_targets
from modules.drivers.can.can_activate import activate_can
from modules.logger import get_logger, setup_logger
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


class RobotStationHandler(SimpleHTTPRequestHandler):
    server_version = "RobotStationHTTP/0.1"

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def log_message(self, format, *args):
        return

    def end_headers(self):
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

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/control/piper/joint-targets":
            payload = self.read_json_body()
            result = publish_joint_targets(payload)
            log_action_result("Piper joint targets", result)
            self.write_json(result, status=ros_result_status(result))
            return
        chassis_action = api_tail(parsed.path, "/api/control/chassis")
        if chassis_action is not None:
            payload = self.read_json_body()
            request_start = time.perf_counter()
            LOGGER.info(
                "CHASSIS_DEBUG backend.request_received trace=%s seq=%s action=%s command=(%.4f, %.4f, %.4f) t=%.6f",
                payload.get("commandTraceId", payload.get("traceId", "")),
                payload.get("commandSequence", payload.get("sequence", "")),
                chassis_action,
                float(payload.get("linearX", payload.get("linear_x", 0)) or 0),
                float(payload.get("linearY", payload.get("linear_y", 0)) or 0),
                float(payload.get("angularZ", payload.get("angular_z", 0)) or 0),
                request_start,
            )
            handlers = {
                "cmd_vel": publish_chassis_velocity,
                "velocity": publish_chassis_velocity,
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
            elapsed_ms = (time.perf_counter() - request_start) * 1000.0
            result.setdefault("debugTiming", {})
            result["debugTiming"]["backendRequestElapsedMs"] = round(elapsed_ms, 3)
            LOGGER.info(
                "CHASSIS_DEBUG backend.response_ready trace=%s seq=%s action=%s code=%s elapsed_ms=%.3f stale=%s",
                payload.get("commandTraceId", payload.get("traceId", "")),
                payload.get("commandSequence", payload.get("sequence", "")),
                chassis_action,
                result.get("code", ""),
                elapsed_ms,
                result.get("stale", False),
            )
            log_action_result(f"Chassis {chassis_action}", result)
            self.write_json(result, status=ros_result_status(result))
            return
        lifting_action = api_tail(parsed.path, "/api/control/lifting")
        if lifting_action is not None:
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
            result = handler(payload)
            log_action_result(f"Lifting {lifting_action}", result)
            self.write_json(result, status=ros_result_status(result))
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
        return mimetypes.guess_type(path)[0] or "application/octet-stream"

    def write_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
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


def main():
    setup_logger()
    parser = argparse.ArgumentParser(description="Run Robot Station local server.")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "9999")))
    args = parser.parse_args()

    if not (FRONTEND_DIR / "index.html").exists():
        raise SystemExit("frontend/index.html not found")

    httpd = ThreadingHTTPServer((args.host, args.port), RobotStationHandler)
    LOGGER.info("Robot Station starting")
    LOGGER.info("Serving frontend: %s", FRONTEND_DIR)
    LOGGER.info("URL: http://%s:%s", args.host, args.port)
    LOGGER.info("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Stopping Robot Station")
    finally:
        shutdown_services()
        shutdown_ros_io()
        httpd.server_close()


if __name__ == "__main__":
    main()
