import math

import pytest

from modules.navigation import manager as navigation_manager
from modules.navigation.manager import (
    PHASE_FORWARD_TRANSLATE,
    PHASE_LATERAL_TRANSLATE,
    PHASE_OMNI_TRANSLATE,
    PHASE_ROTATE,
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


def test_rotate_phase_completes_within_tolerances(monkeypatch):
    manager = _manager(monkeypatch)
    target, params = manager._command_from_payload({"mode": "omni", "x": 1.0, "y": 1.0, "yawDeg": 3})

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
