import math

import pytest

from modules.inference.validation import (
    ActionChunkValidationError,
    LEFT_J1_MAX_RAD,
    RIGHT_J1_MIN_RAD,
    side_joint_limits,
    validate_action_chunk,
)


def _arm(**overrides):
    arm = {
        "joint1": 0.0,
        "joint2": 0.0,
        "joint3": 0.0,
        "joint4": 0.0,
        "joint5": 0.0,
        "joint6": 0.0,
        "gripper": 0.05,
    }
    arm.update(overrides)
    return arm


def _action(**overrides):
    action = {
        "left": _arm(),
        "right": _arm(),
        "lift": {"height": 0.4},
        "speed": {"vx": 0.0, "vy": 0.0, "wz": 0.0},
    }
    action.update(overrides)
    return action


def _chunk(actions=None, **overrides):
    message = {
        "type": "action_chunk",
        "chunk_id": "chunk_001",
        "actions": actions if actions is not None else [_action()],
    }
    message.update(overrides)
    return message


def test_valid_chunk_parses_into_steps():
    result = validate_action_chunk(_chunk())
    assert "chunk_id" not in result
    assert result["stepCount"] == 1
    step = result["steps"][0]
    assert len(step["left"]) == 7
    assert len(step["right"]) == 7
    assert step["lift_height"] == pytest.approx(0.4)
    assert step["speed"] == (0.0, 0.0, 0.0)


def test_missing_arm_field_rejected():
    arm = _arm()
    del arm["joint4"]
    with pytest.raises(ActionChunkValidationError):
        validate_action_chunk(_chunk([_action(left=arm)]))


def test_missing_gripper_rejected():
    arm = _arm()
    del arm["gripper"]
    with pytest.raises(ActionChunkValidationError):
        validate_action_chunk(_chunk([_action(right=arm)]))


def test_nan_value_rejected():
    with pytest.raises(ActionChunkValidationError):
        validate_action_chunk(_chunk([_action(left=_arm(joint2=float("nan")))]))


def test_out_of_limit_joint_clipped():
    # joint2 limit is [0, 3.14]; a negative value is clipped to 0, not rejected.
    result = validate_action_chunk(_chunk([_action(left=_arm(joint2=-1.0))]))
    assert result["steps"][0]["left"][1] == pytest.approx(0.0)
    assert result["clipped"] >= 1


def test_side_specific_j1_limits():
    left = side_joint_limits("left")
    right = side_joint_limits("right")
    assert left["joint1"][1] == pytest.approx(LEFT_J1_MAX_RAD)
    assert right["joint1"][0] == pytest.approx(RIGHT_J1_MIN_RAD)
    # Left arm joint1 is clipped down to the +25 deg cap.
    left_step = validate_action_chunk(_chunk([_action(left=_arm(joint1=math.radians(40)))]))["steps"][0]
    assert left_step["left"][0] == pytest.approx(LEFT_J1_MAX_RAD)
    # Right arm joint1 is clipped up to the -25 deg cap.
    right_step = validate_action_chunk(_chunk([_action(right=_arm(joint1=math.radians(-40)))]))["steps"][0]
    assert right_step["right"][0] == pytest.approx(RIGHT_J1_MIN_RAD)


def test_out_of_limit_lift_clipped():
    result = validate_action_chunk(_chunk([_action(lift={"height": 5.0})]))
    # Clipped to the upper height limit (>= 0) rather than rejected.
    assert result["steps"][0]["lift_height"] <= 0.8 + 1e-9
    assert result["clipped"] >= 1


def test_out_of_limit_speed_clipped():
    # vx beyond the cap is clipped to the positive limit (symmetric range).
    step = validate_action_chunk(_chunk([_action(speed={"vx": 10.0, "vy": 0.0, "wz": 0.0})]))["steps"][0]
    assert step["speed"][0] == pytest.approx(0.2)


def test_negative_speed_clipped_to_symmetric_limit():
    # A cap of c means the value is clipped to [-c, c]; -10 vx -> -0.2.
    step = validate_action_chunk(_chunk([_action(speed={"vx": -10.0, "vy": 0.0, "wz": 0.0})]))["steps"][0]
    assert step["speed"][0] == pytest.approx(-0.2)


def test_wz_passthrough_and_clip():
    # wz within the default hardware cap (0.5 rad/s) passes through unchanged.
    step = validate_action_chunk(_chunk([_action(speed={"vx": 0.1, "vy": 0.05, "wz": 0.3})]))["steps"][0]
    assert step["speed"] == pytest.approx((0.1, 0.05, 0.3))
    # wz beyond the cap is clipped to +/-0.5.
    step = validate_action_chunk(_chunk([_action(speed={"vx": 0.0, "vy": 0.0, "wz": 2.0})]))["steps"][0]
    assert step["speed"][2] == pytest.approx(0.5)


def test_chassis_limits_override_is_stricter():
    # An override below the hardware ceiling clips more aggressively.
    step = validate_action_chunk(
        _chunk([_action(speed={"vx": 0.1, "vy": 0.0, "wz": 0.0})]),
        chassis_limits_override={"maxLinearMps": 0.05},
    )["steps"][0]
    assert step["speed"][0] == pytest.approx(0.05)


def test_chassis_limits_override_cannot_exceed_hardware():
    # Requesting a looser cap than hardware still clips to the hardware ceiling.
    step = validate_action_chunk(
        _chunk([_action(speed={"vx": 0.5, "vy": 0.0, "wz": 0.0})]),
        chassis_limits_override={"maxLinearMps": 99.0},
    )["steps"][0]
    assert step["speed"][0] == pytest.approx(0.2)


def test_optional_lift_and_speed_default():
    action = _action()
    del action["lift"]
    del action["speed"]
    step = validate_action_chunk(_chunk([action]))["steps"][0]
    assert step["lift_height"] is None
    assert step["speed"] == (0.0, 0.0, 0.0)


def test_empty_actions_rejected():
    with pytest.raises(ActionChunkValidationError):
        validate_action_chunk(_chunk([]))


def test_wrong_type_rejected():
    with pytest.raises(ActionChunkValidationError):
        validate_action_chunk({"type": "observation", "actions": [_action()]})


def test_too_many_steps_rejected():
    with pytest.raises(ActionChunkValidationError):
        validate_action_chunk(_chunk([_action(), _action(), _action()]), max_steps=2)
