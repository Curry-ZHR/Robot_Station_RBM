"""Action chunk schema parsing and safety validation for remote inference.

The remote inference machine returns absolute joint targets per arm plus an
optional lift height and chassis velocity. Every value is validated against
explicit joint/gripper/lift/chassis limits before it is ever turned into a ROS
command, so an out-of-range or malformed response can never reach the robot.
"""

import math
import os

from modules.control.chassis import chassis_limits
from modules.control.lifting import lifting_limits


JOINT_NAMES = ("joint1", "joint2", "joint3", "joint4", "joint5", "joint6")
GRIPPER_NAME = "gripper"
SIDES = ("left", "right")

# Base per-joint limits in radians, derived from the Piper description URDF.
BASE_JOINT_LIMITS = {
    "joint1": (-2.618, 2.618),
    "joint2": (0.0, 3.14),
    "joint3": (-2.697, 0.0),
    "joint4": (-1.832, 1.832),
    "joint5": (-1.22, 1.22),
    "joint6": (-3.14, 3.14),
}

# Side specific joint1 caps mirror modules.control.piper.controller so the two
# arms cannot swing into each other.
LEFT_J1_MAX_RAD = math.radians(25.0)
RIGHT_J1_MIN_RAD = math.radians(-25.0)


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return float(default)


GRIPPER_MIN_M = _env_float("INFERENCE_GRIPPER_MIN_M", 0.0)
GRIPPER_MAX_M = _env_float("INFERENCE_GRIPPER_MAX_M", 0.1)

DEFAULT_MAX_CHUNK_STEPS = int(_env_float("INFERENCE_MAX_CHUNK_STEPS", 200))


class ActionChunkValidationError(ValueError):
    """Raised when a remote action chunk fails schema or limit validation."""


def side_joint_limits(side):
    limits = dict(BASE_JOINT_LIMITS)
    j1_low, j1_high = limits["joint1"]
    if side == "left":
        j1_high = min(j1_high, LEFT_J1_MAX_RAD)
    elif side == "right":
        j1_low = max(j1_low, RIGHT_J1_MIN_RAD)
    limits["joint1"] = (j1_low, j1_high)
    return limits


def _finite_number(value, field):
    if isinstance(value, bool):
        raise ActionChunkValidationError(f"{field} must be a number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ActionChunkValidationError(f"{field} must be a number.") from exc
    if not math.isfinite(parsed):
        raise ActionChunkValidationError(f"{field} must be a finite number.")
    return parsed


def _clip(value, field, low, high, clips):
    """Clamp an out-of-range value to the limit instead of rejecting it.

    A non-finite or non-numeric value still raises, because it cannot be
    meaningfully clipped. Any clamp is recorded in ``clips`` for reporting.
    """
    parsed = _finite_number(value, field)
    clamped = max(low, min(high, parsed))
    if clamped != parsed:
        clips.append(field)
    return clamped


def _arm_positions(side_payload, side, step_index, clips):
    if not isinstance(side_payload, dict):
        raise ActionChunkValidationError(f"actions[{step_index}].{side} must be an object.")
    limits = side_joint_limits(side)
    positions = []
    for name in JOINT_NAMES:
        if name not in side_payload:
            raise ActionChunkValidationError(
                f"actions[{step_index}].{side}.{name} is required."
            )
        low, high = limits[name]
        positions.append(_clip(side_payload[name], f"actions[{step_index}].{side}.{name}", low, high, clips))
    if GRIPPER_NAME not in side_payload:
        raise ActionChunkValidationError(
            f"actions[{step_index}].{side}.{GRIPPER_NAME} is required."
        )
    positions.append(
        _clip(
            side_payload[GRIPPER_NAME],
            f"actions[{step_index}].{side}.{GRIPPER_NAME}",
            GRIPPER_MIN_M,
            GRIPPER_MAX_M,
            clips,
        )
    )
    return positions


def _lift_height(action, step_index, clips):
    lift = action.get("lift")
    if lift is None:
        return None
    if not isinstance(lift, dict) or "height" not in lift:
        raise ActionChunkValidationError(f"actions[{step_index}].lift must contain a height.")
    limits = lifting_limits().get("limits", {})
    low = float(limits.get("minHeightM", 0.0))
    high = float(limits.get("maxHeightM", 0.8))
    return _clip(lift["height"], f"actions[{step_index}].lift.height", low, high, clips)


def _limit_override(override, keys, hard):
    """Return a user supplied velocity cap, never exceeding the hardware ceiling."""
    for key in keys:
        if key in override:
            try:
                value = abs(float(override[key]))
            except (TypeError, ValueError):
                return hard
            if not math.isfinite(value):
                return hard
            return min(value, hard)
    return hard


def effective_chassis_limits(override=None):
    """Resolve the chassis velocity caps used for validation.

    The hardware limits (from chassis_limits / env) are the hard ceiling; an
    operator supplied override can only make them stricter, never looser.
    """
    hard = chassis_limits().get("limits", {})
    max_linear = float(hard.get("maxLinearMps", 0.2))
    max_lateral = float(hard.get("maxLateralMps", 0.15))
    max_angular = float(hard.get("maxAngularRadS", 0.5))
    if isinstance(override, dict):
        max_linear = _limit_override(override, ("maxLinearMps", "maxVx", "vx"), max_linear)
        max_lateral = _limit_override(override, ("maxLateralMps", "maxVy", "vy"), max_lateral)
        max_angular = _limit_override(override, ("maxAngularRadS", "maxWz", "wz"), max_angular)
    return {"maxLinearMps": max_linear, "maxLateralMps": max_lateral, "maxAngularRadS": max_angular}


def _chassis_velocity(action, step_index, limits, clips):
    speed = action.get("speed")
    if speed is None:
        return 0.0, 0.0, 0.0
    if not isinstance(speed, dict):
        raise ActionChunkValidationError(f"actions[{step_index}].speed must be an object.")
    # Velocity caps are symmetric: a cap of c means the value is clipped to [-c, c].
    vx = _clip(speed.get("vx", 0.0), f"actions[{step_index}].speed.vx", -limits["maxLinearMps"], limits["maxLinearMps"], clips)
    vy = _clip(speed.get("vy", 0.0), f"actions[{step_index}].speed.vy", -limits["maxLateralMps"], limits["maxLateralMps"], clips)
    wz = _clip(speed.get("wz", 0.0), f"actions[{step_index}].speed.wz", -limits["maxAngularRadS"], limits["maxAngularRadS"], clips)
    return vx, vy, wz


def validate_action_chunk(message, max_steps=DEFAULT_MAX_CHUNK_STEPS, chassis_limits_override=None):
    """Validate a remote action_chunk message and return a normalized chunk.

    The normalized chunk is a dict with ``steps`` where each step is
    ``{"left": [7], "right": [7], "lift_height": float|None,
    "speed": (vx, vy, wz)}`` ready for the executor. Chassis velocity is
    validated against the operator supplied caps (bounded by the hardware
    limits).
    """

    if not isinstance(message, dict):
        raise ActionChunkValidationError("Action chunk must be a JSON object.")
    if message.get("type") != "action_chunk":
        raise ActionChunkValidationError("Message type must be 'action_chunk'.")

    actions = message.get("actions")
    if not isinstance(actions, list) or not actions:
        raise ActionChunkValidationError("actions must be a non-empty list.")
    if len(actions) > max_steps:
        raise ActionChunkValidationError(
            f"actions has {len(actions)} steps, exceeding the max of {max_steps}."
        )

    chassis_lim = effective_chassis_limits(chassis_limits_override)
    clips = []
    steps = []
    for step_index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise ActionChunkValidationError(f"actions[{step_index}] must be an object.")
        step = {
            "left": _arm_positions(action.get("left"), "left", step_index, clips),
            "right": _arm_positions(action.get("right"), "right", step_index, clips),
            "lift_height": _lift_height(action, step_index, clips),
            "speed": _chassis_velocity(action, step_index, chassis_lim, clips),
        }
        steps.append(step)

    return {
        "steps": steps,
        "stepCount": len(steps),
        "clipped": len(clips),
        "clippedFields": clips[:10],
    }
