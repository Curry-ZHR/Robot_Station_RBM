import math
import os
import time

from modules.ros_io import get_ros_writer


SIDES = ("left", "right")
SIDE_LABELS = {
    "left": "left",
    "right": "right",
}
JOINT_ACTION_KEYS = {
    "left": "piper_left_joint_double",
    "right": "piper_right_joint_double",
}
HOLD_ACTION_KEYS = {
    "left": "piper_left_joint_smoother_hold",
    "right": "piper_right_joint_smoother_hold",
}
DEFAULT_MAX_JOINT_SPEED_DEG_S = 5.0
MIN_MAX_JOINT_SPEED_DEG_S = 0.5
MAX_MAX_JOINT_SPEED_DEG_S = 30.0
DEFAULT_GRIPPER_EFFORT = 1.0
LEFT_J1_MAX_DEG = 25.0
RIGHT_J1_MIN_DEG = -25.0


class PiperControlValidationError(ValueError):
    pass


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def _as_payload_dict(payload):
    if not isinstance(payload, dict):
        raise PiperControlValidationError("Payload must be a JSON object.")
    return payload


def _number(value, field):
    if isinstance(value, bool):
        raise PiperControlValidationError(f"{field} must be a number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise PiperControlValidationError(f"{field} must be a number.") from exc
    if not math.isfinite(parsed):
        raise PiperControlValidationError(f"{field} must be a finite number.")
    return parsed


def _speed(value, field="max_joint_speed_deg_s"):
    parsed = _number(value, field)
    if parsed < MIN_MAX_JOINT_SPEED_DEG_S or parsed > MAX_MAX_JOINT_SPEED_DEG_S:
        raise PiperControlValidationError(
            f"{field} must be between {MIN_MAX_JOINT_SPEED_DEG_S} and {MAX_MAX_JOINT_SPEED_DEG_S} deg/s."
        )
    return parsed


def _clamped_number(value, field, default, minimum, maximum):
    try:
        parsed = _number(value, field)
    except PiperControlValidationError:
        parsed = float(default)
    return max(minimum, min(maximum, parsed))


def _positions(side_payload, side):
    if not isinstance(side_payload, dict):
        raise PiperControlValidationError(f"{SIDE_LABELS[side]} target must be a JSON object.")
    values = side_payload.get("positions")
    if not isinstance(values, (list, tuple)):
        raise PiperControlValidationError(f"{SIDE_LABELS[side]}.positions must be a list of 7 numbers.")
    parsed = [_number(value, f"{SIDE_LABELS[side]}.positions[{index}]") for index, value in enumerate(values)]
    if len(parsed) != 7:
        raise PiperControlValidationError(f"{SIDE_LABELS[side]}.positions must contain exactly 7 numbers.")
    _validate_side_joint_limits(parsed, side)
    return parsed


def _validate_side_joint_limits(positions, side):
    j1_deg = math.degrees(positions[0])
    if side == "left" and j1_deg > LEFT_J1_MAX_DEG:
        raise PiperControlValidationError(
            f"left.positions[0] must be <= {LEFT_J1_MAX_DEG:g} deg."
        )
    if side == "right" and j1_deg < RIGHT_J1_MIN_DEG:
        raise PiperControlValidationError(
            f"right.positions[0] must be >= {RIGHT_J1_MIN_DEG:g} deg."
        )


def _requested_sides(payload, require_targets):
    sides = [side for side in SIDES if side in payload]
    if sides:
        return sides
    if require_targets:
        raise PiperControlValidationError("At least one of left or right must be provided.")
    return list(SIDES)


def _bottom_speed_percent(payload):
    env_default = os.environ.get("PIPER_ACTION_SPEED_PERCENT", os.environ.get("PIPER_ACTION_SPEED", "10"))
    return _clamped_number(
        payload.get("joint_speed_percent", env_default),
        "joint_speed_percent",
        10,
        1,
        100,
    )


def _gripper_effort(payload):
    return _clamped_number(
        payload.get("gripper_effort", DEFAULT_GRIPPER_EFFORT),
        "gripper_effort",
        DEFAULT_GRIPPER_EFFORT,
        0.5,
        3.0,
    )


def _publish_hold(payload, writer):
    sides = _requested_sides(payload, require_targets=False)
    results = []
    for side in sides:
        result = writer.publish(HOLD_ACTION_KEYS[side], {"enabled": True})
        results.append({"side": side, **result})

    ok = all(result.get("ok") for result in results)
    return _result(
        ok,
        "PIPER-C-HOLD" if ok else "PIPER-C-UNAVAILABLE",
        "Piper joint smoother hold requested." if ok else "Failed to request Piper joint smoother hold.",
        results=results,
        publishedAt=time.strftime("%H:%M:%S"),
    )


def publish_joint_targets(payload, writer=None):
    writer = writer or get_ros_writer()
    try:
        payload = _as_payload_dict(payload)
        if payload.get("hold") is True or payload.get("stop") is True:
            return _publish_hold(payload, writer)

        sides = _requested_sides(payload, require_targets=True)
        default_speed = _speed(payload.get("max_joint_speed_deg_s", DEFAULT_MAX_JOINT_SPEED_DEG_S))
        bottom_speed = _bottom_speed_percent(payload)
        gripper_effort = _gripper_effort(payload)

        results = []
        for side in sides:
            side_payload = payload.get(side)
            positions = _positions(side_payload, side)
            side_speed = _speed(side_payload.get("max_joint_speed_deg_s", default_speed), f"{side}.max_joint_speed_deg_s")
            command_payload = {
                "positions": positions,
                "velocities": [side_speed] * 6 + [bottom_speed],
                "efforts": [0.0] * 6 + [gripper_effort],
            }
            result = writer.publish(JOINT_ACTION_KEYS[side], command_payload)
            results.append({"side": side, **result})
    except PiperControlValidationError as exc:
        return _result(False, "PIPER-C-PAYLOAD", str(exc))

    ok = all(result.get("ok") for result in results)
    topics = [result.get("topic") for result in results if result.get("topic")]
    return _result(
        ok,
        "PIPER-C-PUBLISHED" if ok else "PIPER-C-UNAVAILABLE",
        "Published Piper joint targets through smoother topics." if ok else "Failed to publish one or more Piper joint targets.",
        results=results,
        topics=topics,
        maxJointSpeedDegS=default_speed,
        jointSpeedPercent=bottom_speed,
        publishedAt=time.strftime("%H:%M:%S"),
    )
