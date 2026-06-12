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
