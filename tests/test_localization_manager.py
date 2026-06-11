import json

from modules.localization.manager import LocalizationManager, localization_result_status


class FakeProcess:
    pid = 4242

    def __init__(self, returncode=None):
        self.returncode = returncode

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = 0
        return 0

    def terminate(self):
        self.returncode = 0

    def kill(self):
        self.returncode = -9


class FakeMappingManager:
    def __init__(self, map_path):
        self.map_path = map_path

    def list_saved_maps(self):
        return {
            "ok": True,
            "code": "MAP-SAVED-LIST",
            "maps": [
                {
                    "name": "lab_map",
                    "mapPath": str(self.map_path),
                    "path": str(self.map_path.parent),
                    "sizeBytes": 12,
                    "mtimeMs": 1234,
                }
            ],
        }


class FakeReader:
    def __init__(self):
        self.status_payload = {
            "state": "localizing",
            "converged": True,
            "fitness": 0.04,
            "frequencyHz": 6.5,
            "pose": {"x": 1.0, "y": 2.0, "z": 0.0, "yawDeg": 30.0},
        }

    def read(self, key, timeout_sec=0.0):
        if key == "localization_status":
            return {
                "ok": True,
                "code": "ROS-R-OK",
                "data": {"data": json.dumps(self.status_payload)},
                "ageMs": 10,
                "stale": False,
                "receivedAt": "10:00:00",
            }
        if key == "localization_pose":
            return {
                "ok": True,
                "code": "ROS-R-OK",
                "data": {"pose": {"position": {"x": 1.0, "y": 2.0, "z": 0.0}}},
                "ageMs": 12,
                "stale": False,
                "receivedAt": "10:00:00",
            }
        raise AssertionError(key)


def test_localization_result_status_maps_payload_errors():
    assert localization_result_status({"ok": True}) == 200
    assert localization_result_status({"ok": False, "code": "LOC-PAYLOAD"}) == 400
    assert localization_result_status({"ok": False, "code": "LOC-BUSY"}) == 409


def test_localization_manager_start_resolves_saved_map_and_builds_command(tmp_path, monkeypatch):
    map_path = tmp_path / "lab_map" / "map.pcd"
    map_path.parent.mkdir()
    map_path.write_text("pcd", encoding="utf-8")
    commands = []

    def fake_popen(command, **kwargs):
        commands.append(command)
        return FakeProcess()

    monkeypatch.setattr("modules.localization.manager.get_mapping_manager", lambda: FakeMappingManager(map_path))
    monkeypatch.setattr("modules.localization.manager.subprocess.Popen", fake_popen)

    manager = LocalizationManager(localizer_command=("localizer",), gpu_localizer_command=("python3",))
    result = manager.start({"mapName": "lab_map"})

    assert result["ok"] is True
    assert result["backend"] == "cpu"
    assert result["map"]["name"] == "lab_map"
    assert result["map"]["settings"]["backend"] == "cpu"
    assert commands[0][:4] == ["localizer", "--ros-args", "-p", f"map_path:={map_path}"]
    assert "map_name:=lab_map" in commands[0]
    assert "base_frame:=base_link" in commands[0]
    assert result["process"]["running"] is True


def test_localization_manager_start_uses_gpu_backend_command(tmp_path, monkeypatch):
    map_path = tmp_path / "lab_map" / "map.pcd"
    map_path.parent.mkdir()
    map_path.write_text("pcd", encoding="utf-8")
    commands = []

    def fake_popen(command, **kwargs):
        commands.append(command)
        return FakeProcess()

    monkeypatch.setattr("modules.localization.manager.get_mapping_manager", lambda: FakeMappingManager(map_path))
    monkeypatch.setattr("modules.localization.manager.subprocess.Popen", fake_popen)

    manager = LocalizationManager(localizer_command=("localizer",), gpu_localizer_command=("python3",))
    result = manager.start({"mapName": "lab_map", "backend": "gpu"})

    assert result["ok"] is True
    assert result["backend"] == "gpu"
    assert result["map"]["settings"]["backend"] == "gpu"
    assert commands[0][:4] == ["python3", "--ros-args", "-p", f"map_path:={map_path}"]


def test_localization_manager_rejects_unknown_backend(tmp_path, monkeypatch):
    map_path = tmp_path / "lab_map" / "map.pcd"
    map_path.parent.mkdir()
    map_path.write_text("pcd", encoding="utf-8")
    commands = []

    def fake_popen(command, **kwargs):
        commands.append(command)
        return FakeProcess()

    monkeypatch.setattr("modules.localization.manager.get_mapping_manager", lambda: FakeMappingManager(map_path))
    monkeypatch.setattr("modules.localization.manager.subprocess.Popen", fake_popen)

    manager = LocalizationManager(localizer_command=("localizer",), gpu_localizer_command=("python3",))
    result = manager.start({"mapName": "lab_map", "backend": "tpu"})

    assert result["ok"] is False
    assert result["code"] == "LOC-PAYLOAD"
    assert commands == []


def test_localization_manager_rejects_unavailable_gpu_backend(tmp_path, monkeypatch):
    map_path = tmp_path / "lab_map" / "map.pcd"
    map_path.parent.mkdir()
    map_path.write_text("pcd", encoding="utf-8")
    commands = []

    def fake_popen(command, **kwargs):
        commands.append(command)
        return FakeProcess()

    monkeypatch.setattr("modules.localization.manager.get_mapping_manager", lambda: FakeMappingManager(map_path))
    monkeypatch.setattr("modules.localization.manager.subprocess.Popen", fake_popen)

    manager = LocalizationManager(
        localizer_command=("localizer",),
        gpu_localizer_command=("definitely-missing-gpu-localizer",),
    )
    result = manager.start({"mapName": "lab_map", "backend": "gpu"})

    assert result["ok"] is False
    assert result["code"] == "LOC-GPU-UNAVAILABLE"
    assert commands == []


def test_localization_manager_status_merges_ros_status(tmp_path, monkeypatch):
    map_path = tmp_path / "lab_map" / "map.pcd"
    map_path.parent.mkdir()
    map_path.write_text("pcd", encoding="utf-8")
    monkeypatch.setattr("modules.localization.manager.get_mapping_manager", lambda: FakeMappingManager(map_path))
    monkeypatch.setattr("modules.localization.manager.subprocess.Popen", lambda *args, **kwargs: FakeProcess())
    monkeypatch.setattr("modules.localization.manager.get_ros_reader", lambda: FakeReader())

    manager = LocalizationManager(localizer_command=("localizer",), gpu_localizer_command=("python3",))
    manager.start({"mapName": "lab_map"})
    result = manager.status()

    assert result["ok"] is True
    assert result["backend"] == "cpu"
    assert result["state"] == "localizing"
    assert result["localizationStatus"]["data"]["fitness"] == 0.04
    assert result["pose"]["ok"] is True
