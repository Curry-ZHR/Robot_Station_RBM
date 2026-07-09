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


class FakeNoDataReader:
    def read(self, key, timeout_sec=0.0):
        return {
            "ok": False,
            "code": "ROS-R-NODATA",
            "detail": f"No message received for {key}.",
        }


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
    assert "max_failed_frames:=15" in commands[0]
    assert "recovery_search_enabled:=true" in commands[0]
    assert "recovery_after_failed_frames:=5" in commands[0]
    assert "recovery_confirm_frames:=2" in commands[0]
    assert "recovery_max_candidates_per_frame:=48" in commands[0]
    assert "recovery_wide_every_n_frames:=3" in commands[0]
    assert "odom_topic:=/odom" in commands[0]
    assert "voxel_leaf:=0.08" in commands[0]
    assert "use_ndt_when_tracking:=true" in commands[0]
    assert "use_odom_retry:=true" in commands[0]
    assert "odom_max_age_sec:=1.0" in commands[0]
    assert "max_pose_jump_m:=0.35" in commands[0]
    assert "fitness_degrade_ratio:=6.0" in commands[0]
    assert "recovery_fitness_ratio:=1.8" in commands[0]
    assert "recovery_fitness_abs:=0.05" in commands[0]
    assert result["process"]["running"] is True


def test_localization_manager_start_sets_fastdds_udp_transport(tmp_path, monkeypatch):
    map_path = tmp_path / "lab_map" / "map.pcd"
    map_path.parent.mkdir()
    map_path.write_text("pcd", encoding="utf-8")
    environments = []

    def fake_popen(command, **kwargs):
        environments.append(kwargs["env"])
        return FakeProcess()

    monkeypatch.delenv("FASTDDS_BUILTIN_TRANSPORTS", raising=False)
    monkeypatch.delenv("ROBOT_STATION_LOCALIZER_FASTDDS_BUILTIN_TRANSPORTS", raising=False)
    monkeypatch.setattr("modules.localization.manager.get_mapping_manager", lambda: FakeMappingManager(map_path))
    monkeypatch.setattr("modules.localization.manager.subprocess.Popen", fake_popen)

    manager = LocalizationManager(localizer_command=("localizer",), gpu_localizer_command=("python3",))
    result = manager.start({"mapName": "lab_map"})

    assert result["ok"] is True
    assert environments[0]["FASTDDS_BUILTIN_TRANSPORTS"] == "UDPv4"


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
    assert "voxel_leaf:=0.08" in commands[0]
    assert "use_ndt_when_tracking:=true" in commands[0]


def test_localization_manager_start_passes_localization_tuning(tmp_path, monkeypatch):
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
    result = manager.start(
        {
            "mapName": "lab_map",
            "backend": "gpu",
            "voxelLeafM": 0.12,
            "useNdtWhenTracking": True,
            "odomTopic": "/wheel_odom",
            "useOdomRetry": False,
            "odomMaxAgeSec": 2.5,
            "ndtResolutionM": 0.8,
            "ndtMaxIterations": 18,
            "gicpMaxCorrespondenceM": 0.35,
            "gicpMaxIterations": 16,
            "recoverySearchEnabled": False,
            "recoveryAfterFailedFrames": 7,
            "recoveryConfirmFrames": 3,
            "recoveryMaxCandidatesPerFrame": 48,
            "recoveryWideEveryNFrames": 4,
            "recoveryFitnessRatio": 1.4,
            "recoveryFitnessAbs": 0.02,
        }
    )

    assert result["ok"] is True
    assert result["map"]["settings"]["voxelLeafM"] == 0.12
    assert result["map"]["settings"]["useNdtWhenTracking"] is True
    assert result["map"]["settings"]["odomTopic"] == "/wheel_odom"
    assert result["map"]["settings"]["useOdomRetry"] is False
    assert result["map"]["settings"]["odomMaxAgeSec"] == 2.5
    assert "voxel_leaf:=0.12" in commands[0]
    assert "use_ndt_when_tracking:=true" in commands[0]
    assert "odom_topic:=/wheel_odom" in commands[0]
    assert "use_odom_retry:=false" in commands[0]
    assert "odom_max_age_sec:=2.5" in commands[0]
    assert "ndt_resolution:=0.8" in commands[0]
    assert "ndt_max_iterations:=18" in commands[0]
    assert "gicp_max_correspondence:=0.35" in commands[0]
    assert "gicp_max_iterations:=16" in commands[0]
    assert "recovery_search_enabled:=false" in commands[0]
    assert "recovery_after_failed_frames:=7" in commands[0]
    assert "recovery_confirm_frames:=3" in commands[0]
    assert "recovery_max_candidates_per_frame:=48" in commands[0]
    assert "recovery_wide_every_n_frames:=4" in commands[0]
    assert "recovery_fitness_ratio:=1.4" in commands[0]
    assert "recovery_fitness_abs:=0.02" in commands[0]


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
    assert result["process"]["status"] == "running"
    assert result["localizationStatus"]["data"]["fitness"] == 0.04
    assert result["pose"]["ok"] is True


def test_localization_manager_status_stays_starting_until_ros_status(tmp_path, monkeypatch):
    map_path = tmp_path / "lab_map" / "map.pcd"
    map_path.parent.mkdir()
    map_path.write_text("pcd", encoding="utf-8")
    monkeypatch.setattr("modules.localization.manager.get_mapping_manager", lambda: FakeMappingManager(map_path))
    monkeypatch.setattr("modules.localization.manager.subprocess.Popen", lambda *args, **kwargs: FakeProcess())
    monkeypatch.setattr("modules.localization.manager.get_ros_reader", lambda: FakeNoDataReader())

    manager = LocalizationManager(localizer_command=("localizer",), gpu_localizer_command=("python3",))
    manager.start({"mapName": "lab_map"})
    result = manager.status()

    assert result["state"] == "starting"
    assert result["process"]["status"] == "starting"


def test_localization_manager_refresh_treats_intentional_stop_as_clean():
    manager = LocalizationManager(localizer_command=("localizer",), gpu_localizer_command=("python3",))
    manager._process = FakeProcess(returncode=-15)
    manager._status = "stopping"
    manager._last_error = "previous error"

    manager._refresh_locked()

    assert manager._process is None
    assert manager._status == "stopped"
    assert manager._last_returncode == -15
    assert manager._last_error == ""


def test_localization_manager_refresh_keeps_unexpected_nonzero_exit_as_failed():
    manager = LocalizationManager(localizer_command=("localizer",), gpu_localizer_command=("python3",))
    manager._process = FakeProcess(returncode=2)
    manager._status = "running"

    manager._refresh_locked()

    assert manager._process is None
    assert manager._status == "failed"
    assert manager._last_returncode == 2
    assert manager._last_error == "Localizer exited with code 2."
