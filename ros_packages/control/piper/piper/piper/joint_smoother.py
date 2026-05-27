import math
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple


JOINT_COUNT = 6
POSITION_COUNT = 7
DEFAULT_MAX_JOINT_SPEED_DEG_S = 5.0
MIN_MAX_JOINT_SPEED_DEG_S = 0.1
MAX_MAX_JOINT_SPEED_DEG_S = 180.0
DEFAULT_JOINT_NAMES = tuple(f"joint{index}" for index in range(POSITION_COUNT))
ZERO_VECTOR = (0.0,) * POSITION_COUNT


@dataclass(frozen=True)
class JointTarget:
    positions: Tuple[float, ...]
    names: Tuple[str, ...] = DEFAULT_JOINT_NAMES
    velocity: Tuple[float, ...] = ZERO_VECTOR
    effort: Tuple[float, ...] = ZERO_VECTOR
    max_joint_speed_deg_s: float = DEFAULT_MAX_JOINT_SPEED_DEG_S


@dataclass(frozen=True)
class SmootherOutput:
    positions: Tuple[float, ...]
    names: Tuple[str, ...] = DEFAULT_JOINT_NAMES
    velocity: Tuple[float, ...] = ZERO_VECTOR
    effort: Tuple[float, ...] = ZERO_VECTOR
    reached: bool = False
    holding: bool = False


def _number(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number.") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{field} must be a finite number.")
    return parsed


def normalize_positions(values, field="positions"):
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field} must contain exactly {POSITION_COUNT} numbers.")
    parsed = tuple(_number(value, f"{field}[{index}]") for index, value in enumerate(values))
    if len(parsed) != POSITION_COUNT:
        raise ValueError(f"{field} must contain exactly {POSITION_COUNT} numbers.")
    return parsed


def normalize_names(values):
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or len(values) != POSITION_COUNT:
        return DEFAULT_JOINT_NAMES
    return tuple(str(value) for value in values)


def normalize_vector(values, fill=0.0):
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        return (float(fill),) * POSITION_COUNT
    parsed = []
    for index in range(POSITION_COUNT):
        if index >= len(values):
            parsed.append(float(fill))
            continue
        try:
            value = _number(values[index], f"vector[{index}]")
        except ValueError:
            value = float(fill)
        parsed.append(value)
    return tuple(parsed)


def clamp_speed_deg_s(
    value,
    default=DEFAULT_MAX_JOINT_SPEED_DEG_S,
    minimum=MIN_MAX_JOINT_SPEED_DEG_S,
    maximum=MAX_MAX_JOINT_SPEED_DEG_S,
):
    try:
        speed = _number(value, "max_joint_speed_deg_s")
    except ValueError:
        speed = float(default)
    return max(float(minimum), min(float(maximum), speed))


def speed_from_velocity(velocity, default=DEFAULT_MAX_JOINT_SPEED_DEG_S):
    if isinstance(velocity, (str, bytes)) or not isinstance(velocity, Sequence):
        return clamp_speed_deg_s(default)
    for value in velocity[:JOINT_COUNT]:
        try:
            speed = _number(value, "velocity")
        except ValueError:
            continue
        if speed > 0:
            return clamp_speed_deg_s(speed)
    return clamp_speed_deg_s(default)


def step_scalar(current, target, max_step):
    current = _number(current, "current")
    target = _number(target, "target")
    max_step = max(0.0, _number(max_step, "max_step"))
    delta = target - current
    if abs(delta) <= max_step:
        return target
    return current + math.copysign(max_step, delta)


def interpolate_positions(current, target, max_joint_step_rad, gripper_direct=True):
    current_positions = normalize_positions(current, "current")
    target_positions = normalize_positions(target, "target")
    max_joint_step_rad = max(0.0, _number(max_joint_step_rad, "max_joint_step_rad"))
    next_positions = []

    for index, (current_value, target_value) in enumerate(zip(current_positions, target_positions)):
        if index < JOINT_COUNT:
            next_positions.append(step_scalar(current_value, target_value, max_joint_step_rad))
        elif gripper_direct:
            next_positions.append(target_value)
        else:
            next_positions.append(step_scalar(current_value, target_value, max_joint_step_rad))

    reached = all(
        math.isclose(next_value, target_value, rel_tol=0.0, abs_tol=1e-12)
        for next_value, target_value in zip(next_positions, target_positions)
    )
    return tuple(next_positions), reached


class LatestTargetSmoother:
    def __init__(self, default_max_joint_speed_deg_s=DEFAULT_MAX_JOINT_SPEED_DEG_S):
        self.default_max_joint_speed_deg_s = clamp_speed_deg_s(default_max_joint_speed_deg_s)
        self.current_positions: Optional[Tuple[float, ...]] = None
        self.active_target: Optional[JointTarget] = None
        self.holding = False

    def update_feedback(self, positions):
        parsed = normalize_positions(positions, "feedback.position")
        if self.current_positions is None or (self.active_target is None and not self.holding):
            self.current_positions = parsed
        return self.current_positions

    def set_target(
        self,
        positions,
        max_joint_speed_deg_s=None,
        names: Optional[Iterable[str]] = None,
        velocity=None,
        effort=None,
    ):
        if max_joint_speed_deg_s is None:
            max_joint_speed_deg_s = self.default_max_joint_speed_deg_s
        self.active_target = JointTarget(
            positions=normalize_positions(positions, "target.position"),
            names=normalize_names(tuple(names or ())),
            velocity=normalize_vector(velocity),
            effort=normalize_vector(effort),
            max_joint_speed_deg_s=clamp_speed_deg_s(max_joint_speed_deg_s),
        )
        self.holding = False
        return self.current_positions is not None

    def hold(self):
        self.active_target = None
        self.holding = self.current_positions is not None
        return self.holding

    def tick(self, dt_sec):
        if self.current_positions is None:
            return None

        if self.active_target is None:
            if not self.holding:
                return None
            return SmootherOutput(positions=self.current_positions, reached=True, holding=True)

        target = self.active_target
        dt_sec = max(0.0, min(_number(dt_sec, "dt_sec"), 0.5))
        max_step_rad = math.radians(target.max_joint_speed_deg_s) * dt_sec
        next_positions, reached = interpolate_positions(
            self.current_positions,
            target.positions,
            max_step_rad,
            gripper_direct=True,
        )
        self.current_positions = next_positions
        if reached:
            self.active_target = None

        return SmootherOutput(
            positions=next_positions,
            names=target.names,
            velocity=target.velocity,
            effort=target.effort,
            reached=reached,
            holding=False,
        )
