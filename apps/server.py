from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
import re
import threading
import time
import signal
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from sonic_adapter import AdapterError, SonicAdapter
from collection_workspace import CollectionWorkspace
from dataset_conversion import ConversionManager, ConversionError
from console_runtime import ConsoleRuntime
from console_support import ConsoleError
from console_timeseries import TimeseriesService
from console_access import ConsoleAccess


APP_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = APP_ROOT / "static"
DEFAULT_SONIC_ROOT = APP_ROOT.parents[1] / "sonic_deploy"


class DataPlatformHandler(SimpleHTTPRequestHandler):
    server_version = "RobotDataPlatform/0.2"

    @property
    def adapter(self) -> SonicAdapter:
        return self.server.adapter  # type: ignore[attr-defined]

    @property
    def workspace(self) -> CollectionWorkspace:
        return self.server.workspace  # type: ignore[attr-defined]

    @property
    def conversions(self):
        if not hasattr(self.server, "conversion_manager"):
            self.server.conversion_manager = ConversionManager(self.adapter.repo_root / "outputs", APP_ROOT / ".runtime")
        return self.server.conversion_manager

    @property
    def console(self):
        return self.server.console_runtime

    def log_message(self, fmt: str, *args) -> None:
        print(f"[http] {self.address_string()} - {fmt % args}")

    def _json(self, value, status: int = 200, extra_headers=None) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for key,value in (extra_headers or {}).items():self.send_header(key,value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _body(self) -> dict:
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise AdapterError("Content-Length 格式不正确") from exc
        if size < 0:
            raise AdapterError("Content-Length 不能为负数")
        if size > 1_000_000:
            raise AdapterError("请求内容过大", 413)
        try:
            value = json.loads(self.rfile.read(size) or b"{}")
        except (ValueError, UnicodeDecodeError) as exc:
            raise AdapterError("请求 JSON 格式不正确") from exc
        if not isinstance(value, dict):
            raise AdapterError("请求内容必须是 JSON 对象")
        return value

    def _handle_error(self, exc: Exception) -> None:
        status = exc.status if isinstance(exc, (AdapterError, ConversionError, ConsoleError)) else 500
        message = str(exc) if isinstance(exc, (AdapterError, ConversionError, ConsoleError)) else "服务端发生未处理错误"
        if status == 500:
            print(f"[error] {type(exc).__name__}: {exc}")
        if self.path.startswith("/api/v1/console"):
            self._json({"ok": False, "error": {"code": getattr(exc, "code", "console_error"), "message": message,
                                              "blockers": getattr(exc, "blockers", [])}}, status)
        elif self.path.startswith("/api/conversions"):
            self._json({"ok": False, "error": {"code": "conversion_error", "message": message}}, status)
        else:
            self._json({"ok": False, "error": message}, status)

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            access=getattr(self.server,"console_access",None)
            if access:access.validate_host(self.headers)
            if parsed.path == "/api/v1/console/robot/commissioning":
                if access and not access.authorized(self.headers,self.client_address[0]):raise ConsoleError("需要操作授权",401,"operator_required")
                if query.get('template')==['1']:
                    from unitree_g1_control import template
                    self._json(template(self.console.profile))
                else:self._json(self.console.real_manual.report())
                return
            if parsed.path in {"/api/v1/console/configuration","/api/v1/console/poses","/api/v1/console/diagnostics","/api/v1/console/diagnostics/download"}:
                if access and not access.authorized(self.headers,self.client_address[0]):raise ConsoleError("需要操作授权",401,"operator_required")
                mode=query.get("mode",["sim"])[0];self.console.validate_mode(mode)
                if parsed.path.endswith("/download"):
                    data=self.console.diagnostics.bundle(mode);self.send_response(200);self.send_header("Content-Type","application/zip");self.send_header("Content-Disposition","attachment; filename=robot-station-diagnostics.zip");self.send_header("Content-Length",str(len(data)));self.end_headers()
                    if self.command != "HEAD":self.wfile.write(data)
                else:
                    result=self.console.configuration.view() if parsed.path.endswith("/configuration") else self.console.poses.list() if parsed.path.endswith("/poses") else self.console.diagnostics.collect(mode)
                    self._json(result)
                return
            if parsed.path == "/api/v1/console/snapshot":
                data=self.console.snapshot(query.get("mode", ["sim"])[0], query.get("profile_id", ["unitree-g1-29"])[0])
                if access:
                    data["snapshot"]["access"]=access.view(self.headers,self.client_address[0])
                    if not data["snapshot"]["access"]["authorized"]:data["snapshot"]["capabilities"]["commands"]=[]
                self._json(data)
                return
            if parsed.path == "/api/v1/console/episodes/timeseries":
                try:
                    max_points = int(query.get("max_points", ["6000"])[0])
                except ValueError as exc:
                    raise ConsoleError("max_points 必须为整数") from exc
                self._json(self.server.timeseries_service.get(query.get("dataset", [""])[0], query.get("episode", [""])[0], max_points))
                return
            if parsed.path == "/api/v1/console/collection/logs":
                if access and not access.authorized(self.headers,self.client_address[0]):
                    raise ConsoleError("需要操作授权",401,"operator_required")
                self._json({"ok":True,"log":self.console.recorder.logs()})
                return
            console_job = re.fullmatch(r"/api/v1/console/deployment/jobs/([a-f0-9]{32})", parsed.path)
            if console_job:
                self._json(self.console.job(console_job.group(1)))
                return
            camera_match = re.fullmatch(r"/api/v1/console/cameras/(head|left_wrist|right_wrist)/(stream|frame)", parsed.path)
            if camera_match:
                mode = query.get("mode", ["sim"])[0]
                self.console.validate_mode(mode)
                self._serve_camera(mode, *camera_match.groups())
                return
            if parsed.path == "/api/conversions/sources":
                self._json(self.conversions.sources())
                return
            if parsed.path == "/api/conversions/jobs":
                self._json(self.conversions.jobs())
                return
            conversion_match = re.fullmatch(r"/api/conversions/jobs/([a-f0-9]{32})(/download)?", parsed.path)
            if conversion_match:
                job_id, download = conversion_match.groups()
                if download:
                    target = self.conversions.download(job_id, query.get("path", [""])[0])
                    self._serve_video(target, mimetypes.guess_type(target.name)[0] or "application/octet-stream")
                else:
                    self._json(self.conversions.job(job_id))
                return
            if parsed.path == "/api/collection":
                self._json(self.workspace.snapshot(query.get("mode", [None])[0]))
                return
            if parsed.path == "/api/episodes":
                try:
                    offset = int(query.get("offset", ["0"])[0])
                    limit = int(query.get("limit", ["30"])[0])
                except ValueError as exc:
                    raise AdapterError("offset 和 limit 必须是整数") from exc
                self._json(self.workspace.episodes(query.get("dataset", [""])[0], offset, limit))
                return
            if parsed.path in {"/api/episodes/review", "/api/episodes/video"}:
                name = query.get("dataset", [""])[0]
                index = self.workspace.episode_index(query.get("episode", [""])[0])
                if parsed.path.endswith("/review"):
                    self._json(self.workspace.review(name, index))
                else:
                    self._serve_video(self.workspace.video(name, index, query.get("camera", [""])[0]))
                return
            if parsed.path == "/healthz":
                self._json({"ok": True, "service": "robot-data-platform"})
                return
            if parsed.path == "/api/status":
                self._json(self.adapter.status())
                return
            if parsed.path == "/api/datasets":
                self._json({"ok": True, "datasets": self.adapter.datasets()})
                return
            if parsed.path == "/api/overview":
                self._json(self.adapter.overview())
                return
            if parsed.path == "/api/logs":
                query = parse_qs(parsed.query)
                pane_value = query.get("pane", [""])[0]
                pane = int(pane_value) if pane_value.isdigit() else None
                lines_value = query.get("lines", ["160"])[0]
                lines = int(lines_value) if lines_value.isdigit() else 160
                self._json({"ok": True, "log": self.adapter.capture_log(pane=pane, lines=lines)})
                return
            if parsed.path.startswith("/api/"):
                self._json({"ok": False, "error": "接口不存在"}, 404)
                return
            self._serve_static(parsed.path)
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            self._handle_error(exc)

    def do_HEAD(self) -> None:
        self.do_GET()

    def _serve_video(self, path: Path, content_type: str = "video/mp4") -> None:
        size = path.stat().st_size
        start, end, status = 0, size - 1, 200
        byte_range = self.headers.get("Range")
        if byte_range:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", byte_range)
            if match and any(match.groups()):
                first, last = match.groups()
                start = int(first) if first else max(0, size - int(last))
                end = min(int(last), size - 1) if first and last else size - 1
            else:
                start = size
            if start > end or start >= size:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            status = 206
        with path.open("rb") as source:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(max(0, end - start + 1)))
            self.send_header("Cache-Control", "private, no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            if self.command == "HEAD":
                return
            source.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                data = source.read(min(256 * 1024, remaining))
                if not data:
                    break
                self.wfile.write(data)
                remaining -= len(data)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            payload = self._body()
            access=getattr(self.server,"console_access",None)
            if access:
                access.guard(self.headers,self.client_address[0],login=parsed.path=="/api/v1/console/session")
                if parsed.path=="/api/v1/console/session":
                    cookie=access.login(payload.get("operation_key"),self.client_address[0])
                    self._json({"ok":True,"message":"操作授权成功"},extra_headers={"Set-Cookie":cookie})
                    return
            extension_routes={}
            if parsed.path.startswith("/api/v1/console/"):extension_routes={"/api/v1/console/configuration":self.console.configure,"/api/v1/console/poses":self.console.poses.save,"/api/v1/console/poses/preview":self.console.pose_preview,"/api/v1/console/robot/manual":self.console.manual_target}
            if parsed.path in extension_routes:
                self._json(extension_routes[parsed.path](payload));return
            console_routes = {"/self-check": "self_check", "/deployment/jobs": "deployment", "/robot/commands": "robot",
                              "/collection/commands": "collection", "/services/actions": "services", "/safety/stop": "safety",
                              "/inference/commands": "inference", "/workflows/runs": "workflows"}
            if parsed.path.startswith("/api/v1/console/"):
                scope = console_routes.get(parsed.path.removeprefix("/api/v1/console"))
                if not scope:
                    raise ConsoleError("接口不存在", 404, "not_found")
                result = self.console.command(scope, payload, self.headers.get("Idempotency-Key"))
                self._json(result, 202 if result.get("state") in {"accepted", "pending", "running"} else 200)
                return
            if hasattr(self.server, "console_runtime") and parsed.path in {"/api/stack/start", "/api/stack/stop", "/api/record/start", "/api/record/save", "/api/record/discard"}:
                raise ConsoleError("旧采集控制入口已停用，请使用统一任务接口", 410, "legacy_control_disabled")
            if parsed.path == "/api/conversions/inspect":
                self._json(self.conversions.inspect(payload.get("dataset")))
                return
            if parsed.path == "/api/conversions/jobs":
                self._json(self.conversions.create(payload), 202)
                return
            cancel_match = re.fullmatch(r"/api/conversions/jobs/([a-f0-9]{32})/cancel", parsed.path)
            if cancel_match:
                self._json(self.conversions.cancel(cancel_match.group(1)))
                return
            routes = {
                "/api/collection/config": lambda: self.adapter.save_config(payload),
                "/api/episodes/rate": lambda: self.workspace.rate(payload),
                "/api/stack/start": lambda: self.adapter.start(payload),
                "/api/stack/stop": self.adapter.stop,
                "/api/record/start": lambda: self.adapter.record("start"),
                "/api/record/save": lambda: self.adapter.record("save"),
                "/api/record/discard": lambda: self.adapter.record("discard"),
                "/api/datasets/process": lambda: self.adapter.process_dataset(payload),
            }
            handler = routes.get(parsed.path)
            if handler is None:
                self._json({"ok": False, "error": "接口不存在"}, 404)
                return
            self._json(handler())
        except Exception as exc:
            self._handle_error(exc)

    def _serve_camera(self, mode, camera, transport):
        data, stamp = self.console.driver.camera_frame(mode, camera)
        if transport == "frame" or self.command == "HEAD":
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
            return
        if not self.server.camera_slots.acquire(blocking=False):
            raise ConsoleError("相机预览连接数已达上限", 429, "stream_limit")
        try:
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            previous = None
            self.connection.settimeout(5)
            while True:
                try:
                    data, stamp = self.console.driver.camera_frame(mode, camera)
                except ConsoleError:
                    break
                if stamp != previous:
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(data)).encode()+b"\r\n\r\n"+data+b"\r\n")
                    self.wfile.flush()
                    previous = stamp
                time.sleep(.08)
        except (OSError, TimeoutError):
            pass
        finally:
            self.server.camera_slots.release()

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        target = (STATIC_ROOT / relative).resolve()
        if STATIC_ROOT not in target.parents and target != STATIC_ROOT:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(content)


def create_server(host,port,sonic_root,runtime_dir=None):
    """Same bootstrap for production and isolated process-restart verification."""
    adapter=SonicAdapter(Path(sonic_root),Path(runtime_dir or APP_ROOT/'.runtime'),enable_legacy_control=False)
    server=None
    try:
        server=ThreadingHTTPServer((host,port),DataPlatformHandler)
        server.daemon_threads=True
        server.adapter=adapter
        server.workspace=CollectionWorkspace(adapter)
        server.console_runtime=ConsoleRuntime(adapter,server.workspace)
        server.camera_slots=threading.BoundedSemaphore(12)
        server.timeseries_service=TimeseriesService(server.workspace,adapter.runtime_dir)
        server.console_access=ConsoleAccess(server.console_runtime.directory,host)
        server.conversion_manager=ConversionManager(adapter.repo_root/'outputs',adapter.runtime_dir)
        return server
    except Exception:
        if server is not None:
            if hasattr(server,'console_runtime'):server.console_runtime.close()
            server.server_close()
        adapter.close()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="机器人数据采集工作台")
    parser.add_argument("--host", default=os.environ.get("DATA_PLATFORM_HOST", "192.168.123.100"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DATA_PLATFORM_PORT", "9999")))
    parser.add_argument(
        "--sonic-root",
        type=Path,
        default=Path(os.environ.get("SONIC_REPO_ROOT", DEFAULT_SONIC_ROOT)),
    )
    parser.add_argument("--runtime-dir",type=Path)
    args = parser.parse_args()
    server=create_server(args.host,args.port,args.sonic_root,args.runtime_dir)
    adapter=server.adapter
    for sig in (signal.SIGTERM,signal.SIGINT):
        signal.signal(sig, lambda *_: threading.Thread(target=server.shutdown,daemon=True).start())
    print(f"机器人数据采集工作台: http://{args.host}:{args.port}")
    print(f"Robot runtime: {adapter.repo_root}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.console_runtime.close()
        adapter.close()


if __name__ == "__main__":
    main()
