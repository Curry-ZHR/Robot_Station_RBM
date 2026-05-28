#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

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
from modules.ros_io import get_ros_reader, get_ros_writer, shutdown_ros_io
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
                bitrate = int(payload.get("bitrate", 1000000))
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
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
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
