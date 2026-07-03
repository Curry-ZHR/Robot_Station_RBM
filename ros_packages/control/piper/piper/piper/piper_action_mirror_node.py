#!/usr/bin/env python3
import threading

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool

from piper.action_mirror import LatestActionMirror, normalize_frame


class PiperActionMirrorNode(Node):
    def __init__(self):
        super().__init__("piper_action_mirror_node")
        self.declare_parameter("input_topic", "/joint_states_gripper_raw")
        self.declare_parameter("feedback_topic", "/joint_states_single")
        self.declare_parameter("target_topic", "/joint_states_gripper")
        self.declare_parameter("hold_topic", "/joint_states_gripper/hold")
        self.declare_parameter("enable_topic", "/enable_flag")
        self.declare_parameter("output_topic", "/master/joint")
        self.declare_parameter("publish_rate_hz", 50.0)
        self.declare_parameter("wait_log_period_sec", 2.0)

        self.input_topic = str(self.get_parameter("input_topic").value)
        self.feedback_topic = str(self.get_parameter("feedback_topic").value)
        self.target_topic = str(self.get_parameter("target_topic").value)
        self.hold_topic = str(self.get_parameter("hold_topic").value)
        self.enable_topic = str(self.get_parameter("enable_topic").value)
        self.output_topic = str(self.get_parameter("output_topic").value)
        self.publish_rate_hz = max(1.0, float(self.get_parameter("publish_rate_hz").value))
        self.wait_log_period_sec = max(0.2, float(self.get_parameter("wait_log_period_sec").value))

        self._lock = threading.RLock()
        self._mirror = LatestActionMirror()
        self._last_wait_log_sec = 0.0

        self._publisher = self.create_publisher(JointState, self.output_topic, 10)
        self.create_subscription(JointState, self.input_topic, self.input_callback, 10)
        self.create_subscription(JointState, self.feedback_topic, self.feedback_callback, 10)
        self.create_subscription(JointState, self.target_topic, self.target_callback, 10)
        self.create_subscription(Bool, self.hold_topic, self.hold_callback, 10)
        self.create_subscription(Bool, self.enable_topic, self.enable_callback, 10)
        self.create_timer(1.0 / self.publish_rate_hz, self.timer_callback)

        self.get_logger().info(
            "Piper action mirror: input=%s feedback=%s target=%s hold=%s output=%s rate=%.1fHz"
            % (
                self.input_topic,
                self.feedback_topic,
                self.target_topic,
                self.hold_topic,
                self.output_topic,
                self.publish_rate_hz,
            )
        )

    def _now_sec(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def _frame_from_msg(self, msg):
        return normalize_frame(msg.name, msg.position, msg.velocity, msg.effort)

    def _publish_frame(self, frame):
        if frame is None:
            return False
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(frame.names)
        msg.position = list(frame.positions)
        msg.velocity = list(frame.velocity)
        msg.effort = list(frame.effort)
        self._publisher.publish(msg)
        return True

    def input_callback(self, msg):
        try:
            frame = self._frame_from_msg(msg)
        except ValueError as exc:
            self.get_logger().warning("Ignored invalid Piper action on %s: %s" % (self.input_topic, exc))
            return
        with self._lock:
            selected = self._mirror.update_action(frame)
        self._publish_frame(selected)

    def feedback_callback(self, msg):
        try:
            frame = self._frame_from_msg(msg)
        except ValueError as exc:
            self.get_logger().warning("Ignored invalid Piper feedback on %s: %s" % (self.feedback_topic, exc))
            return
        with self._lock:
            self._mirror.update_feedback(frame)

    def target_callback(self, msg):
        try:
            self._frame_from_msg(msg)
        except ValueError as exc:
            self.get_logger().warning("Ignored invalid Piper target on %s: %s" % (self.target_topic, exc))
            return
        with self._lock:
            self._mirror.clear_hold()

    def hold_callback(self, msg):
        if not msg.data:
            return
        with self._lock:
            self._mirror.set_hold(True)

    def enable_callback(self, msg):
        if msg.data:
            return
        with self._lock:
            self._mirror.set_hold(True)

    def timer_callback(self):
        with self._lock:
            frame = self._mirror.current_frame()
        if self._publish_frame(frame):
            return

        now_sec = self._now_sec()
        if now_sec - self._last_wait_log_sec >= self.wait_log_period_sec:
            self._last_wait_log_sec = now_sec
            self.get_logger().warning(
                "Piper action mirror has no action or feedback yet; not publishing %s."
                % self.output_topic
            )


def main(args=None):
    rclpy.init(args=args)
    node = PiperActionMirrorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
