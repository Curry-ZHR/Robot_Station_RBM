import math
import os


JOINT_NAMES = ["joint0", "joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
INITIAL_POSE_XY_VARIANCE = 0.25
INITIAL_POSE_YAW_VARIANCE = math.radians(15.0) ** 2


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


def _finite_number(value, field):
    parsed = _number(value, field)
    if not math.isfinite(parsed):
        raise CommandValidationError(f"{field} must be a finite number.")
    return parsed


def _payload_number(payload, keys, field, nested=None, default=0.0):
    marker = object()
    value = marker
    for key in keys:
        if key in payload:
            value = payload[key]
            break
    if value is marker and nested:
        nested_payload = payload.get(nested[0])
        if isinstance(nested_payload, dict) and nested[1] in nested_payload:
            value = nested_payload[nested[1]]
    if value is marker:
        value = default
    return _finite_number(value, field)


def build_twist_command(payload, message_class, stamp=None):
    payload = _as_payload_dict(payload)
    message = message_class()
    message.linear.x = _payload_number(
        payload,
        ("linearX", "linear_x", "x", "vx", "forward"),
        "linearX",
        nested=("linear", "x"),
    )
    message.linear.y = _payload_number(
        payload,
        ("linearY", "linear_y", "y", "vy", "lateral"),
        "linearY",
        nested=("linear", "y"),
    )
    message.linear.z = _payload_number(
        payload,
        ("linearZ", "linear_z", "z", "vz"),
        "linearZ",
        nested=("linear", "z"),
    )
    message.angular.x = _payload_number(
        payload,
        ("angularX", "angular_x", "rollRate"),
        "angularX",
        nested=("angular", "x"),
    )
    message.angular.y = _payload_number(
        payload,
        ("angularY", "angular_y", "pitchRate"),
        "angularY",
        nested=("angular", "y"),
    )
    message.angular.z = _payload_number(
        payload,
        ("angularZ", "angular_z", "yawRate", "wz", "angularVelocity"),
        "angularZ",
        nested=("angular", "z"),
    )
    return message


def _initial_pose_yaw(source):
    for key in ("yawDeg", "yaw_deg", "yawDegrees", "thetaDeg", "theta_deg"):
        if key in source:
            return math.radians(_finite_number(source[key], key))
    for key in ("yawRad", "yaw_rad", "theta", "yaw"):
        if key in source:
            return _finite_number(source[key], key)
    raise CommandValidationError("Initial pose requires yawDeg or yawRad.")


def _initial_pose_frame_id(source):
    value = source.get("frameId", source.get("frame_id", os.environ.get("LOCALIZATION_INITIAL_POSE_FRAME", "map")))
    frame_id = str(value or "").strip()
    if not frame_id:
        raise CommandValidationError("frameId must be a non-empty string.")
    return frame_id


def _initial_pose_covariance(source):
    if "covariance" in source:
        values = _number_list(source["covariance"], "covariance", expected_len=36)
        if not all(math.isfinite(value) for value in values):
            raise CommandValidationError("covariance must contain finite numbers.")
        return values

    values = [0.0] * 36
    values[0] = INITIAL_POSE_XY_VARIANCE
    values[7] = INITIAL_POSE_XY_VARIANCE
    values[35] = INITIAL_POSE_YAW_VARIANCE
    return values


def build_initial_pose_command(payload, message_class, stamp=None):
    payload = _as_payload_dict(payload)
    pose = payload.get("pose", {})
    if pose is not None and not isinstance(pose, dict):
        raise CommandValidationError("pose must be a JSON object.")
    source = {**(pose or {}), **payload}

    x = _finite_number(source.get("x"), "x")
    y = _finite_number(source.get("y"), "y")
    z = _finite_number(source.get("z", 0.0), "z")
    yaw = _initial_pose_yaw(source)

    message = message_class()
    if hasattr(message, "header"):
        if stamp is not None:
            message.header.stamp = stamp
        message.header.frame_id = _initial_pose_frame_id(source)

    message.pose.pose.position.x = x
    message.pose.pose.position.y = y
    message.pose.pose.position.z = z
    message.pose.pose.orientation.x = 0.0
    message.pose.pose.orientation.y = 0.0
    message.pose.pose.orientation.z = math.sin(yaw / 2.0)
    message.pose.pose.orientation.w = math.cos(yaw / 2.0)
    message.pose.covariance = _initial_pose_covariance(source)
    return message


BUILDERS = {
    "joint_state": build_joint_state_command,
    "pos_cmd": build_pos_cmd,
    "bool": build_bool_command,
    "twist": build_twist_command,
    "initial_pose": build_initial_pose_command,
}


def build_command(builder_name, payload, message_class, stamp=None):
    try:
        builder = BUILDERS[builder_name]
    except KeyError as exc:
        raise CommandValidationError(f"Unknown command builder: {builder_name}") from exc
    return builder(payload, message_class, stamp=stamp)
