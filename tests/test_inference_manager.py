import json
import time

from modules.inference.action_logs import InferenceActionLogger
from modules.inference.manager import InferenceManager


def _arm():
    return {"joint1": 0.0, "joint2": 0.1, "joint3": -0.1, "joint4": 0.0, "joint5": 0.0, "joint6": 0.0, "gripper": 0.05}


def _chunk_message(steps, chunk_id="chunk_x"):
    actions = []
    for i in range(steps):
        actions.append(
            {
                "left": _arm(),
                "right": _arm(),
                "lift": {"height": 400.0 + 10.0 * i},
                "speed": {"vx": 0.0, "vy": 0.0},
            }
        )
    message = {"type": "action_chunk", "actions": actions}
    if chunk_id is not None:
        message["chunk_id"] = chunk_id
    return message


class FakeSession:
    def __init__(self, message):
        self._message = message
        self._connected = False
        self.url = None
        self.sent = []
        self.last_exchange_timing = {
            "sendMs": 1.2,
            "receiveMs": 34.5,
            "roundTripMs": 35.7,
            "ignoredMessages": 0,
        }

    def is_connected(self):
        return self._connected

    def connect(self, url, timeout_sec=10.0):
        self._connected = True
        self.url = url
        return True

    def request_chunk(self, message, timeout_sec=15.0):
        self.sent.append(message)
        return self._message

    def close(self, timeout_sec=5.0):
        self._connected = False
        self.url = None
        return True


class Recorder:
    def __init__(self):
        self.joint_calls = []
        self.chassis_calls = []
        self.chassis_stops = 0
        self.lift_calls = []
        self.lift_stops = 0

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


def _manager(message, recorder, snapshot=None, action_logger=None):
    if action_logger is None:
        action_logger = InferenceActionLogger(enabled=False)
    return InferenceManager(
        session=FakeSession(message),
        joint_publisher=recorder.joint,
        chassis_publisher=recorder.chassis,
        chassis_stopper=recorder.chassis_stop,
        lift_mover=recorder.lift,
        lift_stopper=recorder.lift_stop,
        observation_builder=lambda prompt: {"type": "observation", "prompt": prompt},
        arm_snapshot_reader=lambda: snapshot if snapshot is not None else {"left": None, "right": None},
        action_logger=action_logger,
    )


def test_connect_request_execute_flow():
    recorder = Recorder()
    manager = _manager(_chunk_message(3), recorder)

    assert manager.connect("ws://localhost:1234/infer")["ok"]
    req = manager.request_chunk({"prompt": "grasp"})
    assert req["ok"]
    assert req["chunkId"] == "chunk_0000"
    assert req["chunkSteps"] == 3
    assert req["chunkTiming"]["sendMs"] == 1.2
    assert req["chunkTiming"]["receiveMs"] == 34.5

    result = manager.execute_chunk({"steps": 2, "frequencyHz": 30, "maxJointSpeedDegS": 25})
    assert result["ok"]
    assert result["executedSteps"] == 2
    assert result["executionTiming"]["stepsPublished"] == 2
    assert result["executionTiming"]["totalMs"] >= 0
    assert abs(result["executionTiming"]["desiredPeriodMs"] - (1000.0 / 30.0)) < 1e-6
    assert result["executionTiming"]["stepPeriodAvgMs"] is not None
    assert manager.status()["executionTiming"]["stepsPublished"] == 2
    assert len(recorder.joint_calls) == 2
    assert len(recorder.chassis_calls) == 2
    # max_joint_speed forwarded.
    assert recorder.joint_calls[0]["max_joint_speed_deg_s"] == 25
    assert recorder.joint_calls[0]["left"]["positions"][0] == 0.0


def test_success_message_completes_without_chunk():
    recorder = Recorder()
    manager = _manager({"type": "action_chunk", "is_success": True}, recorder)

    assert manager.connect("ws://localhost:1234/infer")["ok"]
    req = manager.request_chunk({"prompt": "done"})
    assert req["ok"]
    assert req["code"] == "INFER-SUCCESS"
    assert req["isSuccess"] is True
    assert req["chunkSteps"] == 0

    status = manager.status()
    assert status["status"] == "completed"
    assert status["chunkId"] is None
    assert manager.execute_chunk({"steps": 1})["code"] == "INFER-NO-CHUNK"


def test_inference_action_logs_record_received_and_executed_chunks(tmp_path):
    recorder = Recorder()
    action_logger = InferenceActionLogger(log_dir=tmp_path)
    manager = _manager(_chunk_message(2, chunk_id="remote_chunk"), recorder, action_logger=action_logger)

    assert manager.connect("ws://localhost:1234/infer")["ok"]
    req = manager.request_chunk({"prompt": "grasp"})
    assert req["ok"]

    result = manager.execute_chunk({"steps": 1, "frequencyHz": 30, "mask": {"speed": False, "lift": False}})
    assert result["ok"]

    received = [json.loads(line) for line in (tmp_path / "received_actions.jsonl").read_text(encoding="utf-8").splitlines()]
    executed = [json.loads(line) for line in (tmp_path / "executed_actions.jsonl").read_text(encoding="utf-8").splitlines()]

    assert len(received) == 1
    assert received[0]["event"] == "received_action_chunk"
    assert received[0]["remoteChunkId"] == "remote_chunk"
    assert received[0]["localChunkId"] == "chunk_0000"
    assert received[0]["valid"] is True
    assert received[0]["stepCount"] == 2
    assert received[0]["rawChunk"]["chunk_id"] == "remote_chunk"
    assert received[0]["timing"]["receiveMs"] == 34.5

    assert len(executed) == 1
    assert executed[0]["event"] == "executed_action_chunk"
    assert executed[0]["localChunkId"] == "chunk_0000"
    assert executed[0]["status"] == "completed"
    assert executed[0]["requestedSteps"] == 1
    assert executed[0]["executedSteps"] == 1
    assert executed[0]["timing"]["stepsPublished"] == 1
    assert executed[0]["timing"]["publishMaxMs"] is not None
    assert executed[0]["actions"][0]["speed"] == {"vx": 0.0, "vy": 0.0, "wz": 0.0, "masked": True}
    assert executed[0]["actions"][0]["lift"] == {"masked": True}


def test_chunk_ids_are_local_and_reset_on_disconnect():
    recorder = Recorder()
    manager = _manager(_chunk_message(1, chunk_id=None), recorder)

    manager.connect("ws://localhost:1/infer")
    first = manager.request_chunk({})
    second = manager.request_chunk({})
    assert first["chunkId"] == "chunk_0000"
    assert second["chunkId"] == "chunk_0001"

    manager.disconnect()
    manager.connect("ws://localhost:1/infer")
    after_reset = manager.request_chunk({})
    assert after_reset["chunkId"] == "chunk_0000"


def test_remote_chunk_id_is_ignored():
    recorder = Recorder()
    manager = _manager(_chunk_message(1, chunk_id="remote_chunk"), recorder)

    manager.connect("ws://localhost:1/infer")
    req = manager.request_chunk({})
    assert req["chunkId"] == "chunk_0000"


def test_lift_dispatched_once_with_last_target():
    recorder = Recorder()
    manager = _manager(_chunk_message(3), recorder)
    manager.connect("ws://localhost:1/infer")
    manager.request_chunk({})
    manager.execute_chunk({"steps": 3, "frequencyHz": 30})
    # Wait for the async lift thread to run.
    time.sleep(0.2)
    assert len(recorder.lift_calls) == 1
    # The last remote lift step is 420 mm; the lifting controller receives metres.
    assert abs(recorder.lift_calls[0]["height"] - 0.42) < 1e-6


def test_execute_without_chunk_fails():
    recorder = Recorder()
    manager = _manager(_chunk_message(1), recorder)
    manager.connect("ws://localhost:1/infer")
    result = manager.execute_chunk({"steps": 1})
    assert not result["ok"]
    assert result["code"] == "INFER-NO-CHUNK"


def test_invalid_chunk_triggers_safe_hold():
    recorder = Recorder()
    bad = {"type": "action_chunk", "chunk_id": "bad", "actions": [{"left": {}, "right": {}}]}
    manager = _manager(bad, recorder)
    manager.connect("ws://localhost:1/infer")
    result = manager.request_chunk({})
    assert not result["ok"]
    assert result["code"] == "INFER-CHUNK-INVALID"
    # Safe hold: arm hold + chassis stop + lift stop were requested.
    assert any(call.get("hold") for call in recorder.joint_calls)
    assert recorder.chassis_stops >= 1
    assert recorder.lift_stops >= 1


def test_mask_disabled_left_arm_holds_and_skips_publish():
    recorder = Recorder()
    manager = _manager(_chunk_message(2), recorder)
    manager.connect("ws://localhost:1/infer")
    manager.request_chunk({})
    mask = {"left": {"enabled": False}, "right": {"enabled": True}}
    result = manager.execute_chunk({"steps": 2, "frequencyHz": 30, "mask": mask})
    assert result["ok"]
    # Left held once via hold; per-step joint payloads contain only the right side.
    assert any(call.get("hold") and call.get("left") for call in recorder.joint_calls)
    step_calls = [c for c in recorder.joint_calls if not c.get("hold")]
    assert step_calls and all("left" not in c and "right" in c for c in step_calls)


def test_mask_disabled_speed_publishes_zero():
    recorder = Recorder()
    manager = _manager(_chunk_message(1), recorder)
    manager.connect("ws://localhost:1/infer")
    manager.request_chunk({})
    manager.execute_chunk({"steps": 1, "frequencyHz": 30, "mask": {"speed": False}})
    assert recorder.chassis_calls[0] == {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0}


def test_mask_disabled_lift_not_dispatched():
    recorder = Recorder()
    manager = _manager(_chunk_message(2), recorder)
    manager.connect("ws://localhost:1/infer")
    manager.request_chunk({})
    manager.execute_chunk({"steps": 2, "frequencyHz": 30, "mask": {"lift": False}})
    time.sleep(0.15)
    assert recorder.lift_calls == []


def test_mask_single_joint_frozen_to_snapshot():
    recorder = Recorder()
    snap = {"left": [9.0] * 7, "right": [9.0] * 7}
    manager = _manager(_chunk_message(1), recorder, snapshot=snap)
    manager.connect("ws://localhost:1/infer")
    manager.request_chunk({})
    # Freeze left joint3 (index 2); the rest follow the model.
    mask = {"left": {"enabled": True, "joints": [True, True, False, True, True, True], "gripper": True}}
    result = manager.execute_chunk({"steps": 1, "frequencyHz": 30, "mask": mask})
    assert result["ok"]
    left_positions = next(c for c in recorder.joint_calls if c.get("left"))["left"]["positions"]
    assert left_positions[2] == 9.0  # frozen joint uses snapshot
    assert left_positions[0] == 0.0  # other joints follow the chunk


def test_mask_partial_without_feedback_errors():
    recorder = Recorder()
    manager = _manager(_chunk_message(1), recorder, snapshot={"left": None, "right": None})
    manager.connect("ws://localhost:1/infer")
    manager.request_chunk({})
    mask = {"left": {"enabled": True, "joints": [False, True, True, True, True, True], "gripper": True}}
    result = manager.execute_chunk({"steps": 1, "frequencyHz": 30, "mask": mask})
    assert not result["ok"]
    assert result["code"] == "INFER-MASK-NOFEEDBACK"


def test_stop_requests_safe_hold():
    recorder = Recorder()
    manager = _manager(_chunk_message(1), recorder)
    manager.connect("ws://localhost:1/infer")
    result = manager.stop()
    assert result["ok"]
    assert any(call.get("hold") for call in recorder.joint_calls)
    assert recorder.chassis_stops >= 1
    assert recorder.lift_stops >= 1
