import json

import backend.server as server
from modules.runtime.service_specs import default_service_specs, load_static_transform_config, static_transform_service_spec


def write_config(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_static_transform_service_uses_config_file(monkeypatch, tmp_path):
    config_path = tmp_path / "static_transforms.json"
    write_config(
        config_path,
        {
            "enabled": True,
            "transforms": [
                {
                    "name": "base_to_rslidar",
                    "parentFrame": "base_link",
                    "childFrame": "rslidar",
                    "translation": {"x": 0.3, "y": 0.0, "z": 0.07},
                    "rotation": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
                }
            ],
        },
    )
    monkeypatch.setenv("ROBOT_STATION_STATIC_TRANSFORMS_CONFIG", str(config_path))

    specs = default_service_specs()
    spec = specs["transforms"]
    command = list(spec.command)

    assert command[:4] == ["ros2", "run", "tf2_ros", "static_transform_publisher"]
    assert command[command.index("--frame-id") + 1] == "base_link"
    assert command[command.index("--child-frame-id") + 1] == "rslidar"
    assert command[command.index("--x") + 1] == "0.3"
    assert command[command.index("--z") + 1] == "0.07"
    assert "__node:=robot_station_static_tf_base_to_rslidar" in command


def test_static_transform_config_can_disable_service(monkeypatch, tmp_path):
    config_path = tmp_path / "static_transforms.json"
    write_config(config_path, {"enabled": False, "transforms": []})
    monkeypatch.setenv("ROBOT_STATION_STATIC_TRANSFORMS_CONFIG", str(config_path))

    assert "transforms" not in default_service_specs()


def test_multiple_static_transforms_share_one_managed_service():
    config = {
        "enabled": True,
        "transforms": [
            {"name": "base_to_rslidar", "parentFrame": "base_link", "childFrame": "rslidar"},
            {"name": "base_to_camera", "parentFrame": "base_link", "childFrame": "camera_f"},
        ],
    }

    spec = static_transform_service_spec(ros_distro="humble", config=config)

    assert spec.command[:2] == ("bash", "-lc")
    assert spec.command[2].count("static_transform_publisher") == 2
    assert "__node:=robot_station_static_tf_base_to_rslidar" in spec.cleanup_process_patterns
    assert "__node:=robot_station_static_tf_base_to_camera" in spec.cleanup_process_patterns


def test_load_static_transform_config_reports_missing_as_disabled(tmp_path):
    config = load_static_transform_config(tmp_path / "missing.json")

    assert config["enabled"] is False
    assert config["transforms"] == []


class FakeServiceManager:
    def __init__(self):
        self.calls = []

    def get_service(self, key):
        self.calls.append(("get", key))
        return {"ok": True, "service": {"key": key}}

    def start_service(self, key):
        self.calls.append(("start", key))
        return {"ok": True, "code": "SVC-STARTED", "detail": "started", "service": {"key": key}}


def test_autostart_transforms_starts_runtime_service(monkeypatch):
    manager = FakeServiceManager()
    monkeypatch.delenv("ROBOT_STATION_AUTOSTART_TRANSFORMS", raising=False)
    monkeypatch.setattr(server, "get_service_manager", lambda: manager)

    result = server.autostart_transforms()

    assert result["ok"] is True
    assert manager.calls == [("get", "transforms"), ("start", "transforms")]


def test_autostart_transforms_can_be_disabled(monkeypatch):
    manager = FakeServiceManager()
    monkeypatch.setenv("ROBOT_STATION_AUTOSTART_TRANSFORMS", "false")
    monkeypatch.setattr(server, "get_service_manager", lambda: manager)

    assert server.autostart_transforms() is None
    assert manager.calls == []


def test_chassis_service_passes_action_topics(monkeypatch):
    monkeypatch.setenv("CHASSIS_RAW_ACTION_TOPIC", "/action/chassis_custom")
    monkeypatch.setenv("CHASSIS_SMOOTHED_ACTION_TOPIC", "/action/chassis_custom_smoothed")

    command = default_service_specs()["chassis"].command

    assert "chassis_raw_action_topic:=/action/chassis_custom" in command
    assert "chassis_smoothed_action_topic:=/action/chassis_custom_smoothed" in command
