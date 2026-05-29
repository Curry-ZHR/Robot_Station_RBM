import math
import os
import threading
import time

from modules.ros_io import get_ros_writer


DEFAULT_MAX_LINEAR_MPS = 0.20
DEFAULT_MAX_LATERAL_MPS = 0.15
DEFAULT_MAX_ANGULAR_RAD_S = 0.50
_command_sequence_lock = threading.Lock()
_latest_command_sequence = None


class ChassisControlValidationError(ValueError):
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
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ChassisControlValidationError("Payload must be a JSON object.")
    return payload


def _number(value, field, default=0.0):
    if value is None:
        value = default
    if isinstance(value, bool):
        raise ChassisControlValidationError(f"{field} must be a number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ChassisControlValidationError(f"{field} must be a number.") from exc
    if not math.isfinite(parsed):
        raise ChassisControlValidationError(f"{field} must be a finite number.")
    return parsed


def _limit_from_env(name, default):
    try:
        return abs(_number(os.environ.get(name), name, default=default))
    except ChassisControlValidationError:
        return default


def _limits():
    return {
        "maxLinearMps": _limit_from_env("CHASSIS_MAX_LINEAR_MPS", DEFAULT_MAX_LINEAR_MPS),
        "maxLateralMps": _limit_from_env("CHASSIS_MAX_LATERAL_MPS", DEFAULT_MAX_LATERAL_MPS),
        "maxAngularRadS": _limit_from_env("CHASSIS_MAX_ANGULAR_RAD_S", DEFAULT_MAX_ANGULAR_RAD_S),
    }


def _payload_number(payload, keys, field, default=0.0):
    for key in keys:
        if key in payload:
            return _number(payload[key], field)
    return _number(default, field)


def _payload_sequence(payload):
    for key in ("commandSequence", "command_sequence", "sequence"):
        if key in payload:
            sequence = _number(payload[key], key)
            if sequence < 0:
                raise ChassisControlValidationError(f"{key} must be >= 0.")
            return int(sequence)
    return None


def _accept_sequence(sequence):
    global _latest_command_sequence
    if sequence is None:
        return True, _latest_command_sequence
    with _command_sequence_lock:
        if _latest_command_sequence is not None and sequence < _latest_command_sequence:
            return False, _latest_command_sequence
        _latest_command_sequence = sequence
        return True, _latest_command_sequence


def _validate_command(command):
    limits = _limits()
    checks = (
        ("linearX", command["linearX"], limits["maxLinearMps"], "m/s"),
        ("linearY", command["linearY"], limits["maxLateralMps"], "m/s"),
        ("angularZ", command["angularZ"], limits["maxAngularRadS"], "rad/s"),
    )
    for field, value, limit, unit in checks:
        if abs(value) > limit:
            raise ChassisControlValidationError(f"{field} must be within +/-{limit:g} {unit}.")
    return limits


def _command_from_payload(payload):
    payload = _as_payload_dict(payload)
    command = {
        "linearX": _payload_number(payload, ("linearX", "linear_x", "x", "forward"), "linearX"),
        "linearY": _payload_number(payload, ("linearY", "linear_y", "y", "lateral"), "linearY"),
        "angularZ": _payload_number(payload, ("angularZ", "angular_z", "yawRate", "angularVelocity"), "angularZ"),
    }
    limits = _validate_command(command)
    return command, limits


def _motion_mode(command):
    if abs(command["linearY"]) > 1e-6:
        return "parallel"
    if abs(command["linearX"]) < 1e-6 and abs(command["angularZ"]) > 1e-6:
        return "spinning"
    return "dual_ackerman"


def publish_chassis_velocity(payload, writer=None):
    writer = writer or get_ros_writer()
    try:
        payload = _as_payload_dict(payload)
        sequence = _payload_sequence(payload)
        command, limits = _command_from_payload(payload)
    except ChassisControlValidationError as exc:
        return _result(False, "CHASSIS-C-PAYLOAD", str(exc), limits=_limits())

    accepted, latest_sequence = _accept_sequence(sequence)
    if not accepted:
        return _result(
            True,
            "CHASSIS-C-STALE",
            "Skipped stale chassis velocity command.",
            command=command,
            motionMode=_motion_mode(command),
            limits=limits,
            stale=True,
            commandSequence=sequence,
            latestCommandSequence=latest_sequence,
            publishedAt=time.strftime("%H:%M:%S"),
        )

    result = writer.publish(
        "chassis_cmd_vel",
        {
            "linearX": command["linearX"],
            "linearY": command["linearY"],
            "angularZ": command["angularZ"],
        },
    )
    ok = bool(result.get("ok"))
    return _result(
        ok,
        "CHASSIS-C-PUBLISHED" if ok else "CHASSIS-C-UNAVAILABLE",
        "Published chassis velocity command." if ok else result.get("detail", "Failed to publish chassis command."),
        command=command,
        motionMode=_motion_mode(command),
        limits=limits,
        topic=result.get("topic"),
        writer=result,
        commandSequence=sequence,
        publishedAt=time.strftime("%H:%M:%S"),
    )


def stop_chassis(payload=None, writer=None):
    try:
        payload = _as_payload_dict(payload)
    except ChassisControlValidationError as exc:
        return _result(False, "CHASSIS-C-PAYLOAD", str(exc), limits=_limits())
    return publish_chassis_velocity(
        {
            **payload,
            "linearX": 0.0,
            "linearY": 0.0,
            "angularZ": 0.0,
        },
        writer=writer,
    )


def chassis_limits():
    return _result(True, "CHASSIS-C-LIMITS", "Chassis velocity limits loaded.", limits=_limits())
