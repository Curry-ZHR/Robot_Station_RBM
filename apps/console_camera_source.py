"""One owned ROS camera publisher shared by real/sim readers and recording."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

from console_support import ConsoleError, age, atomic_json, read_json
from ros2_camera_bridge import validate_ros2_config


class CameraSourceManager:
    def __init__(self, driver):
        self.driver = driver
        self.directory = driver.directory/"camera-bridge"

    def settings(self, mode):
        config = self.driver.config(mode)
        if config["camera_source"] != "ros2":
            return None
        if not config["camera_endpoint"].startswith("tcp://127.0.0.1:"):
            raise ConsoleError("托管 ROS 2 桥接仅绑定 127.0.0.1；远程 ZMQ 来源请选 zmq", 412, "camera_config")
        result = {"ros2_camera": validate_ros2_config(config["ros2_camera"]),
                  "camera_endpoint": config["camera_endpoint"], "camera_keys": config["camera_keys"]}
        code = (self.driver.app_root/"ros2_camera_bridge.py").read_bytes()+(self.driver.app_root/"console_support.py").read_bytes()
        result["_worker_version"] = hashlib.sha256(code+json.dumps(result, sort_keys=True).encode()).hexdigest()[:20]
        return result

    def status(self, mode):
        settings = self.settings(mode)
        if settings is None:
            return {"kind": "zmq", "state": "external", "message": "接收外部 ZMQ 图像发布流"}
        row = read_json(self.directory/"status.json")
        running = self.driver.supervisor.running("camera-bridge")
        record = self.driver.supervisor.record("camera-bridge") or {}
        same_process = row.get("pid") == record.get("pid")
        valid = running and same_process and row.get("worker_version") == settings["_worker_version"] and age(row.get("heartbeat_at")) < 3
        state = row.get("state", "waiting") if valid else "stopped" if not running else "starting"
        if same_process and row.get("worker_version") == settings["_worker_version"] and row.get("state") == "failed":
            state = "failed"
        return {"kind": "ros2", "domain_id": settings["ros2_camera"]["domain_id"], "state": state,
                "topics": settings["ros2_camera"]["topics"], "endpoint": settings["camera_endpoint"],
                "views": row.get("views", {}) if valid else {}, "errors": row.get("errors", {}) if valid else {},
                "packets": row.get("packets", 0) if valid else 0,
                "message": row.get("error") if state == "failed" else
                    f"ROS 2 Domain {settings['ros2_camera']['domain_id']} · {state}"}

    def start(self, mode):
        settings = self.settings(mode)
        if settings is None:
            return {"kind": "zmq", "reused": True}
        path = self.directory/"config.json"
        supervisor = self.driver.supervisor
        with supervisor.lock:
            if supervisor.running("camera-bridge") and read_json(path) != settings:
                supervisor.stop("camera-bridge")
            if not supervisor.running("camera-bridge"):
                atomic_json(path, settings)
            launcher = self.driver.app_root.parent/"scripts/run_ros2_camera_bridge.sh"
            python = self.driver.app_root/".venv_ros2_camera/bin/python"
            if not launcher.is_file() or not python.is_file():
                raise ConsoleError("ROS 2 相机环境未安装，请运行 scripts/install_ros2_camera.sh", 412, "camera_environment")
            result = supervisor.start("camera-bridge", ["bash", str(launcher), "--config", str(path),
                "--directory", str(self.directory)], self.driver.app_root.parent)
        deadline = time.monotonic()+8
        while time.monotonic() < deadline:
            row = self.status(mode)
            if row["state"] in {"waiting", "streaming"}:
                return {**result, **row}
            if row["state"] == "failed" or not supervisor.running("camera-bridge"):
                raise ConsoleError("ROS 2 相机桥接启动失败："+supervisor.logs("camera-bridge", 1600)[-900:], 412, "camera_start_failed")
            time.sleep(.05)
        raise ConsoleError("ROS 2 相机桥接启动超时，请查看桥接日志", 412, "camera_start_timeout")

    def stop(self):
        return self.driver.supervisor.stop("camera-bridge")
