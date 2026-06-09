#include <Eigen/Dense>

#include <pcl/common/transforms.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/io/pcd_io.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/registration/gicp.h>
#include <pcl/registration/ndt.h>
#include <pcl_conversions/pcl_conversions.h>

#include <nav_msgs/msg/odometry.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <tf2/time.h>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_sensor_msgs/tf2_sensor_msgs.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <mutex>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace fs = std::filesystem;
using PointT = pcl::PointXYZI;
using CloudT = pcl::PointCloud<PointT>;
using Clock = std::chrono::steady_clock;

std::mutex g_log_mutex;

struct Options
{
  fs::path session_dir;
  fs::path progress_path;
  int frames = 10;
  std::string cloud_topic = "/rslidar_points";
  std::string odom_topic = "/odom";
  std::string base_frame = "base_link";
  double capture_timeout_sec = 20.0;
  double voxel_leaf = 0.02;
  double ndt_resolution = 0.5;
  double gicp_max_correspondence = 0.20;
};

struct Pose2D
{
  double x = 0.0;
  double y = 0.0;
  double yaw = 0.0;
};

struct SessionState
{
  bool valid = false;
  int next_index = 0;
  Pose2D previous_odom;
  Eigen::Matrix4f previous_transform = Eigen::Matrix4f::Identity();
};

struct RegistrationReport
{
  std::string stage = "initial_map";
  bool ndt_converged = false;
  bool gicp_converged = false;
  double ndt_fitness = std::numeric_limits<double>::quiet_NaN();
  double fitness = std::numeric_limits<double>::quiet_NaN();
  int source_points = 0;
  int map_points = 0;
  int tf_applied = 0;
  int tf_failed = 0;
  std::string cloud_frame;
  std::string base_frame;
  Eigen::Matrix4f initial_guess = Eigen::Matrix4f::Identity();
  Eigen::Matrix4f final_transform = Eigen::Matrix4f::Identity();
};

struct KeyframeReport
{
  int index = 0;
  int frames = 0;
  int points = 0;
  fs::path path;
};

struct RunReport
{
  bool ok = false;
  std::string detail;
  fs::path map_path;
  KeyframeReport keyframe;
  RegistrationReport registration;
};

struct CaptureResult
{
  std::vector<CloudT::Ptr> clouds;
  Pose2D odom;
  int tf_applied = 0;
  int tf_failed = 0;
  std::string cloud_frame;
};

std::string requireValue(int & i, int argc, char ** argv, const std::string & name)
{
  if (i + 1 >= argc) {
    throw std::runtime_error("Missing value for " + name);
  }
  return argv[++i];
}

Options parseArgs(int argc, char ** argv)
{
  Options options;
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "--session-dir") {
      options.session_dir = requireValue(i, argc, argv, arg);
    } else if (arg == "--progress-path") {
      options.progress_path = requireValue(i, argc, argv, arg);
    } else if (arg == "--frames") {
      options.frames = std::stoi(requireValue(i, argc, argv, arg));
    } else if (arg == "--cloud-topic") {
      options.cloud_topic = requireValue(i, argc, argv, arg);
    } else if (arg == "--odom-topic") {
      options.odom_topic = requireValue(i, argc, argv, arg);
    } else if (arg == "--base-frame") {
      options.base_frame = requireValue(i, argc, argv, arg);
    } else if (arg == "--capture-timeout-sec") {
      options.capture_timeout_sec = std::stod(requireValue(i, argc, argv, arg));
    } else if (arg == "--voxel-leaf") {
      options.voxel_leaf = std::stod(requireValue(i, argc, argv, arg));
    } else if (arg == "--ndt-resolution") {
      options.ndt_resolution = std::stod(requireValue(i, argc, argv, arg));
    } else if (arg == "--gicp-max-correspondence") {
      options.gicp_max_correspondence = std::stod(requireValue(i, argc, argv, arg));
    } else if (arg == "--help" || arg == "-h") {
      throw std::runtime_error(
        "Usage: robot_station_mapper_cli --session-dir DIR [--frames N] "
        "[--cloud-topic TOPIC] [--odom-topic TOPIC]");
    } else {
      throw std::runtime_error("Unknown argument: " + arg);
    }
  }
  if (options.session_dir.empty()) {
    throw std::runtime_error("--session-dir is required");
  }
  options.frames = std::max(1, std::min(200, options.frames));
  options.capture_timeout_sec = std::max(2.0, options.capture_timeout_sec);
  options.voxel_leaf = std::max(0.001, options.voxel_leaf);
  options.ndt_resolution = std::max(0.05, options.ndt_resolution);
  options.gicp_max_correspondence = std::max(0.02, options.gicp_max_correspondence);
  return options;
}

std::string escapeJson(const std::string & text)
{
  std::ostringstream out;
  for (const char ch : text) {
    switch (ch) {
      case '\\':
        out << "\\\\";
        break;
      case '"':
        out << "\\\"";
        break;
      case '\n':
        out << "\\n";
        break;
      case '\r':
        out << "\\r";
        break;
      case '\t':
        out << "\\t";
        break;
      default:
        out << ch;
        break;
    }
  }
  return out.str();
}

std::string jsonString(const std::string & text) { return "\"" + escapeJson(text) + "\""; }

std::string jsonNumber(const double value)
{
  if (!std::isfinite(value)) {
    return "null";
  }
  std::ostringstream out;
  out << std::setprecision(10) << value;
  return out.str();
}

std::string matrixJson(const Eigen::Matrix4f & matrix)
{
  std::ostringstream out;
  out << "[";
  bool first = true;
  for (int row = 0; row < 4; ++row) {
    for (int col = 0; col < 4; ++col) {
      if (!first) {
        out << ",";
      }
      first = false;
      out << std::setprecision(10) << matrix(row, col);
    }
  }
  out << "]";
  return out.str();
}

std::string nowString()
{
  const auto now = std::chrono::system_clock::now();
  const auto time = std::chrono::system_clock::to_time_t(now);
  std::tm tm{};
  localtime_r(&time, &tm);
  std::ostringstream out;
  out << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
  return out.str();
}

double elapsedSeconds(const Clock::time_point & started_at)
{
  const auto elapsed = Clock::now() - started_at;
  return std::chrono::duration<double>(elapsed).count();
}

std::string secondsText(const double seconds)
{
  std::ostringstream out;
  out << std::fixed << std::setprecision(2) << seconds << "s";
  return out.str();
}

void logLine(const std::string & message)
{
  std::lock_guard<std::mutex> lock(g_log_mutex);
  std::cout << "[" << nowString() << "] " << message << std::endl;
}

class StageHeartbeat
{
public:
  StageHeartbeat(std::string name, std::chrono::seconds interval)
  : name_(std::move(name)), interval_(interval), started_at_(Clock::now())
  {
    worker_ = std::thread([this]() { run(); });
  }

  ~StageHeartbeat()
  {
    {
      std::lock_guard<std::mutex> lock(mutex_);
      stop_ = true;
    }
    condition_.notify_all();
    if (worker_.joinable()) {
      worker_.join();
    }
  }

private:
  void run()
  {
    std::unique_lock<std::mutex> lock(mutex_);
    while (!condition_.wait_for(lock, interval_, [this]() { return stop_; })) {
      lock.unlock();
      logLine(name_ + " still running, elapsed=" + secondsText(elapsedSeconds(started_at_)));
      lock.lock();
    }
  }

  std::string name_;
  std::chrono::seconds interval_;
  Clock::time_point started_at_;
  bool stop_ = false;
  std::mutex mutex_;
  std::condition_variable condition_;
  std::thread worker_;
};

void writeReport(const fs::path & path, const RunReport & report)
{
  fs::create_directories(path.parent_path());
  std::ofstream out(path);
  out << "{\n";
  out << "  \"ok\": " << (report.ok ? "true" : "false") << ",\n";
  out << "  \"detail\": " << jsonString(report.detail) << ",\n";
  out << "  \"mapPath\": " << jsonString(report.map_path.generic_string()) << ",\n";
  out << "  \"keyframe\": {\n";
  out << "    \"index\": " << report.keyframe.index << ",\n";
  out << "    \"frames\": " << report.keyframe.frames << ",\n";
  out << "    \"points\": " << report.keyframe.points << ",\n";
  out << "    \"path\": " << jsonString(report.keyframe.path.generic_string()) << "\n";
  out << "  },\n";
  out << "  \"registration\": {\n";
  out << "    \"stage\": " << jsonString(report.registration.stage) << ",\n";
  out << "    \"ndtConverged\": " << (report.registration.ndt_converged ? "true" : "false") << ",\n";
  out << "    \"gicpConverged\": " << (report.registration.gicp_converged ? "true" : "false") << ",\n";
  out << "    \"ndtFitness\": " << jsonNumber(report.registration.ndt_fitness) << ",\n";
  out << "    \"fitness\": " << jsonNumber(report.registration.fitness) << ",\n";
  out << "    \"sourcePoints\": " << report.registration.source_points << ",\n";
  out << "    \"mapPoints\": " << report.registration.map_points << ",\n";
  out << "    \"tfApplied\": " << report.registration.tf_applied << ",\n";
  out << "    \"tfFailed\": " << report.registration.tf_failed << ",\n";
  out << "    \"cloudFrame\": " << jsonString(report.registration.cloud_frame) << ",\n";
  out << "    \"baseFrame\": " << jsonString(report.registration.base_frame) << ",\n";
  out << "    \"initialGuess\": " << matrixJson(report.registration.initial_guess) << ",\n";
  out << "    \"finalTransform\": " << matrixJson(report.registration.final_transform) << "\n";
  out << "  }\n";
  out << "}\n";
}

void writeProgress(
  const fs::path & path, const std::string & phase, const int captured_frames = -1,
  const int target_frames = -1)
{
  if (path.empty()) {
    return;
  }
  fs::create_directories(path.parent_path());
  std::ofstream out(path);
  out << "{\n";
  out << "  \"phase\": " << jsonString(phase);
  if (captured_frames >= 0) {
    out << ",\n  \"capturedFrames\": " << captured_frames;
  }
  if (target_frames >= 0) {
    out << ",\n  \"targetFrames\": " << target_frames;
  }
  out << "\n}\n";
}

double yawFromOdom(const nav_msgs::msg::Odometry & odom)
{
  const auto & q = odom.pose.pose.orientation;
  const double siny_cosp = 2.0 * (q.w * q.z + q.x * q.y);
  const double cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z);
  return std::atan2(siny_cosp, cosy_cosp);
}

Pose2D poseFromOdom(const nav_msgs::msg::Odometry & odom)
{
  return Pose2D{odom.pose.pose.position.x, odom.pose.pose.position.y, yawFromOdom(odom)};
}

double normalizeAngle(double angle)
{
  constexpr double pi = 3.14159265358979323846;
  while (angle > pi) {
    angle -= 2.0 * pi;
  }
  while (angle < -pi) {
    angle += 2.0 * pi;
  }
  return angle;
}

Eigen::Matrix4f transform2D(const double x, const double y, const double yaw)
{
  Eigen::Matrix4f matrix = Eigen::Matrix4f::Identity();
  const float c = static_cast<float>(std::cos(yaw));
  const float s = static_cast<float>(std::sin(yaw));
  matrix(0, 0) = c;
  matrix(0, 1) = -s;
  matrix(1, 0) = s;
  matrix(1, 1) = c;
  matrix(0, 3) = static_cast<float>(x);
  matrix(1, 3) = static_cast<float>(y);
  return matrix;
}

Eigen::Matrix4f odomDeltaCurrentToPrevious(const Pose2D & previous, const Pose2D & current)
{
  const double dx = current.x - previous.x;
  const double dy = current.y - previous.y;
  const double c = std::cos(previous.yaw);
  const double s = std::sin(previous.yaw);
  const double local_x = c * dx + s * dy;
  const double local_y = -s * dx + c * dy;
  return transform2D(local_x, local_y, normalizeAngle(current.yaw - previous.yaw));
}

bool matrixFinite(const Eigen::Matrix4f & matrix)
{
  for (int row = 0; row < 4; ++row) {
    for (int col = 0; col < 4; ++col) {
      if (!std::isfinite(matrix(row, col))) {
        return false;
      }
    }
  }
  return true;
}

CloudT::Ptr cleanCloud(const CloudT & input)
{
  auto output = std::make_shared<CloudT>();
  output->points.reserve(input.points.size());
  for (const auto & point : input.points) {
    if (!std::isfinite(point.x) || !std::isfinite(point.y) || !std::isfinite(point.z)) {
      continue;
    }
    PointT cleaned = point;
    if (!std::isfinite(cleaned.intensity)) {
      cleaned.intensity = 0.0f;
    }
    output->points.push_back(cleaned);
  }
  output->width = static_cast<std::uint32_t>(output->points.size());
  output->height = 1;
  output->is_dense = true;
  return output;
}

CloudT::Ptr downsampleCloud(const CloudT::ConstPtr & input, const double leaf)
{
  if (!input || input->empty() || leaf <= 0.0) {
    auto copy = std::make_shared<CloudT>();
    if (input) {
      *copy = *input;
    }
    return copy;
  }
  pcl::VoxelGrid<PointT> voxel;
  voxel.setInputCloud(input);
  const float leaf_f = static_cast<float>(leaf);
  voxel.setLeafSize(leaf_f, leaf_f, leaf_f);
  auto output = std::make_shared<CloudT>();
  voxel.filter(*output);
  output->width = static_cast<std::uint32_t>(output->points.size());
  output->height = 1;
  output->is_dense = true;
  return output;
}

CloudT::Ptr mergeClouds(const std::vector<CloudT::Ptr> & clouds, const double leaf)
{
  auto merged = std::make_shared<CloudT>();
  for (const auto & cloud : clouds) {
    if (cloud) {
      *merged += *cloud;
    }
  }
  merged->width = static_cast<std::uint32_t>(merged->points.size());
  merged->height = 1;
  merged->is_dense = true;
  return downsampleCloud(merged, leaf);
}

SessionState readState(const fs::path & path)
{
  SessionState state;
  std::ifstream in(path);
  if (!in) {
    return state;
  }
  if (!(in >> state.next_index >> state.previous_odom.x >> state.previous_odom.y >>
        state.previous_odom.yaw)) {
    return state;
  }
  bool matrix_ok = true;
  for (int row = 0; row < 4; ++row) {
    for (int col = 0; col < 4; ++col) {
      if (!(in >> state.previous_transform(row, col))) {
        matrix_ok = false;
      }
    }
  }
  state.valid = matrix_ok;
  if (!state.valid) {
    state.previous_transform = Eigen::Matrix4f::Identity();
    state.next_index = 0;
  }
  return state;
}

void writeState(
  const fs::path & path, const int next_index, const Pose2D & odom,
  const Eigen::Matrix4f & transform)
{
  fs::create_directories(path.parent_path());
  std::ofstream out(path);
  out << next_index << " " << std::setprecision(12) << odom.x << " " << odom.y << " "
      << odom.yaw << "\n";
  for (int row = 0; row < 4; ++row) {
    for (int col = 0; col < 4; ++col) {
      out << std::setprecision(12) << transform(row, col);
      if (!(row == 3 && col == 3)) {
        out << " ";
      }
    }
  }
  out << "\n";
}

std::string paddedIndex(const int index)
{
  const std::string text = std::to_string(index);
  if (text.size() >= 3) {
    return text;
  }
  return std::string(3 - text.size(), '0') + text;
}

class CaptureNode : public rclcpp::Node
{
public:
  explicit CaptureNode(const Options & options)
  : Node("robot_station_mapper_capture"),
    options_(options),
    tf_buffer_(this->get_clock()),
    tf_listener_(tf_buffer_, this, false)
  {
    cloud_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      options_.cloud_topic, rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::PointCloud2::ConstSharedPtr msg) { onCloud(msg); });
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
      options_.odom_topic, rclcpp::QoS(rclcpp::KeepLast(50)).best_effort(),
      [this](nav_msgs::msg::Odometry::ConstSharedPtr msg) { onOdom(msg); });
  }

  bool complete() const
  {
    std::lock_guard<std::mutex> lock(mutex_);
    return static_cast<int>(clouds_.size()) >= options_.frames && latest_odom_.has_value();
  }

  int cloudCount() const
  {
    std::lock_guard<std::mutex> lock(mutex_);
    return static_cast<int>(clouds_.size());
  }

  std::vector<CloudT::Ptr> clouds() const
  {
    std::lock_guard<std::mutex> lock(mutex_);
    return clouds_;
  }

  std::optional<Pose2D> latestOdom() const
  {
    std::lock_guard<std::mutex> lock(mutex_);
    return latest_odom_;
  }

  int tfApplied() const
  {
    std::lock_guard<std::mutex> lock(mutex_);
    return tf_applied_;
  }

  int tfFailed() const
  {
    std::lock_guard<std::mutex> lock(mutex_);
    return tf_failed_;
  }

  std::string cloudFrame() const
  {
    std::lock_guard<std::mutex> lock(mutex_);
    return cloud_frame_;
  }

private:
  void onCloud(const sensor_msgs::msg::PointCloud2::ConstSharedPtr msg)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    if (static_cast<int>(clouds_.size()) >= options_.frames) {
      return;
    }

    sensor_msgs::msg::PointCloud2 working = *msg;
    bool transformed = false;
    const bool wants_transform =
      !options_.base_frame.empty() && !msg->header.frame_id.empty() &&
      msg->header.frame_id != options_.base_frame;
    if (wants_transform) {
      try {
        auto transform = tf_buffer_.lookupTransform(
          options_.base_frame, msg->header.frame_id, tf2_ros::fromMsg(msg->header.stamp));
        tf2::doTransform(*msg, working, transform);
        transformed = true;
      } catch (const std::exception &) {
        try {
          auto transform =
            tf_buffer_.lookupTransform(options_.base_frame, msg->header.frame_id, tf2::TimePointZero);
          tf2::doTransform(*msg, working, transform);
          transformed = true;
        } catch (const std::exception &) {
          ++tf_failed_;
        }
      }
    }

    CloudT pcl_cloud;
    pcl::fromROSMsg(working, pcl_cloud);
    auto cleaned = cleanCloud(pcl_cloud);
    if (cleaned->empty()) {
      return;
    }
    clouds_.push_back(cleaned);
    cloud_frame_ = working.header.frame_id;
    if (transformed) {
      ++tf_applied_;
    }
  }

  void onOdom(const nav_msgs::msg::Odometry::ConstSharedPtr msg)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    latest_odom_ = poseFromOdom(*msg);
  }

  Options options_;
  mutable std::mutex mutex_;
  std::vector<CloudT::Ptr> clouds_;
  std::optional<Pose2D> latest_odom_;
  int tf_applied_ = 0;
  int tf_failed_ = 0;
  std::string cloud_frame_;
  tf2_ros::Buffer tf_buffer_;
  tf2_ros::TransformListener tf_listener_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr cloud_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
};

CaptureResult captureClouds(const Options & options)
{
  logLine(
    "capture started: frames=" + std::to_string(options.frames) + " cloudTopic=" +
    options.cloud_topic + " odomTopic=" + options.odom_topic + " baseFrame=" + options.base_frame +
    " timeout=" + secondsText(options.capture_timeout_sec));
  const auto started_at = Clock::now();
  auto node = std::make_shared<CaptureNode>(options);
  const auto deadline =
    Clock::now() +
    std::chrono::milliseconds(static_cast<int>(options.capture_timeout_sec * 1000.0));

  int last_progress_count = -1;
  while (rclcpp::ok() && !node->complete() && Clock::now() < deadline) {
    rclcpp::spin_some(node);
    const int progress_count = node->cloudCount();
    if (progress_count != last_progress_count) {
      writeProgress(options.progress_path, "capturing", progress_count, options.frames);
      logLine(
        "capture progress: " + std::to_string(progress_count) + "/" +
        std::to_string(options.frames) + " frames");
      last_progress_count = progress_count;
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
  }
  rclcpp::spin_some(node);

  auto captured = node->clouds();
  const auto odom = node->latestOdom();
  writeProgress(options.progress_path, "capturing", static_cast<int>(captured.size()), options.frames);
  if (static_cast<int>(captured.size()) < options.frames) {
    throw std::runtime_error(
      "Timed out while waiting for point clouds: got " + std::to_string(captured.size()) +
      " / " + std::to_string(options.frames));
  }
  if (!odom.has_value()) {
    throw std::runtime_error("Timed out while waiting for odometry on " + options.odom_topic);
  }
  logLine(
    "capture done: frames=" + std::to_string(captured.size()) + " tfApplied=" +
    std::to_string(node->tfApplied()) + " tfFailed=" + std::to_string(node->tfFailed()) +
    " cloudFrame=" + node->cloudFrame() + " elapsed=" + secondsText(elapsedSeconds(started_at)));
  CaptureResult result;
  result.clouds = captured;
  result.odom = odom.value();
  result.tf_applied = node->tfApplied();
  result.tf_failed = node->tfFailed();
  result.cloud_frame = node->cloudFrame();
  return result;
}

RunReport runMapping(const Options & options)
{
  logLine("mapping run started: sessionDir=" + options.session_dir.generic_string());
  RunReport report;
  report.map_path = options.session_dir / "map_tmp.pcd";
  report.registration.base_frame = options.base_frame;

  const fs::path keyframe_dir = options.session_dir / "keyframes";
  const fs::path state_path = options.session_dir / "state.txt";
  fs::create_directories(keyframe_dir);

  writeProgress(options.progress_path, "capturing", 0, options.frames);
  const auto capture = captureClouds(options);
  report.registration.tf_applied = capture.tf_applied;
  report.registration.tf_failed = capture.tf_failed;
  report.registration.cloud_frame = capture.cloud_frame;
  report.registration.base_frame = options.base_frame;

  writeProgress(options.progress_path, "filtering", options.frames, options.frames);
  auto filter_started_at = Clock::now();
  logLine(
    "filtering started: inputClouds=" + std::to_string(capture.clouds.size()) +
    " voxelLeaf=" + std::to_string(options.voxel_leaf));
  auto source = mergeClouds(capture.clouds, options.voxel_leaf);
  if (!source || source->empty()) {
    throw std::runtime_error("Captured point clouds are empty after filtering.");
  }
  report.registration.source_points = static_cast<int>(source->points.size());
  logLine(
    "filtering done: sourcePoints=" + std::to_string(source->points.size()) +
    " elapsed=" + secondsText(elapsedSeconds(filter_started_at)));

  const SessionState state = readState(state_path);
  const int keyframe_index = state.valid ? state.next_index : 0;
  const fs::path keyframe_path = keyframe_dir / ("keyframe_" + paddedIndex(keyframe_index) + ".pcd");
  const Pose2D current_odom = capture.odom;

  CloudT::Ptr aligned(new CloudT);
  Eigen::Matrix4f final_transform = Eigen::Matrix4f::Identity();
  Eigen::Matrix4f initial_guess = Eigen::Matrix4f::Identity();

  if (!state.valid || !fs::exists(report.map_path)) {
    logLine("registration skipped: no existing map, creating initial keyframe");
    *aligned = *source;
    report.registration.stage = "initial_map";
    report.registration.ndt_converged = true;
    report.registration.gicp_converged = true;
    report.registration.ndt_fitness = 0.0;
    report.registration.fitness = 0.0;
  } else {
    writeProgress(options.progress_path, "registering", options.frames, options.frames);
    CloudT::Ptr target(new CloudT);
    if (pcl::io::loadPCDFile<PointT>(report.map_path.string(), *target) != 0 || target->empty()) {
      throw std::runtime_error("Failed to load existing temporary map: " + report.map_path.string());
    }
    logLine(
      "registration started: sourcePoints=" + std::to_string(source->points.size()) +
      " targetPoints=" + std::to_string(target->points.size()) + " nextKeyframe=" +
      std::to_string(keyframe_index));

    initial_guess =
      state.previous_transform * odomDeltaCurrentToPrevious(state.previous_odom, current_odom);
    report.registration.initial_guess = initial_guess;

    writeProgress(options.progress_path, "registering_ndt", options.frames, options.frames);
    auto ndt_started_at = Clock::now();
    logLine(
      "NDT started: resolution=" + std::to_string(options.ndt_resolution) +
      " maxIterations=40 stepSize=0.100000 transformationEpsilon=0.005000");
    pcl::NormalDistributionsTransform<PointT, PointT> ndt;
    ndt.setInputSource(source);
    ndt.setInputTarget(target);
    ndt.setResolution(options.ndt_resolution);
    ndt.setMaximumIterations(40);
    ndt.setStepSize(0.1);
    ndt.setTransformationEpsilon(0.005);
    int ndt_iteration = 0;
    std::function<void(const CloudT &, const pcl::Indices &, const CloudT &, const pcl::Indices &)>
      ndt_progress = [&ndt_iteration, &ndt_started_at](
                       const CloudT & output, const pcl::Indices &, const CloudT &,
                       const pcl::Indices &) {
        ++ndt_iteration;
        logLine(
          "NDT iteration " + std::to_string(ndt_iteration) + "/40: outputPoints=" +
          std::to_string(output.points.size()) + " elapsed=" +
          secondsText(elapsedSeconds(ndt_started_at)));
      };
    ndt.registerVisualizationCallback(ndt_progress);
    CloudT ndt_output;
    {
      StageHeartbeat heartbeat("NDT", std::chrono::seconds(5));
      ndt.align(ndt_output, initial_guess);
    }
    report.registration.ndt_converged = ndt.hasConverged();
    report.registration.ndt_fitness = ndt.getFitnessScore();
    logLine(
      "NDT done: converged=" +
      std::string(report.registration.ndt_converged ? "true" : "false") +
      " iterations=" + std::to_string(ndt.getFinalNumIteration()) + "/40 fitness=" +
      jsonNumber(report.registration.ndt_fitness) + " elapsed=" +
      secondsText(elapsedSeconds(ndt_started_at)));
    Eigen::Matrix4f gicp_guess = ndt.hasConverged() ? ndt.getFinalTransformation() : initial_guess;
    if (!matrixFinite(gicp_guess)) {
      gicp_guess = initial_guess;
      logLine("NDT final transform was not finite; falling back to odometry initial guess for GICP");
    }

    writeProgress(options.progress_path, "registering_gicp", options.frames, options.frames);
    auto gicp_started_at = Clock::now();
    logLine(
      "GICP started: maxIterations=50 maxCorrespondence=" +
      std::to_string(options.gicp_max_correspondence) +
      " transformationEpsilon=0.000500 euclideanFitnessEpsilon=0.000500");
    pcl::GeneralizedIterativeClosestPoint<PointT, PointT> gicp;
    gicp.setInputSource(source);
    gicp.setInputTarget(target);
    gicp.setMaximumIterations(50);
    gicp.setMaxCorrespondenceDistance(options.gicp_max_correspondence);
    gicp.setTransformationEpsilon(0.0005);
    gicp.setEuclideanFitnessEpsilon(0.0005);
    {
      StageHeartbeat heartbeat("GICP", std::chrono::seconds(5));
      gicp.align(*aligned, gicp_guess);
    }
    report.registration.gicp_converged = gicp.hasConverged();
    report.registration.fitness = gicp.getFitnessScore();
    final_transform = gicp.getFinalTransformation();
    logLine(
      "GICP done: converged=" +
      std::string(report.registration.gicp_converged ? "true" : "false") +
      " iterations=" + std::to_string(gicp.nr_iterations_) + "/50 fitness=" +
      jsonNumber(report.registration.fitness) + " alignedPoints=" +
      std::to_string(aligned->points.size()) + " elapsed=" +
      secondsText(elapsedSeconds(gicp_started_at)));
    if (!report.registration.gicp_converged || !matrixFinite(final_transform)) {
      throw std::runtime_error("GICP did not converge; this keyframe was not merged into the map.");
    }

    writeProgress(options.progress_path, "writing_map", options.frames, options.frames);
    auto write_map_started_at = Clock::now();
    logLine("writing temporary map started");
    CloudT::Ptr merged_map(new CloudT);
    *merged_map = *target;
    *merged_map += *aligned;
    auto downsampled_map = downsampleCloud(merged_map, options.voxel_leaf);
    if (pcl::io::savePCDFileBinary(report.map_path.string(), *downsampled_map) != 0) {
      throw std::runtime_error("Failed to save temporary map: " + report.map_path.string());
    }
    report.registration.map_points = static_cast<int>(downsampled_map->points.size());
    report.registration.stage = "ndt_gicp";
    logLine(
      "writing temporary map done: mapPoints=" + std::to_string(downsampled_map->points.size()) +
      " elapsed=" + secondsText(elapsedSeconds(write_map_started_at)));
  }

  writeProgress(options.progress_path, "writing_map", options.frames, options.frames);
  auto output_started_at = Clock::now();
  if (!state.valid || !fs::exists(report.map_path)) {
    logLine("writing initial map started");
    if (pcl::io::savePCDFileBinary(report.map_path.string(), *aligned) != 0) {
      throw std::runtime_error("Failed to save initial map: " + report.map_path.string());
    }
    report.registration.map_points = static_cast<int>(aligned->points.size());
    logLine("writing initial map done: mapPoints=" + std::to_string(aligned->points.size()));
  }

  logLine("writing keyframe started: path=" + keyframe_path.generic_string());
  if (pcl::io::savePCDFileBinary(keyframe_path.string(), *aligned) != 0) {
    throw std::runtime_error("Failed to save keyframe: " + keyframe_path.string());
  }
  logLine(
    "writing keyframe done: keyframe=" + std::to_string(keyframe_index) + " points=" +
    std::to_string(aligned->points.size()) + " elapsed=" + secondsText(elapsedSeconds(output_started_at)));

  report.registration.final_transform = final_transform;
  report.keyframe.index = keyframe_index;
  report.keyframe.frames = options.frames;
  report.keyframe.points = static_cast<int>(aligned->points.size());
  report.keyframe.path = keyframe_path;
  report.ok = true;
  report.detail = "Point cloud keyframe captured and registered.";

  writeState(state_path, keyframe_index + 1, current_odom, final_transform);
  writeProgress(options.progress_path, "done", options.frames, options.frames);
  logLine(
    "mapping run done: stage=" + report.registration.stage + " keyframe=" +
    std::to_string(report.keyframe.index) + " mapPoints=" +
    std::to_string(report.registration.map_points));
  return report;
}

int main(int argc, char ** argv)
{
  Options options;
  fs::path result_path;
  try {
    options = parseArgs(argc, argv);
    fs::create_directories(options.session_dir);
    result_path = options.session_dir / "last_result.json";
  } catch (const std::exception & exc) {
    std::cerr << exc.what() << std::endl;
    return 2;
  }

  rclcpp::init(argc, argv);
  RunReport report;
  report.map_path = options.session_dir / "map_tmp.pcd";
  report.registration.base_frame = options.base_frame;
  try {
    report = runMapping(options);
  } catch (const std::exception & exc) {
    report.ok = false;
    report.detail = exc.what();
    report.registration.stage = "failed";
    writeProgress(options.progress_path, "failed");
  }
  writeReport(result_path, report);
  rclcpp::shutdown();
  return report.ok ? 0 : 3;
}
