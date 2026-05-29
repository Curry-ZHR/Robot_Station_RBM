import math
import os
import threading
import time

from modules.logger import get_logger
from modules.ros_io import get_ros_writer


DEFAULT_MAX_LINEAR_MPS = 0.20
DEFAULT_MAX_LATERAL_MPS = 0.15
DEFAULT_MAX_ANGULAR_RAD_S = 0.50
LOGGER = get_logger()
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


def _payload_trace_id(payload):
    for key in ("commandTraceId", "command_trace_id", "traceId", "trace_id"):
        value = payload.get(key)
        if value is not None:
            return str(value)
    return ""


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
    controller_start = time.perf_counter()
    try:
        payload = _as_payload_dict(payload)
        sequence = _payload_sequence(payload)
        trace_id = _payload_trace_id(payload)
        command, limits = _command_from_payload(payload)
    except ChassisControlValidationError as exc:
        return _result(False, "CHASSIS-C-PAYLOAD", str(exc), limits=_limits())

    LOGGER.info(
        "CHASSIS_DEBUG controller.received trace=%s seq=%s command=(%.4f, %.4f, %.4f) t=%.6f",
        trace_id,
        sequence,
        command["linearX"],
        command["linearY"],
        command["angularZ"],
        controller_start,
    )

    accepted, latest_sequence = _accept_sequence(sequence)
    if not accepted:
        LOGGER.info(
            "CHASSIS_DEBUG controller.stale trace=%s seq=%s latest_seq=%s elapsed_ms=%.3f",
            trace_id,
            sequence,
            latest_sequence,
            (time.perf_counter() - controller_start) * 1000.0,
        )
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
            debugTiming={
                "controllerElapsedMs": round((time.perf_counter() - controller_start) * 1000.0, 3),
            },
            publishedAt=time.strftime("%H:%M:%S"),
        )

    writer_start = time.perf_counter()
    result = writer.publish(
        "chassis_cmd_vel",
        {
            "linearX": command["linearX"],
            "linearY": command["linearY"],
            "angularZ": command["angularZ"],
            "commandTraceId": trace_id,
            "commandSequence": sequence,
        },
    )
    writer_elapsed_ms = (time.perf_counter() - writer_start) * 1000.0
    controller_elapsed_ms = (time.perf_counter() - controller_start) * 1000.0
    ok = bool(result.get("ok"))
    LOGGER.info(
        "CHASSIS_DEBUG controller.writer_done trace=%s seq=%s ok=%s writer_elapsed_ms=%.3f controller_elapsed_ms=%.3f",
        trace_id,
        sequence,
        ok,
        writer_elapsed_ms,
        controller_elapsed_ms,
    )
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
        commandTraceId=trace_id,
        debugTiming={
            "controllerElapsedMs": round(controller_elapsed_ms, 3),
            "controllerToWriterElapsedMs": round(writer_elapsed_ms, 3),
        },
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
