#!/usr/bin/env python3
import threading

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool

from piper.joint_smoother import (
    DEFAULT_MAX_JOINT_SPEED_DEG_S,
    LatestTargetSmoother,
    clamp_speed_deg_s,
    normalize_vector,
    speed_from_velocity,
)


class PiperJointSmootherNode(Node):
    def __init__(self):
        super().__init__("piper_joint_smoother_node")
        self.declare_parameter("target_topic", "/joint_states_gripper")
        self.declare_parameter("feedback_topic", "/joint_states_single")
        self.declare_parameter("output_topic", "/joint_states_gripper_raw")
        self.declare_parameter("hold_topic", "/joint_states_gripper/hold")
        self.declare_parameter("enable_topic", "/enable_flag")
        self.declare_parameter("publish_rate_hz", 50.0)
        self.declare_parameter("max_joint_speed_deg_s", DEFAULT_MAX_JOINT_SPEED_DEG_S)
        self.declare_parameter("wait_log_period_sec", 2.0)

        self.target_topic = str(self.get_parameter("target_topic").value)
        self.feedback_topic = str(self.get_parameter("feedback_topic").value)
        self.output_topic = str(self.get_parameter("output_topic").value)
        self.hold_topic = str(self.get_parameter("hold_topic").value)
        self.enable_topic = str(self.get_parameter("enable_topic").value)
        self.publish_rate_hz = max(1.0, float(self.get_parameter("publish_rate_hz").value))
        self.default_max_joint_speed_deg_s = clamp_speed_deg_s(
            self.get_parameter("max_joint_speed_deg_s").value
        )
        self.wait_log_period_sec = max(0.2, float(self.get_parameter("wait_log_period_sec").value))

        self._lock = threading.RLock()
        self._smoother = LatestTargetSmoother(self.default_max_joint_speed_deg_s)
        self._last_tick_sec = None
        self._last_wait_log_sec = 0.0
        self._waiting_for_feedback = False

        self._publisher = self.create_publisher(JointState, self.output_topic, 10)
        self.create_subscription(JointState, self.target_topic, self.target_callback, 10)
        self.create_subscription(JointState, self.feedback_topic, self.feedback_callback, 10)
        self.create_subscription(Bool, self.hold_topic, self.hold_callback, 10)
        self.create_subscription(Bool, self.enable_topic, self.enable_callback, 10)
        self.create_timer(1.0 / self.publish_rate_hz, self.timer_callback)

        self.get_logger().info(
            "Piper joint smoother: target=%s feedback=%s output=%s hold=%s rate=%.1fHz max_speed=%.2fdeg/s"
            % (
                self.target_topic,
                self.feedback_topic,
                self.output_topic,
                self.hold_topic,
                self.publish_rate_hz,
                self.default_max_joint_speed_deg_s,
            )
        )

    def _now_sec(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def target_callback(self, msg):
        max_speed = speed_from_velocity(msg.velocity, self.default_max_joint_speed_deg_s)
        raw_velocity = list(normalize_vector(msg.velocity))
        for index in range(6):
            raw_velocity[index] = 0.0

        try:
            with self._lock:
                initialized = self._smoother.set_target(
                    msg.position,
                    max_joint_speed_deg_s=max_speed,
                    names=msg.name,
                    velocity=raw_velocity,
                    effort=msg.effort,
                )
                self._waiting_for_feedback = not initialized
        except ValueError as exc:
            self.get_logger().warning("Ignored invalid joint target on %s: %s" % (self.target_topic, exc))
            return

        if initialized:
            self.get_logger().debug(
                "Accepted joint target on %s at %.2f deg/s" % (self.target_topic, max_speed)
            )
        else:
            self.get_logger().warning(
                "Received joint target on %s, waiting for feedback on %s before smoothing."
                % (self.target_topic, self.feedback_topic)
            )

    def feedback_callback(self, msg):
        try:
            with self._lock:
                was_waiting = self._waiting_for_feedback
                self._smoother.update_feedback(msg.position)
                self._waiting_for_feedback = False
        except ValueError as exc:
            self.get_logger().warning("Ignored invalid joint feedback on %s: %s" % (self.feedback_topic, exc))
            return

        if was_waiting:
            self.get_logger().info("Feedback initialized from %s; smoothing can start." % self.feedback_topic)

    def hold_callback(self, msg):
        if not msg.data:
            return
        with self._lock:
            holding = self._smoother.hold()
        if holding:
            self.get_logger().warning("Joint smoother hold requested; active target cleared.")
        else:
            self.get_logger().warning("Joint smoother hold requested before feedback; active target cleared.")

    def enable_callback(self, msg):
        if msg.data:
            return
        with self._lock:
            self._smoother.hold()
        self.get_logger().warning("Enable flag is false; active joint target cleared.")

    def timer_callback(self):
        now_sec = self._now_sec()
        with self._lock:
            if self._last_tick_sec is None:
                dt_sec = 1.0 / self.publish_rate_hz
            else:
                dt_sec = now_sec - self._last_tick_sec
            self._last_tick_sec = now_sec
            output = self._smoother.tick(dt_sec)
            waiting = self._waiting_for_feedback

        if output is None:
            if waiting and now_sec - self._last_wait_log_sec >= self.wait_log_period_sec:
                self._last_wait_log_sec = now_sec
                self.get_logger().warning(
                    "Waiting for feedback on %s before publishing smoothed joint targets."
                    % self.feedback_topic
                )
            return

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(output.names)
        msg.position = list(output.positions)
        msg.velocity = list(output.velocity)
        msg.effort = list(output.effort)
        self._publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = PiperJointSmootherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
