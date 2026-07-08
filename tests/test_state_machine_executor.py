import math
import threading
import time

from modules.state_machine import executor as executor_module
from modules.state_machine.executor import StateMachineExecutor


def _node(node_id, task_type, params=None, outgoing=None):
    return {
        "id": node_id,
        "type": "task",
        "taskType": task_type,
        "title": node_id,
        "params": params or {},
        "outgoingIds": outgoing or [],
    }


def _start(outgoing):
    return {"id": "sm_start", "type": "start", "title": "Start", "params": {}, "outgoingIds": outgoing}


def _end():
    return {"id": "sm_end", "type": "end", "title": "End", "params": {}, "outgoingIds": []}


def _wait_terminal(manager, timeout_sec=1.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        run = manager.status()["run"]
        if not run["active"]:
            return run
        time.sleep(0.01)
    raise AssertionError(f"State machine did not finish: {manager.status()['run']}")


class FakeNavigationManager:
    def __init__(self, statuses):
        self.started = []
        self.stopped = []
        self._statuses = list(statuses)
        self._last_status = {
            "ok": True,
            "status": "running",
            "phase": "lateral_translate",
            "detail": "Navigation running.",
        }

    def start(self, payload):
        self.started.append(payload)
        return {
            "ok": True,
            "code": "NAV-STARTED",
            "status": "running",
            "phase": "lateral_translate",
            "detail": "Navigation started.",
        }

    def status(self):
        if self._statuses:
            self._last_status = self._statuses.pop(0)
        return dict(self._last_status)

    def stop(self, detail="Navigation stopped."):
        self.stopped.append(detail)
        self._last_status = {
            "ok": True,
            "code": "NAV-STOPPED",
            "status": "stopped",
            "phase": "stopped",
            "detail": detail,
        }
        return dict(self._last_status)


def _arm_positions(joint1=0.0, gripper=0.0):
    return [joint1, 0.0, 0.0, 0.0, 0.0, 0.0, gripper]


def _arm_sample(left=None, right=None):
    return {
        "left": left or _arm_positions(),
        "right": right or _arm_positions(),
    }


class FakeRosReader:
    def __init__(self, samples):
        self.samples = list(samples)
        self.index = 0
        self.calls = []

    def read(self, key, timeout_sec=0.0):
        self.calls.append((key, timeout_sec))
        sample = self.samples[min(self.index, len(self.samples) - 1)]
        if key == executor_module.WAIT_LEFT_JOINT_STATE_KEY:
            positions = sample["left"]
        elif key == executor_module.WAIT_RIGHT_JOINT_STATE_KEY:
            positions = sample["right"]
            self.index += 1
        else:
            return {"ok": False, "detail": f"unknown key {key}"}
        return {"ok": True, "stale": False, "data": {"position": list(positions)}}


class ExternalPiperRosReader:
    def __init__(self, sample):
        self.sample = sample
        self.calls = []

    def read(self, key, timeout_sec=0.0):
        self.calls.append((key, timeout_sec))
        if key == "piper_left_joint_state":
            return {"ok": True, "stale": False, "data": {"position": list(self.sample["left"])}}
        if key == "piper_right_joint_state":
            return {"ok": True, "stale": False, "data": {"position": list(self.sample["right"])}}
        return {"ok": False, "detail": f"no data for {key}"}


class SequencedPiperJointReader:
    def __init__(self, samples, advance_after_side="left"):
        self.samples = list(samples)
        self.advance_after_side = advance_after_side
        self.index = 0
        self.calls = []

    def read(self, key, timeout_sec=0.0):
        self.calls.append((key, timeout_sec))
        sample = self.samples[min(self.index, len(self.samples) - 1)]
        if key in executor_module.WAIT_LEFT_JOINT_STATE_KEYS:
            side = "left"
        elif key in executor_module.WAIT_RIGHT_JOINT_STATE_KEYS:
            side = "right"
        else:
            return {"ok": False, "detail": f"no data for {key}"}
        positions = sample[side]
        if side == self.advance_after_side:
            self.index += 1
        return {
            "ok": True,
            "stale": False,
            "topic": f"/{side}_joint_state",
            "data": {"position": list(positions)},
        }


class FakeTopicReader:
    def __init__(self, baseline, next_result):
        self.baseline = dict(baseline)
        if isinstance(next_result, list):
            self.next_results = [dict(item) for item in next_result]
        else:
            self.next_results = [dict(next_result)]
        self.read_calls = []
        self.read_after_calls = []

    def _next_result(self):
        if len(self.next_results) > 1:
            return dict(self.next_results.pop(0))
        return dict(self.next_results[0])

    def read(self, key, timeout_sec=0.0):
        self.read_calls.append((key, timeout_sec))
        return dict(self.baseline)

    def read_after(self, key, after_sequence=None, timeout_sec=0.0):
        self.read_after_calls.append((key, after_sequence, timeout_sec))
        return self._next_result()

    def read_bool_topic(self, topic, timeout_sec=0.0):
        self.read_calls.append((topic, timeout_sec))
        return dict(self.baseline)

    def read_bool_topic_after(self, topic, after_sequence=None, timeout_sec=0.0):
        self.read_after_calls.append((topic, after_sequence, timeout_sec))
        return self._next_result()


class FakeRosWriter:
    def __init__(self):
        self.published = []

    def publish(self, key, payload):
        self.published.append((key, dict(payload)))
        return {
            "ok": True,
            "code": "ROS-W-PUBLISHED",
            "detail": f"Published command to /{key}.",
            "key": key,
            "topic": f"/{key}",
            "messageType": "std_msgs/msg/Bool",
            "publishedAt": "12:00:00",
        }

    def publish_bool_topic(self, topic, value=True):
        self.published.append((topic, {"data": bool(value)}))
        return {
            "ok": True,
            "code": "ROS-W-PUBLISHED",
            "detail": f"Published bool signal to {topic}.",
            "key": f"state_machine_bool:{topic}",
            "topic": topic,
            "messageType": "std_msgs/msg/Bool",
            "data": bool(value),
            "publishedAt": "12:00:00",
        }


class FakeInferenceManager:
    def __init__(self, request_results, execute_results=None):
        self.request_results = [dict(item) for item in request_results]
        self.execute_results = [dict(item) for item in (execute_results or [])]
        self.connected = []
        self.requests = []
        self.executions = []
        self.stopped = []

    def _next(self, values, default):
        if len(values) > 1:
            return dict(values.pop(0))
        if values:
            return dict(values[0])
        return dict(default)

    def connect(self, url):
        self.connected.append(url)
        return {"ok": True, "code": "INFER-CONNECTED", "detail": "connected", "remoteUrl": url}

    def request_chunk(self, payload):
        self.requests.append(dict(payload))
        return self._next(
            self.request_results,
            {"ok": True, "code": "INFER-SUCCESS", "detail": "success", "isSuccess": True, "chunkSteps": 0},
        )

    def execute_chunk(self, payload):
        self.executions.append(dict(payload))
        return self._next(
            self.execute_results,
            {"ok": True, "code": "INFER-EXECUTED", "detail": "executed", "executedSteps": payload.get("steps", 1), "requestedSteps": payload.get("steps", 1)},
        )

    def stop(self, reason="stop"):
        self.stopped.append(reason)
        return {"ok": True, "code": "INFER-STOPPED", "detail": f"stopped {reason}"}


class BlockingInferenceManager(FakeInferenceManager):
    def __init__(self):
        super().__init__([{"ok": True, "code": "INFER-CHUNK-READY", "detail": "ready", "isSuccess": False, "chunkId": "chunk_0000", "chunkSteps": 1}])
        self.executing = threading.Event()
        self.stopped_event = threading.Event()

    def execute_chunk(self, payload):
        self.executions.append(dict(payload))
        self.executing.set()
        self.stopped_event.wait(timeout=1.0)
        return {
            "ok": False,
            "code": "INFER-STOPPED",
            "detail": "Execution stopped before completing the requested steps.",
            "executedSteps": 0,
            "requestedSteps": payload.get("steps", 1),
        }

    def stop(self, reason="stop"):
        result = super().stop(reason=reason)
        self.stopped_event.set()
        return result


def test_navigation_state_runs_to_completed(monkeypatch):
    nav_status = {
        "ok": True,
        "code": "NAV-STATUS",
        "status": "completed",
        "phase": "completed",
        "detail": "Navigation completed.",
        "currentPose": {"x": 1.0, "y": 2.0, "yawDeg": 30.0},
        "errors": {"distance": 0.0, "bodyX": 0.0, "bodyY": 0.0, "yawDeg": 0.0},
        "command": {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0},
    }
    fake_navigation = FakeNavigationManager([nav_status])
    monkeypatch.setattr(executor_module, "get_navigation_manager", lambda: fake_navigation)
    manager = StateMachineExecutor(poll_interval_sec=0.01)
    params = {
        "targetName": "工作台",
        "x": 1.0,
        "y": 2.0,
        "yawDeg": 30.0,
        "mode": "lateral",
        "maxLinearMps": 0.2,
        "maxLateralMps": 0.15,
        "maxAngularRadS": 0.5,
        "positionToleranceM": 0.05,
        "yawToleranceDeg": 3,
        "localizationStaleSec": 0.8,
        "controlRateHz": 20,
    }

    result = manager.start(
        {
            "name": "导航流程",
            "nodes": [
                _start(["nav"]),
                _node("nav", "navigation", params=params, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert fake_navigation.started == [params]
    assert run["status"] == "completed"
    assert run["path"] == ["sm_start", "nav", "sm_end"]
    assert run["completedIds"] == ["sm_start", "nav", "sm_end"]
    assert run["taskStatus"]["nodeId"] == "nav"
    assert run["taskStatus"]["taskType"] == "navigation"
    assert run["taskStatus"]["status"] == "completed"
    assert run["taskStatus"]["data"]["phase"] == "completed"


def test_navigation_state_waits_while_navigation_waits_for_localization(monkeypatch):
    fake_navigation = FakeNavigationManager(
        [
            {
                "ok": True,
                "code": "NAV-STATUS",
                "status": "running",
                "phase": "waiting_localization",
                "detail": "Waiting for localization pose.",
                "lastLocalizationError": "No message received from /localization/pose.",
            },
            {
                "ok": True,
                "code": "NAV-STATUS",
                "status": "completed",
                "phase": "completed",
                "detail": "Navigation completed.",
                "currentPose": {"x": 1.0, "y": 0.0, "yawDeg": 0.0},
                "errors": {"distance": 0.0, "bodyX": 0.0, "bodyY": 0.0, "yawDeg": 0.0},
                "command": {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0},
            },
        ]
    )
    monkeypatch.setattr(executor_module, "get_navigation_manager", lambda: fake_navigation)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    manager.start(
        {
            "name": "等待定位流程",
            "nodes": [
                _start(["nav"]),
                _node("nav", "navigation", params={"mode": "lateral", "x": 1, "y": 0, "yawDeg": 0}, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert run["status"] == "completed"
    assert run["taskStatus"]["status"] == "completed"
    assert run["taskStatus"]["data"]["phase"] == "completed"


def test_reset_odom_state_runs_once_and_continues(monkeypatch):
    calls = []

    def fake_reset(payload):
        calls.append(payload)
        return {
            "ok": True,
            "code": "CHASSIS-C-ODOM-RESET",
            "detail": "reset ok",
            "action": "reset_odom",
            "service": "/reset_odom",
        }

    monkeypatch.setattr(executor_module, "reset_chassis_odometry", fake_reset)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "归零流程",
            "nodes": [
                _start(["reset"]),
                _node("reset", "reset_odom", outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert calls == [{}]
    assert run["status"] == "completed"
    assert run["path"] == ["sm_start", "reset", "sm_end"]
    assert run["completedIds"] == ["sm_start", "reset", "sm_end"]
    assert run["taskStatus"]["nodeId"] == "reset"
    assert run["taskStatus"]["taskType"] == "reset_odom"
    assert run["taskStatus"]["status"] == "completed"
    assert run["taskStatus"]["data"]["phase"] == "completed"
    assert run["taskStatus"]["data"]["service"] == "/reset_odom"


def test_inference_state_loops_until_remote_success(monkeypatch):
    fake_inference = FakeInferenceManager(
        [
            {
                "ok": True,
                "code": "INFER-CHUNK-READY",
                "detail": "chunk ready",
                "isSuccess": False,
                "chunkId": "chunk_0000",
                "chunkSteps": 2,
            },
            {
                "ok": True,
                "code": "INFER-SUCCESS",
                "detail": "success",
                "isSuccess": True,
                "chunkSteps": 0,
            },
        ],
        [
            {
                "ok": True,
                "code": "INFER-EXECUTED",
                "detail": "executed",
                "executedSteps": 2,
                "requestedSteps": 2,
            }
        ],
    )
    fake_writer = FakeRosWriter()
    monkeypatch.setattr(executor_module, "get_inference_manager", lambda: fake_inference)
    monkeypatch.setattr(executor_module, "get_ros_writer", lambda: fake_writer)
    manager = StateMachineExecutor(poll_interval_sec=0.01)
    params = {
        "remoteUrl": "ws://localhost:1234/infer",
        "prompt": "pick grape juice",
        "steps": 2,
        "frequencyHz": 30,
        "maxJointSpeedDegS": 25,
        "maxLinearMps": 0.2,
        "maxLateralMps": 0.15,
        "maxAngularRadS": 0.5,
    }

    result = manager.start(
        {
            "name": "推理流程",
            "nodes": [
                _start(["infer"]),
                _node("infer", "inference", params=params, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert fake_inference.connected == ["ws://localhost:1234/infer"]
    assert len(fake_inference.requests) == 2
    assert fake_inference.requests[0]["prompt"] == "pick grape juice"
    assert fake_inference.executions == [{"steps": 2, "frequencyHz": 30.0, "maxJointSpeedDegS": 25.0}]
    assert fake_writer.published == [("piper_enable_all", {"enabled": True})] * 3
    assert run["status"] == "completed"
    assert run["path"] == ["sm_start", "infer", "sm_end"]
    assert run["taskStatus"]["nodeId"] == "infer"
    assert run["taskStatus"]["taskType"] == "inference"
    assert run["taskStatus"]["status"] == "completed"
    assert run["taskStatus"]["data"]["phase"] == "success"
    assert run["taskStatus"]["data"]["isSuccess"] is True
    assert run["taskStatus"]["data"]["totalExecutedSteps"] == 2


def test_inference_state_request_failure_fails_state_machine(monkeypatch):
    fake_inference = FakeInferenceManager(
        [
            {
                "ok": False,
                "code": "INFER-WS-DISCONNECTED",
                "detail": "remote disconnected",
            }
        ]
    )
    monkeypatch.setattr(executor_module, "get_inference_manager", lambda: fake_inference)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "推理失败流程",
            "nodes": [
                _start(["infer"]),
                _node(
                    "infer",
                    "inference",
                    params={"remoteUrl": "ws://localhost:1234/infer", "autoEnablePiper": False},
                    outgoing=["sm_end"],
                ),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert run["status"] == "failed"
    assert run["currentId"] == "infer"
    assert run["error"] == "remote disconnected"
    assert run["taskStatus"]["taskType"] == "inference"
    assert run["taskStatus"]["status"] == "failed"
    assert run["taskStatus"]["data"]["requestCode"] == "INFER-WS-DISCONNECTED"


def test_state_machine_stop_stops_current_inference(monkeypatch):
    fake_inference = BlockingInferenceManager()
    monkeypatch.setattr(executor_module, "get_inference_manager", lambda: fake_inference)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    manager.start(
        {
            "name": "停止推理流程",
            "nodes": [
                _start(["infer"]),
                _node(
                    "infer",
                    "inference",
                    params={"remoteUrl": "ws://localhost:1234/infer", "autoEnablePiper": False},
                    outgoing=["sm_end"],
                ),
                _end(),
            ],
        }
    )
    assert fake_inference.executing.wait(timeout=1.0)

    stop_result = manager.stop()
    run = stop_result["run"]

    assert fake_inference.stopped == ["state_machine"]
    assert run["status"] == "stopped"
    assert run["active"] is False
    assert run["taskStatus"]["taskType"] == "inference"
    assert run["taskStatus"]["status"] == "stopped"


def _left_piper_joint_params(**overrides):
    params = {
        "side": "left",
        "leftJoint1Deg": 10,
        "leftJoint2Deg": 20,
        "leftJoint3Deg": -30,
        "leftJoint4Deg": 5,
        "leftJoint5Deg": 0,
        "leftJoint6Deg": 0,
        "leftGripperM": 0.03,
        "maxJointSpeedDegS": 7,
        "gripperEffort": 1.2,
        "toleranceDeg": 0.5,
        "gripperToleranceM": 0.001,
        "stableSec": 0.01,
        "timeoutSec": 1,
    }
    params.update(overrides)
    return params


def _left_piper_target_positions():
    return [
        math.radians(10),
        math.radians(20),
        math.radians(-30),
        math.radians(5),
        0.0,
        0.0,
        0.03,
    ]


def test_piper_joint_state_default_stable_sec_is_two_seconds():
    params = _left_piper_joint_params()
    params.pop("stableSec")

    config = StateMachineExecutor._piper_joint_config(params)

    assert config["stableSec"] == 2.0


def test_piper_joint_state_publishes_and_waits_until_target_reached(monkeypatch):
    target = _left_piper_target_positions()
    reader = SequencedPiperJointReader(
        [
            _arm_sample(left=[0.0] * 7),
            _arm_sample(left=target),
            _arm_sample(left=target),
        ],
        advance_after_side="left",
    )
    published = []

    def fake_publish(payload):
        published.append(payload)
        return {
            "ok": True,
            "code": "PIPER-C-PUBLISHED",
            "detail": "ok",
            "topics": ["/joint_states_gripper_l"],
            "publishedAt": "12:00:00",
        }

    monkeypatch.setattr(executor_module, "get_ros_reader", lambda: reader)
    monkeypatch.setattr(executor_module, "publish_joint_targets", fake_publish)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "机械臂控制流程",
            "nodes": [
                _start(["arm"]),
                _node("arm", "piper_joint", params=_left_piper_joint_params(), outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert run["status"] == "completed"
    assert run["path"] == ["sm_start", "arm", "sm_end"]
    assert len(published) == 1
    payload = published[0]
    assert payload["max_joint_speed_deg_s"] == 7.0
    assert payload["gripper_effort"] == 1.2
    assert all(abs(actual - expected) < 1e-9 for actual, expected in zip(payload["left"]["positions"], target))
    assert "right" not in payload
    assert run["taskStatus"]["taskType"] == "piper_joint"
    assert run["taskStatus"]["status"] == "completed"
    assert run["taskStatus"]["data"]["phase"] == "completed"
    assert run["taskStatus"]["data"]["withinTolerance"] is True
    assert run["taskStatus"]["data"]["topics"] == ["/joint_states_gripper_l"]


def test_piper_joint_state_completion_ignores_gripper_error(monkeypatch):
    target = _left_piper_target_positions()
    clamped_gripper = list(target)
    clamped_gripper[6] = 0.0
    reader = SequencedPiperJointReader(
        [
            _arm_sample(left=[0.0] * 7),
            _arm_sample(left=clamped_gripper),
            _arm_sample(left=clamped_gripper),
        ],
        advance_after_side="left",
    )
    published = []

    def fake_publish(payload):
        published.append(payload)
        return {
            "ok": True,
            "code": "PIPER-C-PUBLISHED",
            "detail": "ok",
            "topics": ["/joint_states_gripper_l"],
        }

    monkeypatch.setattr(executor_module, "get_ros_reader", lambda: reader)
    monkeypatch.setattr(executor_module, "publish_joint_targets", fake_publish)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "机械臂夹取流程",
            "nodes": [
                _start(["arm"]),
                _node("arm", "piper_joint", params=_left_piper_joint_params(), outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert run["status"] == "completed"
    assert len(published) == 1
    data = run["taskStatus"]["data"]
    assert data["withinTolerance"] is True
    assert data["jointWithinTolerance"] is True
    assert data["gripperWithinTolerance"] is False
    assert data["maxGripperErrorM"] == 0.03


def test_piper_joint_state_rejects_incomplete_target(monkeypatch):
    published = []
    monkeypatch.setattr(executor_module, "publish_joint_targets", lambda payload: published.append(payload))
    manager = StateMachineExecutor(poll_interval_sec=0.01)
    params = _left_piper_joint_params()
    params.pop("leftJoint6Deg")

    result = manager.start(
        {
            "name": "机械臂参数不完整",
            "nodes": [
                _start(["arm"]),
                _node("arm", "piper_joint", params=params, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert run["status"] == "failed"
    assert "leftJoint6Deg is required" in run["error"]
    assert published == []


def test_piper_joint_state_times_out_when_feedback_never_reaches_target(monkeypatch):
    reader = SequencedPiperJointReader([_arm_sample(left=[0.0] * 7)], advance_after_side="left")
    published = []

    def fake_publish(payload):
        published.append(payload)
        return {
            "ok": True,
            "code": "PIPER-C-PUBLISHED",
            "detail": "ok",
            "topics": ["/joint_states_gripper_l"],
        }

    monkeypatch.setattr(executor_module, "get_ros_reader", lambda: reader)
    monkeypatch.setattr(executor_module, "publish_joint_targets", fake_publish)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "机械臂到位超时",
            "nodes": [
                _start(["arm"]),
                _node("arm", "piper_joint", params=_left_piper_joint_params(timeoutSec=0.1), outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert run["status"] == "failed"
    assert "not reached" in run["error"]
    assert len(published) == 1
    assert run["taskStatus"]["data"]["phase"] == "failed"


def test_loop_run_restarts_after_end_until_stopped(monkeypatch):
    calls = []

    def fake_reset(payload):
        calls.append(payload)
        return {
            "ok": True,
            "code": "CHASSIS-C-ODOM-RESET",
            "detail": "reset ok",
            "action": "reset_odom",
            "service": "/reset_odom",
        }

    monkeypatch.setattr(executor_module, "reset_chassis_odometry", fake_reset)
    monkeypatch.setattr(executor_module, "LOOP_RESTART_PAUSE_SEC", 0.005)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "循环归零流程",
            "loop": True,
            "nodes": [
                _start(["reset"]),
                _node("reset", "reset_odom", outgoing=["sm_end"]),
                _end(),
            ],
        }
    )

    deadline = time.time() + 1.0
    run = manager.status()["run"]
    while time.time() < deadline:
        run = manager.status()["run"]
        if run["completedIterations"] >= 2:
            break
        time.sleep(0.01)
    else:
        raise AssertionError(f"State machine did not loop twice: {run}")

    assert result["ok"] is True
    assert run["active"] is True
    assert run["status"] == "running"
    assert run["loop"] is True
    assert run["iteration"] >= 2
    assert run["completedIterations"] >= 2
    assert len(calls) >= 2

    stop_result = manager.stop()
    stopped_run = stop_result["run"]

    assert stopped_run["status"] == "stopped"
    assert stopped_run["active"] is False
    assert stopped_run["loop"] is True
    assert stopped_run["completedIterations"] >= 2


def test_reset_odom_state_failure_fails_state_machine(monkeypatch):
    def fake_reset(payload):
        return {
            "ok": False,
            "code": "CHASSIS-C-ODOM-RESET-FAILED",
            "detail": "reset failed",
            "action": "reset_odom",
            "service": "/reset_odom",
        }

    monkeypatch.setattr(executor_module, "reset_chassis_odometry", fake_reset)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "归零失败流程",
            "nodes": [
                _start(["reset"]),
                _node("reset", "reset_odom", outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert run["status"] == "failed"
    assert run["currentId"] == "reset"
    assert run["error"] == "reset failed"
    assert run["taskStatus"]["nodeId"] == "reset"
    assert run["taskStatus"]["taskType"] == "reset_odom"
    assert run["taskStatus"]["status"] == "failed"
    assert run["taskStatus"]["data"]["phase"] == "failed"


def test_wait_state_completes_after_gripper_moves_then_stays_stable(monkeypatch):
    fake_ros = FakeRosReader(
        [
            _arm_sample(),
            _arm_sample(),
            _arm_sample(left=_arm_positions(gripper=0.003)),
            _arm_sample(left=_arm_positions(gripper=0.003)),
            _arm_sample(left=_arm_positions(gripper=0.003)),
            _arm_sample(left=_arm_positions(gripper=0.003)),
        ]
    )
    monkeypatch.setattr(executor_module, "get_ros_reader", lambda: fake_ros)
    monkeypatch.setattr(executor_module, "WAIT_MIN_STABLE_SEC", 0.01)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "等待流程",
            "nodes": [
                _start(["wait"]),
                _node("wait", "wait", params={"stableSec": 0.01}, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert run["status"] == "completed"
    assert run["path"] == ["sm_start", "wait", "sm_end"]
    assert run["completedIds"] == ["sm_start", "wait", "sm_end"]
    assert run["taskStatus"]["nodeId"] == "wait"
    assert run["taskStatus"]["taskType"] == "wait"
    assert run["taskStatus"]["status"] == "completed"
    assert run["taskStatus"]["data"]["phase"] == "completed"
    assert fake_ros.calls


def test_wait_joint_reader_falls_back_to_external_piper_topics():
    reader = ExternalPiperRosReader(
        _arm_sample(
            left=_arm_positions(joint1=0.2, gripper=0.003),
            right=_arm_positions(joint1=-0.2, gripper=0.004),
        )
    )
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    snapshot = manager._read_wait_joint_positions(reader)

    assert snapshot["joints"][0] == 0.2
    assert snapshot["joints"][6] == -0.2
    assert snapshot["grippers"] == [0.003, 0.004]
    assert ("piper_left_joint_state_double", executor_module.WAIT_JOINT_READ_WAIT_SEC) in reader.calls
    assert ("piper_left_joint_state", executor_module.WAIT_JOINT_READ_WAIT_SEC) in reader.calls


def test_wait_state_rejects_invalid_stable_sec(monkeypatch):
    monkeypatch.setattr(executor_module, "get_ros_reader", lambda: FakeRosReader([_arm_sample()]))
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "等待流程",
            "nodes": [
                _start(["wait"]),
                _node("wait", "wait", params={"stableSec": 0}, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert run["status"] == "failed"
    assert run["currentId"] == "wait"
    assert "stableSec must be" in run["error"]
    assert run["taskStatus"]["status"] == "failed"


def test_wait_state_does_not_finish_before_arm_or_gripper_moves(monkeypatch):
    monkeypatch.setattr(executor_module, "get_ros_reader", lambda: FakeRosReader([_arm_sample()]))
    monkeypatch.setattr(executor_module, "WAIT_MIN_STABLE_SEC", 0.01)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "等待流程",
            "nodes": [
                _start(["wait"]),
                _node("wait", "wait", params={"stableSec": 0.01}, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    time.sleep(0.05)
    run = manager.status()["run"]

    assert result["ok"] is True
    assert run["active"] is True
    assert run["currentId"] == "wait"
    assert run["taskStatus"]["data"]["phase"] == "waiting_motion"

    stop_result = manager.stop()
    assert stop_result["run"]["status"] == "stopped"


def test_topic_publish_state_publishes_true_and_continues(monkeypatch):
    fake_writer = FakeRosWriter()
    monkeypatch.setattr(executor_module, "get_ros_writer", lambda: fake_writer)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "发布信号流程",
            "nodes": [
                _start(["publish"]),
                _node("publish", "topic_publish", params={"topicName": "/state_machine/start"}, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert fake_writer.published == [("/state_machine/start", {"data": True})]
    assert run["status"] == "completed"
    assert run["path"] == ["sm_start", "publish", "sm_end"]
    assert run["taskStatus"]["nodeId"] == "publish"
    assert run["taskStatus"]["taskType"] == "topic_publish"
    assert run["taskStatus"]["status"] == "completed"
    assert run["taskStatus"]["data"]["phase"] == "completed"
    assert run["taskStatus"]["data"]["key"] == "/state_machine/start"
    assert run["taskStatus"]["data"]["topic"] == "/state_machine/start"


def test_topic_wait_state_waits_for_next_message_and_continues(monkeypatch):
    fake_reader = FakeTopicReader(
        {
            "ok": True,
            "code": "ROS-R-OK",
            "detail": "Latest message from /data_collection/start is 10 ms old.",
            "key": "data_collection_start",
            "topic": "/data_collection/start",
            "messageType": "std_msgs/msg/Bool",
            "sequence": 7,
            "data": {"data": True},
        },
        {
            "ok": True,
            "code": "ROS-R-OK",
            "detail": "Latest message from /data_collection/start is 0 ms old.",
            "key": "data_collection_start",
            "topic": "/data_collection/start",
            "messageType": "std_msgs/msg/Bool",
            "sequence": 8,
            "data": {"data": True},
        },
    )
    monkeypatch.setattr(executor_module, "get_ros_reader", lambda: fake_reader)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "监听信号流程",
            "nodes": [
                _start(["wait_signal"]),
                _node("wait_signal", "topic_wait", params={"topicName": "/data_collection/start"}, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert fake_reader.read_calls == [("/data_collection/start", 0.0)]
    assert fake_reader.read_after_calls
    assert fake_reader.read_after_calls[0][0] == "/data_collection/start"
    assert fake_reader.read_after_calls[0][1] == 7
    assert run["status"] == "completed"
    assert run["path"] == ["sm_start", "wait_signal", "sm_end"]
    assert run["taskStatus"]["nodeId"] == "wait_signal"
    assert run["taskStatus"]["taskType"] == "topic_wait"
    assert run["taskStatus"]["status"] == "completed"
    assert run["taskStatus"]["data"]["phase"] == "completed"
    assert run["taskStatus"]["data"]["sequence"] == 8


def test_topic_wait_state_ignores_false_until_true(monkeypatch):
    fake_reader = FakeTopicReader(
        {
            "ok": True,
            "code": "ROS-R-OK",
            "detail": "Latest message from /data_collection/start is 10 ms old.",
            "key": "data_collection_start",
            "topic": "/data_collection/start",
            "messageType": "std_msgs/msg/Bool",
            "sequence": 7,
            "data": {"data": False},
        },
        [
            {
                "ok": True,
                "code": "ROS-R-OK",
                "detail": "Latest message from /data_collection/start is 0 ms old.",
                "key": "data_collection_start",
                "topic": "/data_collection/start",
                "messageType": "std_msgs/msg/Bool",
                "sequence": 8,
                "data": {"data": False},
            },
            {
                "ok": True,
                "code": "ROS-R-OK",
                "detail": "Latest message from /data_collection/start is 0 ms old.",
                "key": "data_collection_start",
                "topic": "/data_collection/start",
                "messageType": "std_msgs/msg/Bool",
                "sequence": 9,
                "data": {"data": True},
            },
        ],
    )
    monkeypatch.setattr(executor_module, "get_ros_reader", lambda: fake_reader)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    result = manager.start(
        {
            "name": "监听 true 信号流程",
            "nodes": [
                _start(["wait_signal"]),
                _node("wait_signal", "topic_wait", params={"topicName": "/data_collection/start"}, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert fake_reader.read_after_calls[0][1] == 7
    assert fake_reader.read_after_calls[1][1] == 8
    assert run["status"] == "completed"
    assert run["taskStatus"]["status"] == "completed"
    assert run["taskStatus"]["data"]["sequence"] == 9
    assert run["taskStatus"]["data"]["data"] == {"data": True}


def test_external_navigation_stop_fails_state_machine(monkeypatch):
    fake_navigation = FakeNavigationManager(
        [
            {
                "ok": True,
                "code": "NAV-STATUS",
                "status": "stopped",
                "phase": "stopped",
                "detail": "Navigation interrupted by manual chassis control.",
            }
        ]
    )
    monkeypatch.setattr(executor_module, "get_navigation_manager", lambda: fake_navigation)
    manager = StateMachineExecutor(poll_interval_sec=0.01)

    manager.start(
        {
            "name": "外部打断",
            "nodes": [
                _start(["nav"]),
                _node("nav", "navigation", params={"mode": "lateral", "x": 1, "y": 0, "yawDeg": 0}, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    run = _wait_terminal(manager)

    assert run["status"] == "failed"
    assert run["currentId"] == "nav"
    assert "manual chassis control" in run["error"]
    assert run["taskStatus"]["status"] == "failed"


def test_state_machine_stop_stops_current_navigation(monkeypatch):
    fake_navigation = FakeNavigationManager(
        [
            {
                "ok": True,
                "code": "NAV-STATUS",
                "status": "running",
                "phase": "lateral_translate",
                "detail": "Navigation running.",
            }
        ]
    )
    monkeypatch.setattr(executor_module, "get_navigation_manager", lambda: fake_navigation)
    manager = StateMachineExecutor(poll_interval_sec=0.01)
    manager.start(
        {
            "name": "停止流程",
            "nodes": [
                _start(["nav"]),
                _node("nav", "navigation", params={"mode": "lateral", "x": 1, "y": 0, "yawDeg": 0}, outgoing=["sm_end"]),
                _end(),
            ],
        }
    )
    deadline = time.time() + 1.0
    while time.time() < deadline and not fake_navigation.started:
        time.sleep(0.01)

    stop_result = manager.stop()
    run = stop_result["run"]

    assert fake_navigation.started
    assert fake_navigation.stopped
    assert run["status"] == "stopped"
    assert run["active"] is False
