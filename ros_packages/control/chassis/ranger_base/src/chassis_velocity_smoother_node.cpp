// Copyright 2026 Robot Station Contributors
/**
 * @file chassis_velocity_smoother_node.cpp
 * @brief Smooth Ranger chassis velocity targets before publishing to hardware.
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>

#include "geometry_msgs/msg/twist.hpp"
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

namespace
{

double positive_or_default(double value, double fallback)
{
  if (!std::isfinite(value) || value <= 0.0) {
    return fallback;
  }
  return value;
}

double non_negative_or_default(double value, double fallback)
{
  if (!std::isfinite(value) || value < 0.0) {
    return fallback;
  }
  return value;
}

double clean_zero(double value)
{
  return std::abs(value) < 1e-12 ? 0.0 : value;
}

double step_scalar(double current, double target, double accel, double decel, double dt)
{
  const double delta = target - current;
  const double limit = std::abs(target) < std::abs(current) ? decel : accel;
  const double max_step = std::max(0.0, limit) * std::max(0.0, dt);
  if (std::abs(delta) <= max_step) {
    return target;
  }
  return current + std::copysign(max_step, delta);
}

std::string chassis_action_json(const geometry_msgs::msg::Twist & twist)
{
  std::ostringstream out;
  out << std::fixed << std::setprecision(6)
      << "{\"linearX\":" << clean_zero(twist.linear.x)
      << ",\"linearY\":" << clean_zero(twist.linear.y)
      << ",\"angularZ\":" << clean_zero(twist.angular.z)
      << "}";
  return out.str();
}

}  // namespace

class ChassisVelocitySmootherNode : public rclcpp::Node
{
public:
  ChassisVelocitySmootherNode()
  : Node("chassis_velocity_smoother")
  {
    declare_parameter<std::string>("target_topic", "/cmd_vel");
    declare_parameter<std::string>("output_topic", "/cmd_vel_smoothed");
    declare_parameter<std::string>("raw_action_topic", "/action/chassis");
    declare_parameter<std::string>("smoothed_action_topic", "/action/chassis_smoothed");
    declare_parameter<double>("publish_rate_hz", 50.0);
    declare_parameter<double>("linear_accel_mps2", 0.25);
    declare_parameter<double>("linear_decel_mps2", 0.60);
    declare_parameter<double>("angular_accel_rad_s2", 0.80);
    declare_parameter<double>("angular_decel_rad_s2", 1.50);
    declare_parameter<double>("watchdog_timeout_sec", 0.25);
    declare_parameter<double>("linear_deadband_mps", 0.005);
    declare_parameter<double>("angular_deadband_rad_s", 0.01);

    target_topic_ = get_parameter("target_topic").as_string();
    output_topic_ = get_parameter("output_topic").as_string();
    raw_action_topic_ = get_parameter("raw_action_topic").as_string();
    smoothed_action_topic_ = get_parameter("smoothed_action_topic").as_string();
    publish_rate_hz_ = positive_or_default(get_parameter("publish_rate_hz").as_double(), 50.0);
    linear_accel_mps2_ = positive_or_default(get_parameter("linear_accel_mps2").as_double(), 0.25);
    linear_decel_mps2_ = positive_or_default(get_parameter("linear_decel_mps2").as_double(), 0.60);
    angular_accel_rad_s2_ = positive_or_default(
      get_parameter(
        "angular_accel_rad_s2").as_double(), 0.80);
    angular_decel_rad_s2_ = positive_or_default(
      get_parameter(
        "angular_decel_rad_s2").as_double(), 1.50);
    watchdog_timeout_sec_ = non_negative_or_default(
      get_parameter(
        "watchdog_timeout_sec").as_double(), 0.25);
    linear_deadband_mps_ = non_negative_or_default(
      get_parameter(
        "linear_deadband_mps").as_double(), 0.005);
    angular_deadband_rad_s_ = non_negative_or_default(
      get_parameter(
        "angular_deadband_rad_s").as_double(), 0.01);

    target_sub_ = create_subscription<geometry_msgs::msg::Twist>(
      target_topic_,
      rclcpp::QoS(1),
      std::bind(&ChassisVelocitySmootherNode::target_callback, this, std::placeholders::_1));
    output_pub_ = create_publisher<geometry_msgs::msg::Twist>(output_topic_, rclcpp::QoS(1));
    raw_action_pub_ = create_publisher<std_msgs::msg::String>(
      raw_action_topic_, rclcpp::QoS(
        1));
    smoothed_action_pub_ = create_publisher<std_msgs::msg::String>(
      smoothed_action_topic_, rclcpp::QoS(
        1));
    timer_ = create_wall_timer(
      std::chrono::duration<double>(1.0 / publish_rate_hz_),
      std::bind(&ChassisVelocitySmootherNode::timer_callback, this));

    RCLCPP_INFO(
      get_logger(),
      "Chassis velocity smoother: target=%s output=%s raw_action=%s smoothed_action=%s rate=%.1fHz "
      "linear_accel=%.3f linear_decel=%.3f angular_accel=%.3f "
      "angular_decel=%.3f watchdog=%.3fs",
      target_topic_.c_str(),
      output_topic_.c_str(),
      raw_action_topic_.c_str(),
      smoothed_action_topic_.c_str(),
      publish_rate_hz_,
      linear_accel_mps2_,
      linear_decel_mps2_,
      angular_accel_rad_s2_,
      angular_decel_rad_s2_,
      watchdog_timeout_sec_);
  }

private:
  void target_callback(const geometry_msgs::msg::Twist::SharedPtr msg)
  {
    if (!std::isfinite(msg->linear.x) || !std::isfinite(msg->linear.y) ||
      !std::isfinite(msg->angular.z))
    {
      RCLCPP_WARN(get_logger(), "Ignored non-finite chassis velocity target.");
      return;
    }

    std::lock_guard<std::mutex> lock(lock_);
    target_.linear.x = msg->linear.x;
    target_.linear.y = msg->linear.y;
    target_.linear.z = 0.0;
    target_.angular.x = 0.0;
    target_.angular.y = 0.0;
    target_.angular.z = msg->angular.z;
    last_target_time_ = get_clock()->now();
    have_target_ = true;
  }

  void timer_callback()
  {
    const rclcpp::Time now = get_clock()->now();
    geometry_msgs::msg::Twist target;
    geometry_msgs::msg::Twist output;
    {
      std::lock_guard<std::mutex> lock(lock_);
      const double dt = tick_dt(now);
      target = desired_target(now);
      step_toward(target, dt);
      output = current_;
    }

    output_pub_->publish(output);

    std_msgs::msg::String raw_action_msg;
    raw_action_msg.data = chassis_action_json(target);
    raw_action_pub_->publish(raw_action_msg);

    std_msgs::msg::String smoothed_action_msg;
    smoothed_action_msg.data = chassis_action_json(output);
    smoothed_action_pub_->publish(smoothed_action_msg);
  }

  double tick_dt(const rclcpp::Time & now)
  {
    if (!have_tick_) {
      have_tick_ = true;
      last_tick_time_ = now;
      return 1.0 / publish_rate_hz_;
    }
    double dt = (now - last_tick_time_).seconds();
    last_tick_time_ = now;
    if (!std::isfinite(dt) || dt < 0.0) {
      return 1.0 / publish_rate_hz_;
    }
    return std::min(dt, 0.2);
  }

  geometry_msgs::msg::Twist desired_target(const rclcpp::Time & now) const
  {
    if (!have_target_ || (now - last_target_time_).seconds() > watchdog_timeout_sec_) {
      return geometry_msgs::msg::Twist();
    }
    return target_;
  }

  void step_toward(const geometry_msgs::msg::Twist & target, double dt)
  {
    step_linear(target, dt);
    current_.angular.z = step_scalar(
      current_.angular.z,
      target.angular.z,
      angular_accel_rad_s2_,
      angular_decel_rad_s2_,
      dt);

    apply_deadband(target);
    current_.linear.z = 0.0;
    current_.angular.x = 0.0;
    current_.angular.y = 0.0;
  }

  void step_linear(const geometry_msgs::msg::Twist & target, double dt)
  {
    const double delta_x = target.linear.x - current_.linear.x;
    const double delta_y = target.linear.y - current_.linear.y;
    const double delta_norm = std::hypot(delta_x, delta_y);
    if (delta_norm <= 1e-12) {
      current_.linear.x = target.linear.x;
      current_.linear.y = target.linear.y;
      return;
    }

    const double current_norm = std::hypot(current_.linear.x, current_.linear.y);
    const double target_norm = std::hypot(target.linear.x, target.linear.y);
    const double limit = target_norm < current_norm ? linear_decel_mps2_ : linear_accel_mps2_;
    const double max_step = limit * std::max(0.0, dt);
    if (delta_norm <= max_step) {
      current_.linear.x = target.linear.x;
      current_.linear.y = target.linear.y;
      return;
    }

    const double scale = max_step / delta_norm;
    current_.linear.x += delta_x * scale;
    current_.linear.y += delta_y * scale;
  }

  void apply_deadband(const geometry_msgs::msg::Twist & target)
  {
    if (std::abs(target.linear.x) <= linear_deadband_mps_ &&
      std::abs(current_.linear.x) <= linear_deadband_mps_)
    {
      current_.linear.x = 0.0;
    }
    if (std::abs(target.linear.y) <= linear_deadband_mps_ &&
      std::abs(current_.linear.y) <= linear_deadband_mps_)
    {
      current_.linear.y = 0.0;
    }
    if (std::abs(target.angular.z) <= angular_deadband_rad_s_ &&
      std::abs(current_.angular.z) <= angular_deadband_rad_s_)
    {
      current_.angular.z = 0.0;
    }
  }

  std::mutex lock_;
  geometry_msgs::msg::Twist target_;
  geometry_msgs::msg::Twist current_;
  rclcpp::Time last_target_time_;
  rclcpp::Time last_tick_time_;
  bool have_target_ = false;
  bool have_tick_ = false;

  std::string target_topic_;
  std::string output_topic_;
  std::string raw_action_topic_;
  std::string smoothed_action_topic_;
  double publish_rate_hz_ = 50.0;
  double linear_accel_mps2_ = 0.25;
  double linear_decel_mps2_ = 0.60;
  double angular_accel_rad_s2_ = 0.80;
  double angular_decel_rad_s2_ = 1.50;
  double watchdog_timeout_sec_ = 0.25;
  double linear_deadband_mps_ = 0.005;
  double angular_deadband_rad_s_ = 0.01;

  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr target_sub_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr output_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr raw_action_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr smoothed_action_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ChassisVelocitySmootherNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
