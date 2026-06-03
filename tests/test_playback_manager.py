import pytest

from modules.playback import PlaybackLoadError, require_timestamps
from modules.playback_manager import PlaybackManager


def _arm_action():
    return [0.0, 0.1, -0.1, 0.0, 0.0, 0.0, 0.05]


def _action(index=0):
    return _arm_action() + _arm_action() + [0.4 + index * 0.01, index * 0.01, 0.0, 0.0]


def _dataset():
    return {
        "name": "episode.parquet",
        "frames": [
            {"timestamp": 100.0, "seconds": 0.0, "frameIndex": 3, "action": _action(0)},
            {"timestamp": 100.001, "seconds": 0.001, "frameIndex": 4, "action": _action(1)},
        ],
    }


class Recorder:
    def __init__(self):
        self.enable_calls = []
        self.joint_calls = []
        self.chassis_calls = []
        self.chassis_stops = 0
        self.lift_calls = []
        self.lift_stops = 0

    def enable(self, enabled):
        self.enable_calls.append(enabled)
        return {"ok": True, "code": "ROS-W-PUBLISHED", "detail": "ok"}

    def joint(self, payload):
        self.joint_calls.append(payload)
        return {"ok": True, "code": "PIPER-C-PUBLISHED", "detail": "ok"}

    def chassis(self, payload):
        self.chassis_calls.append(payload)
        return {"ok": True, "code": "CHASSIS-C-PUBLISHED", "detail": "ok"}

    def chassis_stop(self, payload=None):
        self.chassis_stops += 1
        return {"ok": True}

    def lift(self, payload):
        self.lift_calls.append(payload)
        return {"ok": True}

    def lift_stop(self, payload=None):
        self.lift_stops += 1
        return {"ok": True}


def _manager(recorder, dataset=None):
    return PlaybackManager(
        dataset_loader=lambda _payload: {"ok": True, "dataset": dataset or _dataset()},
        piper_enable_publisher=recorder.enable,
        joint_publisher=recorder.joint,
        chassis_publisher=recorder.chassis,
        chassis_stopper=recorder.chassis_stop,
        lift_mover=recorder.lift,
        lift_stopper=recorder.lift_stop,
    )


def test_timestamp_required():
    with pytest.raises(PlaybackLoadError) as exc:
        require_timestamps([0.0, None], "Parquet")

    assert exc.value.code == "PLAYBACK-TIMESTAMP"


def test_start_rejects_frames_without_timestamp():
    recorder = Recorder()
    manager = _manager(recorder, dataset={"frames": [{"action": _action(0)}]})
    assert manager.enable_piper({"enabled": True, "repeat": 1})["ok"]

    result = manager.start({"path": "episode.parquet"})

    assert not result["ok"]
    assert result["code"] == "PLAYBACK-TIMESTAMP"
    assert recorder.joint_calls == []
    assert recorder.chassis_calls == []


def test_enable_then_start_publishes_timestamped_actions():
    recorder = Recorder()
    manager = _manager(recorder)

    disabled = manager.start({"path": "episode.parquet"})
    assert not disabled["ok"]
    assert disabled["code"] == "PLAYBACK-DISABLED"

    assert manager.enable_piper({"enabled": True, "repeat": 1})["ok"]
    started = manager.start({"path": "episode.parquet", "maxJointSpeedDegS": 25})

    assert started["ok"]
    assert started["totalFrames"] == 2
    assert manager.wait(timeout=1.0)

    status = manager.status()
    assert status["status"] == "completed"
    assert status["executedFrames"] == 2
    assert recorder.enable_calls == [True]

    joint_steps = [payload for payload in recorder.joint_calls if "left" in payload]
    assert len(joint_steps) == 2
    assert joint_steps[0]["max_joint_speed_deg_s"] == 25
    assert joint_steps[0]["left"]["positions"] == _arm_action()
    assert joint_steps[1]["right"]["positions"] == _arm_action()

    assert len(recorder.chassis_calls) == 2
    assert recorder.chassis_calls[0]["linearX"] == 0.0
    assert recorder.chassis_calls[1]["linearX"] == 0.01
    assert "commandSequence" not in recorder.chassis_calls[0]
    assert recorder.chassis_stops >= 1
    assert recorder.lift_stops >= 1


def test_disabling_playback_does_not_publish_false_enable():
    recorder = Recorder()
    manager = _manager(recorder)

    assert manager.enable_piper({"enabled": True, "repeat": 1})["ok"]
    disabled = manager.enable_piper({"enabled": False, "repeat": 1})

    assert disabled["ok"]
    assert disabled["robotEnabled"] is False
    assert recorder.enable_calls == [True]

    start = manager.start({"path": "episode.parquet"})
    assert not start["ok"]
    assert start["code"] == "PLAYBACK-DISABLED"


def test_optional_platform_values_can_be_missing():
    recorder = Recorder()
    dataset = {
        "name": "episode.mcap",
        "frames": [
            {
                "timestamp": 100.0,
                "seconds": 0.0,
                "frameIndex": 0,
                "action": _arm_action() + _arm_action() + [None, 0.02, None, -0.1],
            }
        ],
    }
    manager = _manager(recorder, dataset=dataset)

    assert manager.enable_piper({"enabled": True, "repeat": 1})["ok"]
    started = manager.start({"path": "episode.mcap"})

    assert started["ok"]
    assert manager.wait(timeout=1.0)
    assert recorder.chassis_calls[0]["linearX"] == 0.02
    assert recorder.chassis_calls[0]["linearY"] == 0.0
    assert recorder.chassis_calls[0]["angularZ"] == -0.1
    assert recorder.lift_calls == []
