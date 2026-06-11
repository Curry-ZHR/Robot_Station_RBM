#include <Eigen/Dense>

#include <pcl/common/transforms.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/io/pcd_io.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/registration/gicp.h>
#include <pcl/registration/ndt.h>
#include <pcl_conversions/pcl_conversions.h>

#ifdef ROBOT_STATION_USE_FAST_GICP_CUDA
#include <fast_gicp/gicp/fast_vgicp_cuda.hpp>
#include <fast_gicp/ndt/ndt_cuda.hpp>
#endif

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <geometry_msgs/msg/pose_with_covariance_stamped.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <std_msgs/msg/string.hpp>
#include <tf2/time.h>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_sensor_msgs/tf2_sensor_msgs.hpp>

#include <algorithm>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <iomanip>
#include <limits>
#include <memory>
#include <mutex>
#include <optional>
#include <sstream>
#include <string>
#include <thread>
#include <utility>

namespace fs = std::filesystem;
using PointT = pcl::PointXYZI;
using CloudT = pcl::PointCloud<PointT>;
using Clock = std::chrono::steady_clock;

#ifdef ROBOT_STATION_USE_FAST_GICP_CUDA
constexpr const char * kRegistrationBackend = "gpu";
constexpr bool kUseNdtWhenTracking = false;
#else
constexpr const char * kRegistrationBackend = "cpu";
constexpr bool kUseNdtWhenTracking = true;
#endif

struct LocalizerOptions
{
  std::string map_path;
  std::string map_name;
  std::string cloud_topic = "/rslidar_points";
  std::string initial_pose_topic = "/initialpose";
  std::string pose_topic = "/localization/pose";
  std::string status_topic = "/localization/status";
  std::string map_frame = "map";
  std::string base_frame = "base_link";
  int max_failed_frames = 3;
  int min_source_points = 50;
  double voxel_leaf = 0.08;
  bool use_ndt_when_tracking = kUseNdtWhenTracking;
  double ndt_resolution = 0.5;
  int ndt_max_iterations = 40;
  double ndt_step_size = 0.1;
  double ndt_transformation_epsilon = 0.005;
  double gicp_max_correspondence = 0.20;
  int gicp_max_iterations = 50;
  double gicp_transformation_epsilon = 0.0005;
  double gicp_euclidean_fitness_epsilon = 0.0005;
  double heartbeat_sec = 1.0;
  std::string registration_backend = kRegistrationBackend;
};

struct Pose2D
{
  double x = 0.0;
  double y = 0.0;
  double yaw = 0.0;
};

struct CloudFrame
{
  CloudT::Ptr cloud;
  std::string cloud_frame;
  rclcpp::Time stamp;
  std::uint64_t sequence = 0;
  int raw_source_points = 0;
};

struct RegistrationResult
{
  bool ok = false;
  bool used_ndt = false;
  bool ndt_converged = false;
  bool gicp_converged = false;
  double ndt_fitness = std::numeric_limits<double>::quiet_NaN();
  double fitness = std::numeric_limits<double>::quiet_NaN();
  int source_points = 0;
  int raw_source_points = 0;
  Eigen::Matrix4f transform = Eigen::Matrix4f::Identity();
};

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

Pose2D poseFromMatrix2D(const Eigen::Matrix4f & matrix)
{
  return Pose2D{
    static_cast<double>(matrix(0, 3)),
    static_cast<double>(matrix(1, 3)),
    normalizeAngle(std::atan2(static_cast<double>(matrix(1, 0)), static_cast<double>(matrix(0, 0))))};
}

double yawFromQuaternion(
  const geometry_msgs::msg::PoseWithCovarianceStamped::SharedPtr & msg)
{
  const auto & q = msg->pose.pose.orientation;
  const double siny_cosp = 2.0 * (q.w * q.z + q.x * q.y);
  const double cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z);
  return std::atan2(siny_cosp, cosy_cosp);
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
  auto output = std::make_shared<CloudT>();
  if (!input || input->empty()) {
    return output;
  }
  if (leaf <= 0.0) {
    *output = *input;
    return output;
  }
  pcl::VoxelGrid<PointT> voxel;
  const float leaf_f = static_cast<float>(leaf);
  voxel.setInputCloud(input);
  voxel.setLeafSize(leaf_f, leaf_f, leaf_f);
  voxel.filter(*output);
  output->width = static_cast<std::uint32_t>(output->points.size());
  output->height = 1;
  output->is_dense = true;
  return output;
}

std::string normalizeFrame(const std::string & frame)
{
  std::string text = frame;
  while (!text.empty() && text.front() == '/') {
    text.erase(text.begin());
  }
  return text;
}

class LocalizerNode : public rclcpp::Node
{
public:
  LocalizerNode()
  : Node("robot_station_localizer"),
    tf_buffer_(this->get_clock()),
    tf_listener_(tf_buffer_, this, false)
  {
    declareParameters();
    readParameters();

    pose_pub_ = create_publisher<geometry_msgs::msg::PoseStamped>(options_.pose_topic, 10);
    status_pub_ = create_publisher<std_msgs::msg::String>(options_.status_topic, 10);
    cloud_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      options_.cloud_topic, rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::PointCloud2::ConstSharedPtr msg) { onCloud(msg); });
    initial_pose_sub_ = create_subscription<geometry_msgs::msg::PoseWithCovarianceStamped>(
      options_.initial_pose_topic, rclcpp::QoS(rclcpp::KeepLast(10)),
      [this](geometry_msgs::msg::PoseWithCovarianceStamped::SharedPtr msg) {
        onInitialPose(msg);
      });

    loadMap();
    heartbeat_timer_ = create_wall_timer(
      std::chrono::milliseconds(
        std::max(100, static_cast<int>(options_.heartbeat_sec * 1000.0))),
      [this]() { publishStatus(); });
    worker_ = std::thread([this]() { workerLoop(); });
    publishStatus();
  }

  ~LocalizerNode() override
  {
    {
      std::lock_guard<std::mutex> lock(mutex_);
      stop_worker_ = true;
    }
    condition_.notify_all();
    if (worker_.joinable()) {
      worker_.join();
    }
  }

private:
  void declareParameters()
  {
    declare_parameter<std::string>("map_path", "");
    declare_parameter<std::string>("map_name", "");
    declare_parameter<std::string>("cloud_topic", options_.cloud_topic);
    declare_parameter<std::string>("initial_pose_topic", options_.initial_pose_topic);
    declare_parameter<std::string>("pose_topic", options_.pose_topic);
    declare_parameter<std::string>("status_topic", options_.status_topic);
    declare_parameter<std::string>("map_frame", options_.map_frame);
    declare_parameter<std::string>("base_frame", options_.base_frame);
    declare_parameter<int>("max_failed_frames", options_.max_failed_frames);
    declare_parameter<int>("min_source_points", options_.min_source_points);
    declare_parameter<double>("voxel_leaf", options_.voxel_leaf);
    declare_parameter<bool>("use_ndt_when_tracking", options_.use_ndt_when_tracking);
    declare_parameter<double>("ndt_resolution", options_.ndt_resolution);
    declare_parameter<int>("ndt_max_iterations", options_.ndt_max_iterations);
    declare_parameter<double>("ndt_step_size", options_.ndt_step_size);
    declare_parameter<double>(
      "ndt_transformation_epsilon", options_.ndt_transformation_epsilon);
    declare_parameter<double>("gicp_max_correspondence", options_.gicp_max_correspondence);
    declare_parameter<int>("gicp_max_iterations", options_.gicp_max_iterations);
    declare_parameter<double>(
      "gicp_transformation_epsilon", options_.gicp_transformation_epsilon);
    declare_parameter<double>(
      "gicp_euclidean_fitness_epsilon", options_.gicp_euclidean_fitness_epsilon);
    declare_parameter<double>("heartbeat_sec", options_.heartbeat_sec);
  }

  void readParameters()
  {
    options_.map_path = get_parameter("map_path").as_string();
    options_.map_name = get_parameter("map_name").as_string();
    options_.cloud_topic = get_parameter("cloud_topic").as_string();
    options_.initial_pose_topic = get_parameter("initial_pose_topic").as_string();
    options_.pose_topic = get_parameter("pose_topic").as_string();
    options_.status_topic = get_parameter("status_topic").as_string();
    options_.map_frame = normalizeFrame(get_parameter("map_frame").as_string());
    options_.base_frame = normalizeFrame(get_parameter("base_frame").as_string());
    options_.max_failed_frames =
      std::max(1, static_cast<int>(get_parameter("max_failed_frames").as_int()));
    options_.min_source_points =
      std::max(1, static_cast<int>(get_parameter("min_source_points").as_int()));
    options_.voxel_leaf = std::max(0.0, get_parameter("voxel_leaf").as_double());
    options_.use_ndt_when_tracking = get_parameter("use_ndt_when_tracking").as_bool();
    options_.ndt_resolution = std::max(0.05, get_parameter("ndt_resolution").as_double());
    options_.ndt_max_iterations =
      std::max(1, static_cast<int>(get_parameter("ndt_max_iterations").as_int()));
    options_.ndt_step_size = std::max(0.001, get_parameter("ndt_step_size").as_double());
    options_.ndt_transformation_epsilon =
      std::max(0.000001, get_parameter("ndt_transformation_epsilon").as_double());
    options_.gicp_max_correspondence =
      std::max(0.02, get_parameter("gicp_max_correspondence").as_double());
    options_.gicp_max_iterations =
      std::max(1, static_cast<int>(get_parameter("gicp_max_iterations").as_int()));
    options_.gicp_transformation_epsilon =
      std::max(0.000001, get_parameter("gicp_transformation_epsilon").as_double());
    options_.gicp_euclidean_fitness_epsilon =
      std::max(0.000001, get_parameter("gicp_euclidean_fitness_epsilon").as_double());
    options_.heartbeat_sec = std::max(0.1, get_parameter("heartbeat_sec").as_double());
  }

  void loadMap()
  {
    std::lock_guard<std::mutex> lock(mutex_);
    state_ = "starting";
    if (options_.map_path.empty()) {
      enterErrorLocked("map_load_failed", "map_path parameter is required.", true);
      return;
    }
    auto loaded = std::make_shared<CloudT>();
    if (pcl::io::loadPCDFile<PointT>(options_.map_path, *loaded) != 0 || loaded->empty()) {
      enterErrorLocked("map_load_failed", "Failed to load non-empty PCD map.", true);
      return;
    }
    auto cleaned_map = cleanCloud(*loaded);
    raw_map_points_ = static_cast<int>(cleaned_map->points.size());
    map_cloud_ = downsampleCloud(cleaned_map, options_.voxel_leaf);
    if (!map_cloud_ || map_cloud_->empty()) {
      enterErrorLocked("map_load_failed", "Map PCD has no valid points.", true);
      return;
    }
    try {
      configureRegistrationLocked();
    } catch (const std::exception & exc) {
      enterErrorLocked("registration_init_failed", exc.what(), true);
      return;
    }
    state_ = "waiting_initial_pose";
    map_loaded_ = true;
    map_points_ = static_cast<int>(map_cloud_->points.size());
    last_error_.clear();
    RCLCPP_INFO(
      get_logger(),
      "Loaded localization map %s with %d/%d points using %s backend voxel_leaf=%.3f use_ndt_when_tracking=%s",
      options_.map_path.c_str(), map_points_, raw_map_points_,
      options_.registration_backend.c_str(), options_.voxel_leaf,
      options_.use_ndt_when_tracking ? "true" : "false");
  }

  void configureRegistrationLocked()
  {
#ifdef ROBOT_STATION_USE_FAST_GICP_CUDA
    ndt_.reset(new fast_gicp::NDTCuda<PointT, PointT>());
    ndt_->setInputTarget(map_cloud_);
    ndt_->setResolution(options_.ndt_resolution);
    ndt_->setMaximumIterations(options_.ndt_max_iterations);
    ndt_->setTransformationEpsilon(options_.ndt_transformation_epsilon);

    gicp_.reset(new fast_gicp::FastVGICPCuda<PointT, PointT>());
    gicp_->setInputTarget(map_cloud_);
    gicp_->setResolution(options_.gicp_max_correspondence);
    gicp_->setMaximumIterations(options_.gicp_max_iterations);
    gicp_->setMaxCorrespondenceDistance(options_.gicp_max_correspondence);
    gicp_->setTransformationEpsilon(options_.gicp_transformation_epsilon);
    gicp_->setEuclideanFitnessEpsilon(options_.gicp_euclidean_fitness_epsilon);
#else
    ndt_.reset(new pcl::NormalDistributionsTransform<PointT, PointT>());
    ndt_->setInputTarget(map_cloud_);
    ndt_->setResolution(options_.ndt_resolution);
    ndt_->setMaximumIterations(options_.ndt_max_iterations);
    ndt_->setStepSize(options_.ndt_step_size);
    ndt_->setTransformationEpsilon(options_.ndt_transformation_epsilon);

    gicp_.reset(new pcl::GeneralizedIterativeClosestPoint<PointT, PointT>());
    gicp_->setInputTarget(map_cloud_);
    gicp_->setMaximumIterations(options_.gicp_max_iterations);
    gicp_->setMaxCorrespondenceDistance(options_.gicp_max_correspondence);
    gicp_->setTransformationEpsilon(options_.gicp_transformation_epsilon);
    gicp_->setEuclideanFitnessEpsilon(options_.gicp_euclidean_fitness_epsilon);
#endif
  }

  void onCloud(const sensor_msgs::msg::PointCloud2::ConstSharedPtr msg)
  {
    sensor_msgs::msg::PointCloud2 working = *msg;
    const std::string source_frame = normalizeFrame(msg->header.frame_id);
    const bool wants_transform =
      !options_.base_frame.empty() && !source_frame.empty() && source_frame != options_.base_frame;

    if (wants_transform) {
      try {
        auto transform = tf_buffer_.lookupTransform(
          options_.base_frame, source_frame, tf2_ros::fromMsg(msg->header.stamp));
        tf2::doTransform(*msg, working, transform);
      } catch (const std::exception &) {
        try {
          auto transform =
            tf_buffer_.lookupTransform(options_.base_frame, source_frame, tf2::TimePointZero);
          tf2::doTransform(*msg, working, transform);
        } catch (const std::exception & exc) {
          recordFrameFailure("cloud_tf_missing", exc.what());
          return;
        }
      }
    }

    CloudT pcl_cloud;
    pcl::fromROSMsg(working, pcl_cloud);
    auto cleaned = cleanCloud(pcl_cloud);
    auto filtered = downsampleCloud(cleaned, options_.voxel_leaf);
    if (!filtered || static_cast<int>(filtered->points.size()) < options_.min_source_points) {
      recordFrameFailure(
        "cloud_too_few_points",
        "Point cloud has fewer valid points than min_source_points after filtering.");
      return;
    }

    {
      std::lock_guard<std::mutex> lock(mutex_);
      latest_cloud_ = CloudFrame{
        filtered, normalizeFrame(working.header.frame_id), rclcpp::Time(msg->header.stamp),
        ++cloud_sequence_, static_cast<int>(cleaned->points.size())};
      last_cloud_frame_ = latest_cloud_->cloud_frame;
      last_raw_source_points_ = latest_cloud_->raw_source_points;
      last_source_points_ = static_cast<int>(filtered->points.size());
      if (last_error_ == "cloud_tf_missing" || last_error_ == "cloud_too_few_points") {
        last_error_.clear();
      }
    }
    condition_.notify_all();
  }

  void onInitialPose(const geometry_msgs::msg::PoseWithCovarianceStamped::SharedPtr msg)
  {
    const std::string frame_id = normalizeFrame(msg->header.frame_id);
    if (frame_id != options_.map_frame) {
      std::lock_guard<std::mutex> lock(mutex_);
      state_ = "error";
      last_error_ = "invalid_initial_pose";
      error_detail_ = "Initial pose frame_id must match map_frame.";
      publishStatusLocked();
      return;
    }

    const auto & position = msg->pose.pose.position;
    const double yaw = yawFromQuaternion(msg);
    if (!std::isfinite(position.x) || !std::isfinite(position.y) || !std::isfinite(yaw)) {
      std::lock_guard<std::mutex> lock(mutex_);
      state_ = "error";
      last_error_ = "invalid_initial_pose";
      error_detail_ = "Initial pose contains non-finite values.";
      publishStatusLocked();
      return;
    }

    {
      std::lock_guard<std::mutex> lock(mutex_);
      last_pose_ = transform2D(position.x, position.y, yaw);
      initialized_ = true;
      tracking_ready_ = false;
      failed_frame_count_ = 0;
      processed_sequence_ = 0;
      last_used_ndt_ = false;
      last_ndt_converged_ = false;
      last_gicp_converged_ = false;
      last_ndt_fitness_ = std::numeric_limits<double>::quiet_NaN();
      last_fitness_ = std::numeric_limits<double>::quiet_NaN();
      state_ = "localizing";
      last_error_.clear();
      error_detail_.clear();
    }
    condition_.notify_all();
    publishStatus();
  }

  void recordFrameFailure(const std::string & code, const std::string & detail)
  {
    {
      std::lock_guard<std::mutex> lock(mutex_);
      ++failed_frame_count_;
      last_error_ = code;
      error_detail_ = detail;
      if (code == "registration_failed") {
        tracking_ready_ = false;
      }
      if (failed_frame_count_ >= options_.max_failed_frames) {
        state_ = "error";
        initialized_ = false;
        tracking_ready_ = false;
      } else if (initialized_) {
        state_ = "degraded";
      }
    }
    publishStatus();
  }

  void workerLoop()
  {
    while (rclcpp::ok()) {
      CloudFrame frame;
      Eigen::Matrix4f initial_guess = Eigen::Matrix4f::Identity();
      bool use_ndt = true;
      {
        std::unique_lock<std::mutex> lock(mutex_);
        condition_.wait(lock, [this]() {
          return stop_worker_ ||
                 (map_loaded_ && initialized_ && latest_cloud_.has_value() &&
                  latest_cloud_->sequence != processed_sequence_ && state_ != "error");
        });
        if (stop_worker_) {
          return;
        }
        frame = latest_cloud_.value();
        processed_sequence_ = frame.sequence;
        initial_guess = last_pose_;
        use_ndt = options_.use_ndt_when_tracking || !tracking_ready_ || failed_frame_count_ > 0;
      }
      const auto started_at = Clock::now();
      RegistrationResult result = registerFrame(frame, initial_guess, use_ndt);
      const double elapsed_sec =
        std::chrono::duration<double>(Clock::now() - started_at).count();
      finishRegistration(frame, result, elapsed_sec);
    }
  }

  RegistrationResult registerFrame(
    const CloudFrame & frame, const Eigen::Matrix4f & initial_guess, const bool use_ndt)
  {
    RegistrationResult result;
    result.source_points = static_cast<int>(frame.cloud->points.size());
    result.raw_source_points = frame.raw_source_points;
    if (!map_cloud_ || map_cloud_->empty() || !frame.cloud || frame.cloud->empty() || !ndt_ ||
      !gicp_)
    {
      return result;
    }

    result = runRegistration(frame, initial_guess, use_ndt);
    if (!result.ok && !use_ndt) {
      result = runRegistration(frame, initial_guess, true);
    }
    return result;
  }

  RegistrationResult runRegistration(
    const CloudFrame & frame, const Eigen::Matrix4f & initial_guess, const bool use_ndt)
  {
    RegistrationResult result;
    result.source_points = static_cast<int>(frame.cloud->points.size());
    result.raw_source_points = frame.raw_source_points;
    Eigen::Matrix4f gicp_guess = initial_guess;
    if (use_ndt) {
      result.used_ndt = true;
      ndt_->setInputSource(frame.cloud);
      CloudT ndt_output;
      ndt_->align(ndt_output, initial_guess);
      result.ndt_converged = ndt_->hasConverged();
      result.ndt_fitness = ndt_->getFitnessScore();
      gicp_guess = ndt_->hasConverged() ? ndt_->getFinalTransformation() : initial_guess;
    }
    if (!matrixFinite(gicp_guess)) {
      gicp_guess = initial_guess;
    }

    CloudT aligned;
    gicp_->setInputSource(frame.cloud);
    gicp_->align(aligned, gicp_guess);
    result.gicp_converged = gicp_->hasConverged();
    result.fitness = gicp_->getFitnessScore();
    result.transform = gicp_->getFinalTransformation();
    result.ok =
      (!result.used_ndt || result.ndt_converged) && result.gicp_converged &&
      matrixFinite(result.transform);
    if (result.ok) {
      const Pose2D pose = poseFromMatrix2D(result.transform);
      result.transform = transform2D(pose.x, pose.y, pose.yaw);
    }
    return result;
  }

  void finishRegistration(
    const CloudFrame & frame, const RegistrationResult & result, const double elapsed_sec)
  {
    if (!result.ok) {
      recordFrameFailure(
        "registration_failed",
        result.used_ndt ? "NDT/GICP did not converge." : "FastVGICP did not converge.");
      return;
    }

    {
      std::lock_guard<std::mutex> lock(mutex_);
      last_pose_ = result.transform;
      last_used_ndt_ = result.used_ndt;
      last_ndt_converged_ = result.ndt_converged;
      last_gicp_converged_ = result.gicp_converged;
      last_ndt_fitness_ = result.ndt_fitness;
      last_fitness_ = result.fitness;
      last_raw_source_points_ = result.raw_source_points;
      last_source_points_ = result.source_points;
      last_cloud_frame_ = frame.cloud_frame;
      failed_frame_count_ = 0;
      tracking_ready_ = true;
      state_ = "localizing";
      last_error_.clear();
      error_detail_.clear();
      if (elapsed_sec > 0.0) {
        frequency_hz_ = 1.0 / elapsed_sec;
      }
    }
    publishPose(result.transform, frame.stamp);
    publishStatus();
  }

  void publishPose(const Eigen::Matrix4f & transform, const rclcpp::Time & stamp)
  {
    const Pose2D pose = poseFromMatrix2D(transform);
    geometry_msgs::msg::PoseStamped msg;
    msg.header.stamp = stamp.nanoseconds() > 0 ? stamp : now();
    msg.header.frame_id = options_.map_frame;
    msg.pose.position.x = pose.x;
    msg.pose.position.y = pose.y;
    msg.pose.position.z = 0.0;
    msg.pose.orientation.x = 0.0;
    msg.pose.orientation.y = 0.0;
    msg.pose.orientation.z = std::sin(pose.yaw / 2.0);
    msg.pose.orientation.w = std::cos(pose.yaw / 2.0);
    pose_pub_->publish(msg);
  }

  void publishStatus()
  {
    std::lock_guard<std::mutex> lock(mutex_);
    publishStatusLocked();
  }

  void publishStatusLocked()
  {
    if (!status_pub_) {
      return;
    }
    std_msgs::msg::String msg;
    msg.data = statusJsonLocked();
    status_pub_->publish(msg);
  }

  void enterErrorLocked(const std::string & code, const std::string & detail, const bool fatal)
  {
    state_ = "error";
    last_error_ = code;
    error_detail_ = detail;
    if (fatal) {
      map_loaded_ = false;
      initialized_ = false;
      tracking_ready_ = false;
    }
  }

  std::string statusJsonLocked() const
  {
    const Pose2D pose = poseFromMatrix2D(last_pose_);
    std::ostringstream out;
    out << "{";
    out << "\"state\":" << jsonString(state_) << ",";
    out << "\"initialized\":" << (initialized_ ? "true" : "false") << ",";
    out << "\"converged\":" << ((state_ == "localizing" && failed_frame_count_ == 0) ? "true" : "false")
        << ",";
    out << "\"lost\":" << ((state_ == "error" && last_error_ == "registration_failed") ? "true" : "false")
        << ",";
    out << "\"mapName\":" << jsonString(options_.map_name) << ",";
    out << "\"mapPath\":" << jsonString(options_.map_path) << ",";
    out << "\"backend\":" << jsonString(options_.registration_backend) << ",";
    out << "\"frameId\":" << jsonString(options_.map_frame) << ",";
    out << "\"baseFrame\":" << jsonString(options_.base_frame) << ",";
    out << "\"cloudFrame\":" << jsonString(last_cloud_frame_) << ",";
    out << "\"rawSourcePoints\":" << last_raw_source_points_ << ",";
    out << "\"sourcePoints\":" << last_source_points_ << ",";
    out << "\"rawMapPoints\":" << raw_map_points_ << ",";
    out << "\"mapPoints\":" << map_points_ << ",";
    out << "\"voxelLeaf\":" << jsonNumber(options_.voxel_leaf) << ",";
    out << "\"trackingReady\":" << (tracking_ready_ ? "true" : "false") << ",";
    out << "\"useNdtWhenTracking\":"
        << (options_.use_ndt_when_tracking ? "true" : "false") << ",";
    out << "\"usedNdt\":" << (last_used_ndt_ ? "true" : "false") << ",";
    out << "\"ndtConverged\":" << (last_ndt_converged_ ? "true" : "false") << ",";
    out << "\"gicpConverged\":" << (last_gicp_converged_ ? "true" : "false") << ",";
    out << "\"ndtFitness\":" << jsonNumber(last_ndt_fitness_) << ",";
    out << "\"fitness\":" << jsonNumber(last_fitness_) << ",";
    out << "\"failedFrameCount\":" << failed_frame_count_ << ",";
    out << "\"maxFailedFrames\":" << options_.max_failed_frames << ",";
    out << "\"frequencyHz\":" << jsonNumber(frequency_hz_) << ",";
    out << "\"lastError\":" << jsonString(last_error_) << ",";
    out << "\"detail\":" << jsonString(error_detail_) << ",";
    out << "\"pose\":{";
    out << "\"x\":" << jsonNumber(pose.x) << ",";
    out << "\"y\":" << jsonNumber(pose.y) << ",";
    out << "\"z\":0,";
    out << "\"yawRad\":" << jsonNumber(pose.yaw) << ",";
    out << "\"yawDeg\":" << jsonNumber(pose.yaw * 180.0 / 3.14159265358979323846);
    out << "},";
    out << "\"stamp\":" << jsonNumber(now().seconds());
    out << "}";
    return out.str();
  }

  LocalizerOptions options_;
  CloudT::Ptr map_cloud_;
  int map_points_ = 0;
  int raw_map_points_ = 0;

#ifdef ROBOT_STATION_USE_FAST_GICP_CUDA
  std::unique_ptr<fast_gicp::NDTCuda<PointT, PointT>> ndt_;
  std::unique_ptr<fast_gicp::FastVGICPCuda<PointT, PointT>> gicp_;
#else
  std::unique_ptr<pcl::NormalDistributionsTransform<PointT, PointT>> ndt_;
  std::unique_ptr<pcl::GeneralizedIterativeClosestPoint<PointT, PointT>> gicp_;
#endif

  std::mutex mutex_;
  std::condition_variable condition_;
  std::thread worker_;
  bool stop_worker_ = false;

  bool map_loaded_ = false;
  bool initialized_ = false;
  bool tracking_ready_ = false;
  std::optional<CloudFrame> latest_cloud_;
  std::uint64_t cloud_sequence_ = 0;
  std::uint64_t processed_sequence_ = 0;
  Eigen::Matrix4f last_pose_ = Eigen::Matrix4f::Identity();

  std::string state_ = "starting";
  std::string last_error_;
  std::string error_detail_;
  std::string last_cloud_frame_;
  int last_raw_source_points_ = 0;
  int last_source_points_ = 0;
  int failed_frame_count_ = 0;
  bool last_used_ndt_ = false;
  bool last_ndt_converged_ = false;
  bool last_gicp_converged_ = false;
  double last_ndt_fitness_ = std::numeric_limits<double>::quiet_NaN();
  double last_fitness_ = std::numeric_limits<double>::quiet_NaN();
  double frequency_hz_ = std::numeric_limits<double>::quiet_NaN();

  tf2_ros::Buffer tf_buffer_;
  tf2_ros::TransformListener tf_listener_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr cloud_sub_;
  rclcpp::Subscription<geometry_msgs::msg::PoseWithCovarianceStamped>::SharedPtr initial_pose_sub_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_pub_;
  rclcpp::TimerBase::SharedPtr heartbeat_timer_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<LocalizerNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
