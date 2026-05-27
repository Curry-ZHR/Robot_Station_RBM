JOINT_NAMES = ["joint0", "joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]


class CommandValidationError(ValueError):
    pass


def _as_payload_dict(payload):
    if not isinstance(payload, dict):
        raise CommandValidationError("Payload must be a JSON object.")
    return payload


def _number(value, field):
    if isinstance(value, bool):
        raise CommandValidationError(f"{field} must be a number.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise CommandValidationError(f"{field} must be a number.") from exc


def _int_number(value, field):
    if isinstance(value, bool):
        raise CommandValidationError(f"{field} must be an integer.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise CommandValidationError(f"{field} must be an integer.") from exc


def _number_list(values, field, expected_len=None):
    if not isinstance(values, (list, tuple)):
        raise CommandValidationError(f"{field} must be a list of numbers.")
    parsed = [_number(value, f"{field}[{index}]") for index, value in enumerate(values)]
    if expected_len is not None and len(parsed) != expected_len:
        raise CommandValidationError(f"{field} must contain exactly {expected_len} numbers.")
    return parsed


def _optional_number_list(payload, keys, field, expected_len, default=None):
    for key in keys:
        if key in payload:
            return _number_list(payload[key], field, expected_len)
    if default is None:
        return None
    return list(default)


def build_joint_state_command(payload, message_class, stamp=None):
    payload = _as_payload_dict(payload)
    positions = None
    for key in ("positions", "position", "joints"):
        if key in payload:
            positions = _number_list(payload[key], key)
            break
    if positions is None:
        raise CommandValidationError("Joint command requires positions, position, or joints.")

    if len(positions) == 6 and "gripper" in payload:
        positions.append(_number(payload["gripper"], "gripper"))
    if len(positions) != 7:
        raise CommandValidationError("Joint command must provide 7 values, including gripper.")

    velocities = _optional_number_list(
        payload,
        ("velocities", "velocity"),
        "velocities",
        7,
        default=[0.0] * 7,
    )
    if "speed" in payload:
        speed = _number(payload["speed"], "speed")
        velocities = [0.0] * 7
        velocities[6] = speed

    efforts = _optional_number_list(
        payload,
        ("efforts", "effort"),
        "efforts",
        7,
        default=[0.0] * 7,
    )
    if "gripper_effort" in payload:
        efforts[6] = _number(payload["gripper_effort"], "gripper_effort")

    message = message_class()
    if hasattr(message, "header") and stamp is not None:
        message.header.stamp = stamp
    message.name = [str(name) for name in payload.get("names", JOINT_NAMES)]
    if len(message.name) != 7:
        raise CommandValidationError("names must contain exactly 7 values.")
    message.position = positions
    message.velocity = velocities
    message.effort = efforts
    return message


def build_pos_cmd(payload, message_class, stamp=None):
    payload = _as_payload_dict(payload)
    pose = payload.get("pose", {})
    if pose is not None and not isinstance(pose, dict):
        raise CommandValidationError("pose must be a JSON object.")
    source = {**pose, **payload}

    message = message_class()
    for field in ("x", "y", "z", "roll", "pitch", "yaw"):
        setattr(message, field, _number(source.get(field), field))
    message.gripper = _number(source.get("gripper", 0.0), "gripper")
    message.mode1 = _int_number(source.get("mode1", 0), "mode1")
    message.mode2 = _int_number(source.get("mode2", 0), "mode2")
    return message


def build_bool_command(payload, message_class, stamp=None):
    payload = _as_payload_dict(payload)
    marker = object()
    value = payload.get("enabled", marker)
    if value is marker:
        value = payload.get("data", marker)
    if value is marker:
        value = payload.get("value", marker)
    if value is marker:
        raise CommandValidationError("Bool command requires enabled, data, or value.")
    if not isinstance(value, bool):
        raise CommandValidationError("Bool command value must be true or false.")

    message = message_class()
    message.data = value
    return message


BUILDERS = {
    "joint_state": build_joint_state_command,
    "pos_cmd": build_pos_cmd,
    "bool": build_bool_command,
}


def build_command(builder_name, payload, message_class, stamp=None):
    try:
        builder = BUILDERS[builder_name]
    except KeyError as exc:
        raise CommandValidationError(f"Unknown command builder: {builder_name}") from exc
    return builder(payload, message_class, stamp=stamp)

