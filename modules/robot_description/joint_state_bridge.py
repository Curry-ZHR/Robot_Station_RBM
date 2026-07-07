import argparse
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState


DEFAULT_LEFT_INPUT = "/joint_states_single_l"
DEFAULT_RIGHT_INPUT = "/joint_states_single_r"
DEFAULT_LIFTING_INPUT = "/LiftMotorStatePub"
DEFAULT_OUTPUT = "/joint_states"
DEFAULT_GRIPPER_SCALE = 1.0
DEFAULT_LIFTING_HEIGHT_SCALE = 0.001
DEFAULT_LIFTING_JOINT_OFFSET = 0.0
DEFAULT_LIFTING_JOINT_MIN = 0.0
DEFAULT_LIFTING_JOINT_MAX = 0.75
DEFAULT_PUBLISH_RATE_HZ = 20.0
BASE_JOINT_NAMES = (
    "fr_steering_joint",
    "fr_wheel",
    "fl_steering_joint",
    "fl_wheel",
    "rl_steering_joint",
    "rl_wheel",
    "rr_steering_joint",
    "rr_wheel",
    "lifting_joint",
)


def _finite(value, default=0.0):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if math.isfinite(parsed) else float(default)


def _value_at(values, index, default=0.0):
    return _finite(values[index], default) if index < len(values) else float(default)


def _clamp(value, lower, upper):
    lower = float(lower)
    upper = float(upper)
    if lower > upper:
        lower, upper = upper, lower
    return max(lower, min(upper, float(value)))


def _side_joint_names(prefix):
    return [f"{prefix}/joint{index}" for index in range(1, 9)]


def _side_joint_positions(source, gripper_scale=DEFAULT_GRIPPER_SCALE):
    positions = [_value_at(source.position, index) for index in range(6)]
    gripper = 0.0
    if len(source.position) > 6:
        gripper = _clamp(_value_at(source.position, 6) * float(gripper_scale), 0.0, 0.05)
    positions.extend((gripper, -gripper))
    return positions


def _prefix_joint_state(source, prefix, gripper_scale=DEFAULT_GRIPPER_SCALE):
    output = JointState()
    output.header = source.header
    output.name = _side_joint_names(prefix)
    output.position = _side_joint_positions(source, gripper_scale)
    return output


def _lifting_joint_position(
    source,
    height_scale=DEFAULT_LIFTING_HEIGHT_SCALE,
    joint_offset=DEFAULT_LIFTING_JOINT_OFFSET,
    joint_min=DEFAULT_LIFTING_JOINT_MIN,
    joint_max=DEFAULT_LIFTING_JOINT_MAX,
):
    height = _finite(getattr(source, "back_height", 0.0))
    position = height * float(height_scale) + float(joint_offset)
    return _clamp(position, joint_min, joint_max)


class RobotStationJointStateBridge(Node):
    def __init__(
        self,
        left_input,
        right_input,
        output_topic,
        gripper_scale,
        publish_rate_hz=DEFAULT_PUBLISH_RATE_HZ,
        lifting_input=DEFAULT_LIFTING_INPUT,
        lifting_height_scale=DEFAULT_LIFTING_HEIGHT_SCALE,
        lifting_joint_offset=DEFAULT_LIFTING_JOINT_OFFSET,
        lifting_joint_min=DEFAULT_LIFTING_JOINT_MIN,
        lifting_joint_max=DEFAULT_LIFTING_JOINT_MAX,
    ):
        super().__init__("robot_station_joint_state_bridge")
        self._publisher = self.create_publisher(JointState, output_topic, 10)
        self._gripper_scale = float(gripper_scale)
        self._lifting_height_scale = float(lifting_height_scale)
        self._lifting_joint_offset = float(lifting_joint_offset)
        self._lifting_joint_min = float(lifting_joint_min)
        self._lifting_joint_max = float(lifting_joint_max)
        self._joint_positions = {name: 0.0 for name in BASE_JOINT_NAMES}
        self._joint_positions.update({name: 0.0 for name in _side_joint_names("left")})
        self._joint_positions.update({name: 0.0 for name in _side_joint_names("right")})
        self._joint_order = list(self._joint_positions)
        self._received_sides = set()
        self._received_lifting = False
        self.create_subscription(JointState, left_input, self._handle_left, qos_profile_sensor_data)
        self.create_subscription(JointState, right_input, self._handle_right, qos_profile_sensor_data)
        if str(lifting_input or "").strip():
            self._create_lifting_subscription(str(lifting_input).strip())
        timer_period = 1.0 / max(1.0, float(publish_rate_hz))
        self.create_timer(timer_period, self._publish_joint_state)
        self._publish_joint_state()
        self.get_logger().info(
            f"Bridging {left_input}, {right_input}, and {lifting_input} to {output_topic} "
            "with full robot-description joint names."
        )

    def _create_lifting_subscription(self, lifting_input):
        from lifting_msg_pkg.msg import LiftMotorMsg

        self.create_subscription(LiftMotorMsg, lifting_input, self._handle_lifting, qos_profile_sensor_data)

    def _handle_left(self, message):
        self._update_side("left", message)

    def _handle_right(self, message):
        self._update_side("right", message)

    def _handle_lifting(self, message):
        self._joint_positions["lifting_joint"] = _lifting_joint_position(
            message,
            height_scale=self._lifting_height_scale,
            joint_offset=self._lifting_joint_offset,
            joint_min=self._lifting_joint_min,
            joint_max=self._lifting_joint_max,
        )
        if not self._received_lifting:
            self._received_lifting = True
            self.get_logger().info("Received first lifting motor state.")
        self._publish_joint_state()

    def _update_side(self, prefix, message):
        for name, position in zip(_side_joint_names(prefix), _side_joint_positions(message, self._gripper_scale)):
            self._joint_positions[name] = position
        if prefix not in self._received_sides:
            self._received_sides.add(prefix)
            self.get_logger().info(f"Received first {prefix} Piper joint state.")
        self._publish_joint_state()

    def _publish_joint_state(self):
        message = JointState()
        message.header.stamp = self.get_clock().now().to_msg()
        message.name = list(self._joint_order)
        message.position = [self._joint_positions[name] for name in self._joint_order]
        self._publisher.publish(message)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bridge Piper joint states into robot-description joint names.")
    parser.add_argument("--left-input", default=DEFAULT_LEFT_INPUT)
    parser.add_argument("--right-input", default=DEFAULT_RIGHT_INPUT)
    parser.add_argument("--lifting-input", default=DEFAULT_LIFTING_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--gripper-scale", type=float, default=DEFAULT_GRIPPER_SCALE)
    parser.add_argument("--lifting-height-scale", type=float, default=DEFAULT_LIFTING_HEIGHT_SCALE)
    parser.add_argument("--lifting-joint-offset", type=float, default=DEFAULT_LIFTING_JOINT_OFFSET)
    parser.add_argument("--lifting-joint-min", type=float, default=DEFAULT_LIFTING_JOINT_MIN)
    parser.add_argument("--lifting-joint-max", type=float, default=DEFAULT_LIFTING_JOINT_MAX)
    parser.add_argument("--publish-rate-hz", type=float, default=DEFAULT_PUBLISH_RATE_HZ)
    args = parser.parse_args(argv)

    rclpy.init()
    node = RobotStationJointStateBridge(
        left_input=args.left_input,
        right_input=args.right_input,
        lifting_input=args.lifting_input,
        output_topic=args.output,
        gripper_scale=args.gripper_scale,
        lifting_height_scale=args.lifting_height_scale,
        lifting_joint_offset=args.lifting_joint_offset,
        lifting_joint_min=args.lifting_joint_min,
        lifting_joint_max=args.lifting_joint_max,
        publish_rate_hz=args.publish_rate_hz,
    )
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
