"""Process harness for real ROS 2 offline tests; all frames stay on ephemeral ZMQ."""
import copy
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import uuid

from console_support import atomic_json, read_json
from ros2_camera_bridge import default_ros2_config


class Ros2CameraFixture:
    def __init__(self, app, publisher_domain=99, start_publisher=True, compressed=False):
        self.app = Path(app)
        self.root = Path(tempfile.mkdtemp(prefix="robot-station-ros2-"))
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.endpoint = f"tcp://127.0.0.1:{sock.getsockname()[1]}"
        settings = default_ros2_config()
        settings["localhost_only"] = True
        prefix = "/_robot_station_test_"+uuid.uuid4().hex[:10]
        for name, row in settings["topics"].items():
            row["topic"] = prefix+"/"+name
        settings["topics"]["right_wrist"]["message_type"] = "sensor_msgs/msg/CompressedImage"
        if compressed:
            for row in settings["topics"].values():row["message_type"] = "sensor_msgs/msg/CompressedImage"
        self.config = {"ros2_camera": settings, "camera_endpoint": self.endpoint,
                       "camera_keys": {"head": "ego_view", "left_wrist": "left_wrist", "right_wrist": "right_wrist"},
                       "_worker_version": "isolated-test"}
        self.config_path = self.root/"config.json"
        atomic_json(self.config_path, self.config)
        self.children = []
        try:
            self.bridge = self.launch(["bash", str(self.app.parent/"scripts/run_ros2_camera_bridge.sh"),
                "--config", str(self.config_path), "--directory", str(self.root/"bridge")], "bridge")
            self.wait(lambda: self.status().get("state") == "waiting")
            self.publisher_domain = publisher_domain
            if start_publisher:
                self.start_publisher(publisher_domain)
        except Exception:
            self.close()
            raise

    def launch(self, args, name):
        with (self.root/(name+".log")).open("ab") as log:
            process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT)
        self.children.append(process)
        return process

    def start_publisher(self, domain=99):
        config = copy.deepcopy(self.config)
        config["ros2_camera"]["domain_id"] = domain
        path = self.root/f"publisher-{domain}.json"
        atomic_json(path, config)
        ready = self.root/f"publisher-{domain}.ready"
        process = self.launch(["bash", "-c", 'source /opt/ros/humble/setup.bash; exec "$1" "$2" --config "$3" --ready "$4" --control "$5"',
            "ros-camera-test", str(self.app/".venv_ros2_camera/bin/python"), str(self.app/"tests/ros2_camera_fixture.py"),
            str(path), str(ready), str(self.root/"control.json")], f"publisher-{domain}")
        self.wait(lambda: ready.is_file())
        return process

    def status(self):
        return read_json(self.root/"bridge/status.json")

    def control(self, **kwargs):
        atomic_json(self.root/"control.json", kwargs)

    def wait(self, predicate, seconds=15):
        deadline = time.monotonic()+seconds
        while time.monotonic() < deadline:
            if predicate():return
            if any(p.poll() is not None for p in self.children):break
            time.sleep(.05)
        logs = "\n".join(p.read_text(errors="replace")[-3000:] for p in self.root.glob("*.log"))
        raise AssertionError("ROS 2 fixture not ready: "+str(self.status())+"\n"+logs)

    def close(self):
        for process in reversed(self.children):
            if process.poll() is None:process.terminate()
        for process in self.children:
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)

    def __enter__(self):return self
    def __exit__(self, *args):self.close()
