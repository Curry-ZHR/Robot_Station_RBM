import math
import time

import pytest

from modules.navigation import manager as navigation_manager
from modules.navigation.manager import (
    PHASE_FORWARD_TRANSLATE,
    PHASE_LATERAL_TRANSLATE,
    PHASE_OMNI_TRANSLATE,
    PHASE_ROTATE,
    PHASE_WAITING_LOCALIZATION,
    NavigationManager,
)


def _pose(x=0.0, y=0.0, yaw=0.0, age_ms=0):
    return {
        "x": x,
        "y": y,
        "z": 0.0,
        "yawRad": yaw,
        "yawDeg": math.degrees(yaw),
        "frameId": "map",
        "ageMs": age_ms,
    }


def _pose_result(x=0.0, y=0.0, yaw=0.0, age_ms=0):
    return {
        "ok": True,
        "stale": False,
        "ageMs": age_ms,
        "data": {
            "header": {"frame_id": "map"},
            "pose": {
                "position": {"x": x, "y": y, "z": 0.0},
                "orientation": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": math.sin(yaw / 2.0),
                    "w": math.cos(yaw / 2.0),
                },
            },
        },
    }


def _state(manager, target, params, phase, translation_yaw=0.0):
    state = manager._base_state()
    state.update(
        {
            "target": target,
            "params": params,
            "phase": phase,
            "translationYawRad": translation_yaw,
        }
    )
    return state


def _manager(monkeypatch):
    monkeypatch.setattr(
        navigation_manager,
        "chassis_limits",
        lambda: {"limits": {"maxLinearMps": 0.2, "maxLateralMps": 0.15, "maxAngularRadS": 0.5}},
    )
    return NavigationManager(reader=None, publisher=lambda command: {"ok": True, "command": command})


def test_navigation_payload_requires_full_goal(monkeypatch):
    manager = _manager(monkeypatch)

    missing_mode = manager.start({"x": 1.0, "y": 2.0, "yawDeg": 0})
    missing_yaw = manager.start({"mode": "lateral", "x": 1.0, "y": 2.0})

    assert missing_mode["code"] == "NAV-PAYLOAD"
    assert "mode" in missing_mode["detail"]
    assert missing_yaw["code"] == "NAV-PAYLOAD"
    assert "yawDeg or yawRad" in missing_yaw["detail"]


def test_lateral_mode_clears_body_y_then_body_x_then_yaw(monkeypatch):
    manager = _manager(monkeypatch)
    target, params = manager._command_from_payload({"mode": "lateral", "x": 1.0, "y": 1.0, "yawDeg": 90})

    command, phase, errors, done = manager._next_command(
        _state(manager, target, params, PHASE_LATERAL_TRANSLATE),
        target,
        params,
        _pose(0.0, 0.0, 0.0),
    )
    assert not done
    assert phase == PHASE_LATERAL_TRANSLATE
    assert command["linearX"] == 0.0
    assert command["linearY"] > 0.0
    assert command["angularZ"] == 0.0
    assert errors["bodyY"] == pytest.approx(1.0)

    command, phase, errors, done = manager._next_command(
        _state(manager, target, params, PHASE_LATERAL_TRANSLATE),
        target,
        params,
        _pose(0.0, 1.0, 0.0),
    )
    assert not done
    assert phase == PHASE_FORWARD_TRANSLATE
    assert command["linearX"] > 0.0
    assert command["linearY"] == 0.0

    command, phase, errors, done = manager._next_command(
        _state(manager, target, params, PHASE_FORWARD_TRANSLATE),
        target,
        params,
        _pose(1.0, 1.0, 0.0),
    )
    assert not done
    assert phase == PHASE_ROTATE
    assert command["linearX"] == 0.0
    assert command["linearY"] == 0.0
    assert command["angularZ"] > 0.0


def test_omni_mode_commands_diagonal_crab(monkeypatch):
    manager = _manager(monkeypatch)
    target, params = manager._command_from_payload({"mode": "omni", "x": 1.0, "y": 1.0, "yawDeg": 0})

    command, phase, errors, done = manager._next_command(
        _state(manager, target, params, PHASE_OMNI_TRANSLATE),
        target,
        params,
        _pose(0.0, 0.0, 0.0),
    )

    assert not done
    assert phase == PHASE_OMNI_TRANSLATE
    assert command["linearX"] > 0.0
    assert command["linearY"] > 0.0
    assert abs(command["linearX"]) <= params["maxLinearMps"]
    assert abs(command["linearY"]) <= params["maxLateralMps"]
    assert errors["distance"] == pytest.approx(math.sqrt(2.0))


def test_omni_mode_zeroes_tiny_linear_x_when_lateral_dominates(monkeypatch):
    manager = _manager(monkeypatch)
    target, params = manager._command_from_payload({"mode": "omni", "x": -0.033, "y": -1.0, "yawDeg": 0})

    command, phase, errors, done = manager._next_command(
        _state(manager, target, params, PHASE_OMNI_TRANSLATE),
        target,
        params,
        _pose(0.0, 0.0, 0.0),
    )

    assert not done
    assert phase == PHASE_OMNI_TRANSLATE
    assert command["linearX"] == 0.0
    assert command["linearY"] < 0.0
    assert abs(command["linearY"]) == pytest.approx(params["maxLateralMps"])
    assert abs(errors["bodyX"]) < params["lateralDominantLinearDeadbandMps"]


def test_omni_near_target_uses_single_axis_when_axis_errors_inside_tolerance_but_distance_outside(monkeypatch):
    manager = _manager(monkeypatch)
    target, params = manager._command_from_payload({"mode": "omni", "x": 0.04, "y": 0.04, "yawDeg": 0})

    command, phase, errors, done = manager._next_command(
        _state(manager, target, params, PHASE_OMNI_TRANSLATE),
        target,
        params,
        _pose(0.0, 0.0, 0.0),
    )

    assert not done
    assert phase == PHASE_OMNI_TRANSLATE
    assert abs(errors["bodyX"]) <= params["positionToleranceM"]
    assert abs(errors["bodyY"]) <= params["positionToleranceM"]
    assert errors["distance"] > params["positionToleranceM"]
    assert errors["nearTarget"] is True
    assert command["linearX"] > 0.0
    assert command["linearY"] == 0.0


def test_omni_near_target_deadbands_small_lateral_error_when_forward_can_finish(monkeypatch):
    manager = _manager(monkeypatch)
    target, params = manager._command_from_payload({"mode": "omni", "x": 0.10, "y": 0.03, "yawDeg": 0})

    command, phase, errors, done = manager._next_command(
        _state(manager, target, params, PHASE_OMNI_TRANSLATE),
        target,
        params,
        _pose(0.0, 0.0, 0.0),
    )

    assert not done
    assert phase == PHASE_OMNI_TRANSLATE
    assert errors["nearTarget"] is True
    assert command["linearX"] > 0.0
    assert command["linearY"] == 0.0
    assert errors["lateralControlActive"] is False


def test_rotate_phase_completes_within_tolerances(monkeypatch):
    manager = _manager(monkeypatch)
    target, params = manager._command_from_payload({"mode": "omni", "x": 1.0, "y": 1.0, "yawDeg": 3, "arrivalStableSec": 0})

    command, phase, errors, done = manager._next_command(
        _state(manager, target, params, PHASE_ROTATE),
        target,
        params,
        _pose(1.0, 1.0, math.radians(1.0)),
    )

    assert done
    assert phase == "completed"
    assert command == {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0}
    assert abs(errors["yawDeg"]) <= params["yawToleranceDeg"]


def test_rotate_phase_waits_for_stable_arrival_by_default(monkeypatch):
    manager = _manager(monkeypatch)
    target, params = manager._command_from_payload({"mode": "omni", "x": 1.0, "y": 1.0, "yawDeg": 3})
    state = _state(manager, target, params, PHASE_ROTATE)

    command, phase, errors, done = manager._next_command(
        state,
        target,
        params,
        _pose(1.0, 1.0, math.radians(1.0)),
    )

    assert not done
    assert phase == PHASE_ROTATE
    assert command == {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0}
    assert state["arrival"]["stableSince"] is not None
    assert errors["arrivalStableElapsedSec"] < params["arrivalStableSec"]

    state["arrival"]["stableSince"] = time.monotonic() - params["arrivalStableSec"] - 0.01
    command, phase, errors, done = manager._next_command(
        state,
        target,
        params,
        _pose(0.93, 1.0, math.radians(1.0)),
    )

    assert done
    assert phase == "completed"
    assert command == {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0}
    assert errors["positionWithinTolerance"] is False
    assert errors["positionWithinHoldBand"] is True


def test_rotate_phase_replans_when_position_leaves_hold_band(monkeypatch):
    manager = _manager(monkeypatch)
    target, params = manager._command_from_payload({"mode": "omni", "x": 1.0, "y": 1.0, "yawDeg": 0})

    command, phase, errors, done = manager._next_command(
        _state(manager, target, params, PHASE_ROTATE),
        target,
        params,
        _pose(0.92, 1.0, 0.0),
    )

    assert not done
    assert phase == PHASE_OMNI_TRANSLATE
    assert errors["positionWithinHoldBand"] is False
    assert command["linearX"] > 0.0
    assert command["linearY"] == 0.0


def test_start_rejects_stale_localization(monkeypatch):
    class FakeReader:
        def read(self, key, timeout_sec=0.0):
            return {
                "ok": True,
                "stale": True,
                "detail": "stale pose",
                "data": {},
            }

    manager = NavigationManager(reader=FakeReader(), publisher=lambda command: {"ok": True, "command": command})
    monkeypatch.setattr(
        navigation_manager,
        "chassis_limits",
        lambda: {"limits": {"maxLinearMps": 0.2, "maxLateralMps": 0.15, "maxAngularRadS": 0.5}},
    )

    result = manager.start({"mode": "lateral", "x": 1.0, "y": 0.0, "yawDeg": 0})

    assert result["code"] == "NAV-LOCALIZATION"
    assert result["status"] == "failed"


def test_running_navigation_waits_for_localization_pose_and_resumes(monkeypatch):
    class FakeReader:
        def __init__(self):
            self.calls = 0
            self.recovered = False

        def read(self, key, timeout_sec=0.0):
            self.calls += 1
            if self.calls == 1:
                return _pose_result(0.0, 0.0, 0.0)
            if not self.recovered:
                return {
                    "ok": False,
                    "code": "ROS-R-NODATA",
                    "detail": "No message received from /localization/pose.",
                }
            return _pose_result(0.0, 0.0, 0.0)

    monkeypatch.setattr(
        navigation_manager,
        "chassis_limits",
        lambda: {"limits": {"maxLinearMps": 0.2, "maxLateralMps": 0.15, "maxAngularRadS": 0.5}},
    )
    reader = FakeReader()
    commands = []

    def publish(command):
        commands.append(command)
        return {"ok": True, "command": command}

    manager = NavigationManager(reader=reader, publisher=publish)
    result = manager.start(
        {
            "mode": "lateral",
            "x": 0.0,
            "y": 0.0,
            "yawDeg": 0,
            "arrivalStableSec": 0,
            "controlRateHz": 50,
        }
    )
    assert result["ok"] is True

    deadline = time.time() + 1.0
    status = manager.status()
    while time.time() < deadline and status.get("phase") != PHASE_WAITING_LOCALIZATION:
        time.sleep(0.01)
        status = manager.status()

    assert status["status"] == "running"
    assert status["phase"] == PHASE_WAITING_LOCALIZATION
    assert status["running"] is True
    assert status["command"] == {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0}
    assert "No message" in status["lastLocalizationError"]
    assert commands[-1] == {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0}

    reader.recovered = True
    deadline = time.time() + 1.0
    status = manager.status()
    while time.time() < deadline and status.get("status") not in {"completed", "failed", "stopped"}:
        time.sleep(0.01)
        status = manager.status()

    assert status["status"] == "completed"
    assert status["lastLocalizationError"] == ""
