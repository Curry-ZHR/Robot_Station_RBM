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
#include <nav_msgs/msg/odometry.hpp>
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
#include <vector>

namespace fs = std::filesystem;
using PointT = pcl::PointXYZI;
using CloudT = pcl::PointCloud<PointT>;
using Clock = std::chrono::steady_clock;

#ifdef ROBOT_STATION_USE_FAST_GICP_CUDA
constexpr const char * kRegistrationBackend = "gpu";
constexpr bool kUseNdtWhenTracking = true;
#else
constexpr const char * kRegistrationBackend = "cpu";
constexpr bool kUseNdtWhenTracking = true;
#endif

struct LocalizerOptions
{
  std::string map_path;
  std::string map_name;
  std::string cloud_topic = "/rslidar_points";
  std::string odom_topic = "/odom";
  std::string initial_pose_topic = "/initialpose";
  std::string pose_topic = "/localization/pose";
  std::string status_topic = "/localization/status";
  std::string map_frame = "map";
  std::string base_frame = "base_link";
  int max_failed_frames = 15;
  bool recovery_search_enabled = true;
  int recovery_after_failed_frames = 7;
  int recovery_confirm_frames = 2;
  int recovery_max_candidates_per_frame = 48;
  int recovery_wide_every_n_frames = 3;
  bool recovery_near_gicp_only_enabled = true;
  double recovery_near_radius_m = 0.8;
  double recovery_near_xy_step_m = 0.2;
  double recovery_near_yaw_step_deg = 10.0;
  double recovery_far_radius_m = 2.0;
  double recovery_far_radius_step_m = 0.25;
  double recovery_far_yaw_step_deg = 15.0;
  int recovery_far_angle_count = 8;
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
  bool use_odom_retry = true;
  double odom_max_age_sec = 1.0;
  double heartbeat_sec = 1.0;
  double max_pose_jump_m = 0.35;
  double max_pose_jump_yaw_deg = 20.0;
  double odom_translation_margin_m = 0.12;
  double odom_yaw_margin_deg = 8.0;
  double odom_delta_scale = 3.0;
  double fitness_max_abs = 0.03;
  double fitness_degrade_ratio = 6.0;
  double fitness_degrade_abs = 0.08;
  double recovery_fitness_ratio = 1.8;
  double recovery_fitness_abs = 0.05;
  std::string registration_backend = kRegistrationBackend;
};

struct Pose2D
{
  double x = 0.0;
  double y = 0.0;
  double yaw = 0.0;
};

struct OdomFrame
{
  Pose2D pose;
  rclcpp::Time stamp;
  Clock::time_point received_at;
};

struct CloudFrame
{
  CloudT::Ptr cloud;
  std::string cloud_frame;
  rclcpp::Time stamp;
  std::uint64_t sequence = 0;
  int raw_source_points = 0;
  std::optional<OdomFrame> odom;
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
  bool used_odom_retry = false;
  bool odom_retry_failed = false;
  bool used_recovery_search = false;
  std::string recovery_stage;
  int recovery_candidate_count = 0;
  bool recovery_center_last_pose = false;
  bool recovery_cursor_valid = false;
  std::size_t recovery_next_cursor = 0;
  Eigen::Matrix4f transform = Eigen::Matrix4f::Identity();
};

struct RecoveryGuess
{
  Eigen::Matrix4f transform = Eigen::Matrix4f::Identity();
  bool use_ndt = true;
  std::string mode = "ndt_gicp";
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

bool poseFinite(const Pose2D & pose)
{
  return std::isfinite(pose.x) && std::isfinite(pose.y) && std::isfinite(pose.yaw);
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
    tf_listener_(tf_buffer_, this, true)
  {
    declareParameters();
    readParameters();

    pose_pub_ = create_publisher<geometry_msgs::msg::PoseStamped>(options_.pose_topic, 10);
    status_pub_ = create_publisher<std_msgs::msg::String>(options_.status_topic, 10);
    cloud_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      options_.cloud_topic, rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::PointCloud2::ConstSharedPtr msg) { onCloud(msg); });
    if (options_.use_odom_retry && !options_.odom_topic.empty()) {
      odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
        options_.odom_topic, rclcpp::QoS(rclcpp::KeepLast(50)).best_effort(),
        [this](nav_msgs::msg::Odometry::ConstSharedPtr msg) { onOdom(msg); });
    }
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
    declare_parameter<std::string>("odom_topic", options_.odom_topic);
    declare_parameter<std::string>("initial_pose_topic", options_.initial_pose_topic);
    declare_parameter<std::string>("pose_topic", options_.pose_topic);
    declare_parameter<std::string>("status_topic", options_.status_topic);
    declare_parameter<std::string>("map_frame", options_.map_frame);
    declare_parameter<std::string>("base_frame", options_.base_frame);
    declare_parameter<int>("max_failed_frames", options_.max_failed_frames);
    declare_parameter<bool>("recovery_search_enabled", options_.recovery_search_enabled);
    declare_parameter<int>("recovery_after_failed_frames", options_.recovery_after_failed_frames);
    declare_parameter<int>("recovery_confirm_frames", options_.recovery_confirm_frames);
    declare_parameter<int>(
      "recovery_max_candidates_per_frame", options_.recovery_max_candidates_per_frame);
    declare_parameter<int>("recovery_wide_every_n_frames", options_.recovery_wide_every_n_frames);
    declare_parameter<bool>(
      "recovery_near_gicp_only_enabled", options_.recovery_near_gicp_only_enabled);
    declare_parameter<double>("recovery_near_radius_m", options_.recovery_near_radius_m);
    declare_parameter<double>("recovery_near_xy_step_m", options_.recovery_near_xy_step_m);
    declare_parameter<double>(
      "recovery_near_yaw_step_deg", options_.recovery_near_yaw_step_deg);
    declare_parameter<double>("recovery_far_radius_m", options_.recovery_far_radius_m);
    declare_parameter<double>("recovery_far_radius_step_m", options_.recovery_far_radius_step_m);
    declare_parameter<double>("recovery_far_yaw_step_deg", options_.recovery_far_yaw_step_deg);
    declare_parameter<int>("recovery_far_angle_count", options_.recovery_far_angle_count);
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
    declare_parameter<bool>("use_odom_retry", options_.use_odom_retry);
    declare_parameter<double>("odom_max_age_sec", options_.odom_max_age_sec);
    declare_parameter<double>("heartbeat_sec", options_.heartbeat_sec);
    declare_parameter<double>("max_pose_jump_m", options_.max_pose_jump_m);
    declare_parameter<double>("max_pose_jump_yaw_deg", options_.max_pose_jump_yaw_deg);
    declare_parameter<double>(
      "odom_translation_margin_m", options_.odom_translation_margin_m);
    declare_parameter<double>("odom_yaw_margin_deg", options_.odom_yaw_margin_deg);
    declare_parameter<double>("odom_delta_scale", options_.odom_delta_scale);
    declare_parameter<double>("fitness_max_abs", options_.fitness_max_abs);
    declare_parameter<double>("fitness_degrade_ratio", options_.fitness_degrade_ratio);
    declare_parameter<double>("fitness_degrade_abs", options_.fitness_degrade_abs);
    declare_parameter<double>("recovery_fitness_ratio", options_.recovery_fitness_ratio);
    declare_parameter<double>("recovery_fitness_abs", options_.recovery_fitness_abs);
  }

  void readParameters()
  {
    options_.map_path = get_parameter("map_path").as_string();
    options_.map_name = get_parameter("map_name").as_string();
    options_.cloud_topic = get_parameter("cloud_topic").as_string();
    options_.odom_topic = get_parameter("odom_topic").as_string();
    options_.initial_pose_topic = get_parameter("initial_pose_topic").as_string();
    options_.pose_topic = get_parameter("pose_topic").as_string();
    options_.status_topic = get_parameter("status_topic").as_string();
    options_.map_frame = normalizeFrame(get_parameter("map_frame").as_string());
    options_.base_frame = normalizeFrame(get_parameter("base_frame").as_string());
    options_.max_failed_frames =
      std::max(1, static_cast<int>(get_parameter("max_failed_frames").as_int()));
    options_.recovery_search_enabled = get_parameter("recovery_search_enabled").as_bool();
    options_.recovery_after_failed_frames =
      std::max(1, static_cast<int>(get_parameter("recovery_after_failed_frames").as_int()));
    options_.recovery_confirm_frames =
      std::max(1, static_cast<int>(get_parameter("recovery_confirm_frames").as_int()));
    options_.recovery_max_candidates_per_frame = std::max(
      1, static_cast<int>(get_parameter("recovery_max_candidates_per_frame").as_int()));
    options_.recovery_wide_every_n_frames =
      std::max(1, static_cast<int>(get_parameter("recovery_wide_every_n_frames").as_int()));
    options_.recovery_near_gicp_only_enabled =
      get_parameter("recovery_near_gicp_only_enabled").as_bool();
    options_.recovery_near_radius_m =
      std::max(0.0, get_parameter("recovery_near_radius_m").as_double());
    options_.recovery_near_xy_step_m =
      std::max(0.02, get_parameter("recovery_near_xy_step_m").as_double());
    options_.recovery_near_yaw_step_deg =
      std::max(1.0, get_parameter("recovery_near_yaw_step_deg").as_double());
    options_.recovery_far_radius_m =
      std::max(0.0, get_parameter("recovery_far_radius_m").as_double());
    options_.recovery_far_radius_step_m =
      std::max(0.05, get_parameter("recovery_far_radius_step_m").as_double());
    options_.recovery_far_yaw_step_deg =
      std::max(1.0, get_parameter("recovery_far_yaw_step_deg").as_double());
    options_.recovery_far_angle_count =
      std::max(1, static_cast<int>(get_parameter("recovery_far_angle_count").as_int()));
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
    options_.use_odom_retry = get_parameter("use_odom_retry").as_bool();
    options_.odom_max_age_sec = std::max(0.05, get_parameter("odom_max_age_sec").as_double());
    options_.heartbeat_sec = std::max(0.1, get_parameter("heartbeat_sec").as_double());
    options_.max_pose_jump_m = std::max(0.01, get_parameter("max_pose_jump_m").as_double());
    options_.max_pose_jump_yaw_deg =
      std::max(0.1, get_parameter("max_pose_jump_yaw_deg").as_double());
    options_.odom_translation_margin_m =
      std::max(0.0, get_parameter("odom_translation_margin_m").as_double());
    options_.odom_yaw_margin_deg =
      std::max(0.0, get_parameter("odom_yaw_margin_deg").as_double());
    options_.odom_delta_scale = std::max(0.0, get_parameter("odom_delta_scale").as_double());
    options_.fitness_max_abs =
      std::max(0.0, get_parameter("fitness_max_abs").as_double());
    options_.fitness_degrade_ratio =
      std::max(1.0, get_parameter("fitness_degrade_ratio").as_double());
    options_.fitness_degrade_abs =
      std::max(0.0, get_parameter("fitness_degrade_abs").as_double());
    options_.recovery_fitness_ratio =
      std::max(1.0, get_parameter("recovery_fitness_ratio").as_double());
    options_.recovery_fitness_abs =
      std::max(0.0, get_parameter("recovery_fitness_abs").as_double());
  }

  void loadMap()
  {
    std::lock_guard<std::mutex> lock(mutex_);
    state_ = "starting";
    resetRecoveryLocked();
    consecutive_odom_retry_failures_ = 0;
    recovery_sweep_cursor_ = 0;
    recovery_sweep_last_pose_center_ = true;
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
    {
      std::lock_guard<std::mutex> lock(mutex_);
      if (!initialized_) {
        return;
      }
    }

    sensor_msgs::msg::PointCloud2 working = *msg;
    const std::string source_frame = normalizeFrame(msg->header.frame_id);
    const bool wants_transform =
      !options_.base_frame.empty() && !source_frame.empty() && source_frame != options_.base_frame;
    const auto tf_lookup_timeout = tf2::durationFromSec(0.2);

    if (wants_transform) {
      try {
        auto transform = tf_buffer_.lookupTransform(
          options_.base_frame, source_frame, tf2_ros::fromMsg(msg->header.stamp),
          tf_lookup_timeout);
        tf2::doTransform(*msg, working, transform);
      } catch (const std::exception &) {
        try {
          auto transform = tf_buffer_.lookupTransform(
            options_.base_frame, source_frame, tf2::TimePointZero, tf_lookup_timeout);
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

  void onOdom(const nav_msgs::msg::Odometry::ConstSharedPtr msg)
  {
    const Pose2D pose = poseFromOdom(*msg);
    if (!poseFinite(pose)) {
      return;
    }
    std::lock_guard<std::mutex> lock(mutex_);
    latest_odom_ = OdomFrame{pose, rclcpp::Time(msg->header.stamp), Clock::now()};
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
      last_success_odom_ = latestOdomLocked();
      initialized_ = true;
      tracking_ready_ = false;
      failed_frame_count_ = 0;
      resetRecoveryLocked();
      consecutive_odom_retry_failures_ = 0;
      recovery_sweep_cursor_ = 0;
      recovery_sweep_last_pose_center_ = true;
      processed_sequence_ = 0;
      last_used_ndt_ = false;
      last_ndt_converged_ = false;
      last_gicp_converged_ = false;
      last_used_odom_retry_ = false;
      last_used_recovery_search_ = false;
      last_recovery_stage_.clear();
      last_recovery_candidate_count_ = 0;
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
      recordFrameFailureLocked(code, detail);
    }
    publishStatus();
  }

  void recordFrameFailureLocked(const std::string & code, const std::string & detail)
  {
    if (!initialized_) {
      if (map_loaded_ && state_ != "error") {
        state_ = "waiting_initial_pose";
      }
      return;
    }
    ++failed_frame_count_;
    last_error_ = code;
    error_detail_ = detail;
    if (code == "registration_failed" || code == "registration_rejected") {
      resetRecoveryLocked();
      tracking_ready_ = false;
    }
    if (code == "recovery_rejected") {
      resetRecoveryLocked();
      tracking_ready_ = false;
    }
    if (failed_frame_count_ >= options_.max_failed_frames) {
      state_ = "lost";
      tracking_ready_ = false;
    } else {
      state_ = "degraded";
    }
  }

  void workerLoop()
  {
    while (rclcpp::ok()) {
      CloudFrame frame;
      Eigen::Matrix4f initial_guess = Eigen::Matrix4f::Identity();
      std::optional<Eigen::Matrix4f> odom_retry_guess;
      bool use_ndt = true;
      bool confirming_recovery = false;
      int failed_frame_count = 0;
      int odom_retry_failure_count = 0;
      std::size_t recovery_sweep_cursor = 0;
      bool recovery_sweep_last_pose_center = true;
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
        frame.odom = latestOdomLocked();
        processed_sequence_ = frame.sequence;
        confirming_recovery = pending_recovery_pose_.has_value() && recovery_confirm_count_ > 0;
        initial_guess = confirming_recovery ? pending_recovery_pose_.value() : last_pose_;
        failed_frame_count = failed_frame_count_;
        odom_retry_failure_count = consecutive_odom_retry_failures_;
        recovery_sweep_cursor = recovery_sweep_cursor_;
        recovery_sweep_last_pose_center = recovery_sweep_last_pose_center_;
        odom_retry_guess =
          (confirming_recovery || odomRetrySuppressedLocked())
            ? std::nullopt
            : odomRetryGuessLocked(frame.odom);
        use_ndt =
          confirming_recovery || options_.use_ndt_when_tracking || !tracking_ready_ ||
          failed_frame_count_ > 0;
      }
      const auto started_at = Clock::now();
      RegistrationResult result = registerFrame(
        frame, initial_guess, odom_retry_guess, use_ndt, confirming_recovery, failed_frame_count,
        odom_retry_failure_count, recovery_sweep_cursor, recovery_sweep_last_pose_center);
      const double elapsed_sec =
        std::chrono::duration<double>(Clock::now() - started_at).count();
      finishRegistration(frame, result, elapsed_sec, confirming_recovery);
    }
  }

  RegistrationResult registerFrame(
    const CloudFrame & frame, const Eigen::Matrix4f & initial_guess,
    const std::optional<Eigen::Matrix4f> & odom_retry_guess, const bool use_ndt,
    const bool confirming_recovery, const int failed_frame_count,
    const int odom_retry_failure_count, const std::size_t recovery_sweep_cursor,
    const bool recovery_sweep_last_pose_center)
  {
    RegistrationResult result;
    result.source_points = static_cast<int>(frame.cloud->points.size());
    result.raw_source_points = frame.raw_source_points;
    if (!map_cloud_ || map_cloud_->empty() || !frame.cloud || frame.cloud->empty() || !ndt_ ||
      !gicp_)
    {
      return result;
    }
    if (confirming_recovery) {
      result = runRegistration(frame, initial_guess, true);
      result.used_recovery_search = result.ok;
      result.recovery_stage = "confirm";
      result.recovery_candidate_count = 1;
      return result;
    }

    result = runRegistration(frame, initial_guess, use_ndt);
    if (!result.ok && !use_ndt) {
      result = runRegistration(frame, initial_guess, true);
    }
    int odom_retry_failures_after_attempt = odom_retry_failure_count;
    if (!result.ok && odom_retry_guess.has_value()) {
      RegistrationResult odom_retry = runRegistration(frame, odom_retry_guess.value(), true);
      odom_retry.used_odom_retry = true;
      if (odom_retry.ok) {
        return odom_retry;
      }
      odom_retry.odom_retry_failed = true;
      odom_retry_failures_after_attempt = odom_retry_failure_count + 1;
      result = odom_retry;
    }
    if (recoverySearchDue(failed_frame_count, odom_retry_failures_after_attempt)) {
      const bool odom_retry_exhausted =
        odom_retry_failures_after_attempt >= options_.recovery_after_failed_frames;
      const bool last_pose_center = odom_retry_exhausted || !odom_retry_guess.has_value();
      const std::size_t search_cursor =
        (last_pose_center == recovery_sweep_last_pose_center) ? recovery_sweep_cursor : 0;
      const Eigen::Matrix4f center =
        last_pose_center ? initial_guess : odom_retry_guess.value();
      RegistrationResult recovery =
        runRecoverySearch(frame, center, search_cursor, last_pose_center);
      recovery.odom_retry_failed = result.odom_retry_failed;
      return recovery;
    }
    return result;
  }

  bool recoverySearchDue(
    const int failed_frame_count, const int odom_retry_failure_count) const
  {
    return options_.recovery_search_enabled &&
           (failed_frame_count >= options_.recovery_after_failed_frames ||
            odom_retry_failure_count >= options_.recovery_after_failed_frames);
  }

  std::vector<double> recoveryYawSweepOffsets(const double step_deg) const
  {
    constexpr double pi = 3.14159265358979323846;
    const int step = std::max(1, std::min(180, static_cast<int>(std::round(step_deg))));
    std::vector<double> offsets;
    offsets.reserve(static_cast<std::size_t>(360 / step + 1));
    offsets.push_back(0.0);
    for (int degrees = step; degrees < 180; degrees += step) {
      const double radians = static_cast<double>(degrees) * pi / 180.0;
      offsets.push_back(radians);
      offsets.push_back(-radians);
    }
    offsets.push_back(pi);
    return offsets;
  }

  std::vector<RecoveryGuess> interleaveRecoveryGuesses(
    const std::vector<RecoveryGuess> & near_guesses,
    const std::vector<RecoveryGuess> & far_guesses) const
  {
    std::vector<RecoveryGuess> merged;
    merged.reserve(near_guesses.size() + far_guesses.size());
    std::size_t near_index = 0;
    std::size_t far_index = 0;
    while (near_index < near_guesses.size() || far_index < far_guesses.size()) {
      for (int count = 0; count < 2 && near_index < near_guesses.size(); ++count) {
        merged.push_back(near_guesses[near_index++]);
      }
      if (far_index < far_guesses.size()) {
        merged.push_back(far_guesses[far_index++]);
      }
    }
    return merged;
  }

  std::vector<RecoveryGuess> recoverySweepGuesses(
    const Eigen::Matrix4f & center, const std::size_t cursor, int & total_candidates,
    std::size_t & next_cursor) const
  {
    constexpr double pi = 3.14159265358979323846;
    std::vector<RecoveryGuess> near_guesses;
    std::vector<RecoveryGuess> far_guesses;

    if (options_.recovery_near_gicp_only_enabled && options_.recovery_near_radius_m > 0.0) {
      const std::vector<double> yaw_offsets =
        recoveryYawSweepOffsets(options_.recovery_near_yaw_step_deg);
      std::vector<std::pair<double, double>> xy_offsets;
      const int max_step =
        static_cast<int>(std::ceil(options_.recovery_near_radius_m / options_.recovery_near_xy_step_m));
      for (int ix = -max_step; ix <= max_step; ++ix) {
        const double x = static_cast<double>(ix) * options_.recovery_near_xy_step_m;
        for (int iy = -max_step; iy <= max_step; ++iy) {
          const double y = static_cast<double>(iy) * options_.recovery_near_xy_step_m;
          if (std::hypot(x, y) <= options_.recovery_near_radius_m + 1e-6) {
            xy_offsets.emplace_back(x, y);
          }
        }
      }
      std::sort(xy_offsets.begin(), xy_offsets.end(), [](const auto & lhs, const auto & rhs) {
        const double lhs_radius = std::hypot(lhs.first, lhs.second);
        const double rhs_radius = std::hypot(rhs.first, rhs.second);
        if (std::abs(lhs_radius - rhs_radius) > 1e-9) {
          return lhs_radius < rhs_radius;
        }
        return std::atan2(lhs.second, lhs.first) < std::atan2(rhs.second, rhs.first);
      });
      near_guesses.reserve(xy_offsets.size() * yaw_offsets.size());
      for (const auto & offset : xy_offsets) {
        for (const double yaw_offset : yaw_offsets) {
          near_guesses.push_back(
            RecoveryGuess{center * transform2D(offset.first, offset.second, yaw_offset), false,
              "gicp_only_near"});
        }
      }
    }

    const double far_radius_max =
      std::max(options_.recovery_far_radius_m, options_.recovery_near_radius_m);
    if (far_radius_max > 0.0) {
      const std::vector<double> yaw_offsets =
        recoveryYawSweepOffsets(options_.recovery_far_yaw_step_deg);
      for (const double yaw_offset : yaw_offsets) {
        far_guesses.push_back(
          RecoveryGuess{center * transform2D(0.0, 0.0, yaw_offset), true, "ndt_gicp_far"});
      }
      const double far_start =
        options_.recovery_near_gicp_only_enabled
          ? options_.recovery_near_radius_m + options_.recovery_far_radius_step_m
          : options_.recovery_far_radius_step_m;
      for (double radius = far_start; radius <= far_radius_max + 1e-6;
        radius += options_.recovery_far_radius_step_m)
      {
        for (const double yaw_offset : yaw_offsets) {
          for (int index = 0; index < options_.recovery_far_angle_count; ++index) {
            const double angle =
              static_cast<double>(index) * 2.0 * pi /
              static_cast<double>(options_.recovery_far_angle_count);
            far_guesses.push_back(
              RecoveryGuess{
                center * transform2D(radius * std::cos(angle), radius * std::sin(angle), yaw_offset),
                true, "ndt_gicp_far"});
          }
        }
      }
    }

    std::vector<RecoveryGuess> all = interleaveRecoveryGuesses(near_guesses, far_guesses);

    total_candidates = static_cast<int>(all.size());
    if (all.empty()) {
      next_cursor = 0;
      return {};
    }

    const std::size_t max_candidates =
      static_cast<std::size_t>(options_.recovery_max_candidates_per_frame);
    if (all.size() <= max_candidates) {
      next_cursor = 0;
      return all;
    }

    std::vector<RecoveryGuess> selected;
    selected.reserve(max_candidates);
    const std::size_t start = cursor % all.size();
    for (std::size_t index = 0; index < max_candidates; ++index) {
      selected.push_back(all[(start + index) % all.size()]);
    }
    next_cursor = (start + max_candidates) % all.size();
    return selected;
  }

  std::vector<Eigen::Matrix4f> recoveryRefineGuesses(const Eigen::Matrix4f & center) const
  {
    constexpr double pi = 3.14159265358979323846;
    const std::vector<std::pair<double, double>> offsets = {
      {0.0, 0.0}, {0.15, 0.0}, {-0.15, 0.0}, {0.0, 0.15}, {0.0, -0.15},
      {0.15, 0.15}, {0.15, -0.15}, {-0.15, 0.15}, {-0.15, -0.15}};
    const std::vector<double> yaw_offsets = {
      0.0, 5.0 * pi / 180.0, -5.0 * pi / 180.0, 10.0 * pi / 180.0,
      -10.0 * pi / 180.0};
    std::vector<Eigen::Matrix4f> guesses;
    guesses.reserve(offsets.size() * yaw_offsets.size());
    for (const auto & offset : offsets) {
      for (const double yaw_offset : yaw_offsets) {
        guesses.push_back(center * transform2D(offset.first, offset.second, yaw_offset));
      }
    }
    return guesses;
  }

  bool betterRegistration(
    const RegistrationResult & candidate, const RegistrationResult & current_best) const
  {
    if (!candidate.ok) {
      return false;
    }
    if (!current_best.ok) {
      return true;
    }
    const bool candidate_finite = std::isfinite(candidate.fitness);
    const bool best_finite = std::isfinite(current_best.fitness);
    if (candidate_finite && best_finite) {
      return candidate.fitness < current_best.fitness;
    }
    return candidate_finite && !best_finite;
  }

  RegistrationResult runRecoverySearch(
    const CloudFrame & frame, const Eigen::Matrix4f & center,
    const std::size_t recovery_sweep_cursor, const bool last_pose_center)
  {
    constexpr double rad_to_deg = 180.0 / 3.14159265358979323846;
    int total_candidates = 0;
    std::size_t next_cursor = 0;
    auto guesses =
      recoverySweepGuesses(center, recovery_sweep_cursor, total_candidates, next_cursor);
    std::string stage = last_pose_center ? "sweep_last_pose_hybrid" : "sweep_odom_hybrid";
    if (total_candidates > static_cast<int>(guesses.size())) {
      stage += "_batch";
    }

    RegistrationResult best;
    best.source_points = static_cast<int>(frame.cloud->points.size());
    best.raw_source_points = frame.raw_source_points;
    best.used_recovery_search = true;
    best.recovery_stage = stage;
    best.recovery_center_last_pose = last_pose_center;
    best.recovery_cursor_valid = true;
    best.recovery_next_cursor = next_cursor;
    const Pose2D center_pose = poseFromMatrix2D(center);
    RCLCPP_INFO(
      get_logger(),
      "Recovery search start: stage=%s frame_sequence=%lu center=(x=%.3f y=%.3f yaw=%.1fdeg) "
      "cursor=%zu next_cursor=%zu batch_candidates=%zu total_candidates=%d",
      stage.c_str(), static_cast<unsigned long>(frame.sequence), center_pose.x, center_pose.y,
      center_pose.yaw * rad_to_deg, recovery_sweep_cursor, next_cursor, guesses.size(),
      total_candidates);
    int tested_candidates = 0;
    for (const auto & guess : guesses) {
      const Pose2D guess_pose = poseFromMatrix2D(guess.transform);
      RCLCPP_INFO(
        get_logger(),
        "Recovery search guess: stage=%s mode=%s index=%d/%zu x=%.3f y=%.3f yaw=%.1fdeg",
        stage.c_str(), guess.mode.c_str(), tested_candidates + 1, guesses.size(), guess_pose.x,
        guess_pose.y, guess_pose.yaw * rad_to_deg);
      RegistrationResult candidate = runRegistration(frame, guess.transform, guess.use_ndt);
      ++tested_candidates;
      const Pose2D candidate_pose = poseFromMatrix2D(candidate.transform);
      RCLCPP_INFO(
        get_logger(),
        "Recovery search result: stage=%s mode=%s index=%d/%zu ok=%s ndt=%s gicp=%s fitness=%.6f "
        "final=(x=%.3f y=%.3f yaw=%.1fdeg)",
        stage.c_str(), guess.mode.c_str(), tested_candidates, guesses.size(),
        candidate.ok ? "true" : "false", candidate.ndt_converged ? "true" : "false",
        candidate.gicp_converged ? "true" : "false", candidate.fitness, candidate_pose.x,
        candidate_pose.y, candidate_pose.yaw * rad_to_deg);
      if (betterRegistration(candidate, best)) {
        best = candidate;
      }
    }

    if (!best.ok) {
      best.recovery_candidate_count = tested_candidates;
      return best;
    }

    int refine_candidates = 0;
    for (const auto & guess : recoveryRefineGuesses(best.transform)) {
      const Pose2D guess_pose = poseFromMatrix2D(guess);
      RCLCPP_INFO(
        get_logger(),
        "Recovery refine guess: stage=%s mode=gicp_only_refine index=%d x=%.3f y=%.3f yaw=%.1fdeg",
        stage.c_str(), refine_candidates + 1, guess_pose.x, guess_pose.y,
        guess_pose.yaw * rad_to_deg);
      RegistrationResult refined = runRegistration(frame, guess, false);
      ++refine_candidates;
      const Pose2D refined_pose = poseFromMatrix2D(refined.transform);
      RCLCPP_INFO(
        get_logger(),
        "Recovery refine result: stage=%s mode=gicp_only_refine index=%d ok=%s ndt=%s gicp=%s fitness=%.6f "
        "final=(x=%.3f y=%.3f yaw=%.1fdeg)",
        stage.c_str(), refine_candidates, refined.ok ? "true" : "false",
        refined.ndt_converged ? "true" : "false", refined.gicp_converged ? "true" : "false",
        refined.fitness, refined_pose.x, refined_pose.y, refined_pose.yaw * rad_to_deg);
      if (betterRegistration(refined, best)) {
        best = refined;
      }
    }

    best.used_recovery_search = true;
    best.recovery_stage = stage + "+refine";
    best.recovery_candidate_count = tested_candidates + refine_candidates;
    best.recovery_center_last_pose = last_pose_center;
    best.recovery_cursor_valid = true;
    best.recovery_next_cursor = next_cursor;
    return best;
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
    const CloudFrame & frame, const RegistrationResult & result, const double elapsed_sec,
    const bool confirming_recovery)
  {
    if (!result.ok) {
      {
        std::lock_guard<std::mutex> lock(mutex_);
        updateRecoveryProgressLocked(result);
        if (confirming_recovery) {
          resetRecoveryLocked();
        }
      }
        const std::string detail =
          result.used_recovery_search
          ? "Recovery sweep did not converge."
          : (result.used_odom_retry
               ? "Odom retry NDT/GICP did not converge."
               : (confirming_recovery
                    ? "Recovery confirmation NDT/GICP did not converge."
                    : (result.used_ndt ? "NDT/GICP did not converge."
                                       : "FastVGICP did not converge.")));
      recordFrameFailure(
        "registration_failed",
        detail);
      return;
    }

    bool should_publish_pose = false;
    {
      std::lock_guard<std::mutex> lock(mutex_);
      std::string rejection_detail;
      updateRecoveryProgressLocked(result);
      const bool recovery_result = confirming_recovery || result.used_recovery_search;
      if (!acceptRegistrationLocked(frame, result, rejection_detail, recovery_result)) {
        RCLCPP_WARN(
          get_logger(), "Registration rejected: recovery=%s detail=%s",
          recovery_result ? "true" : "false", rejection_detail.c_str());
        if (recovery_result) {
          resetRecoveryLocked();
        }
        recordFrameFailureLocked("registration_rejected", rejection_detail);
        publishStatusLocked();
        return;
      }

      if (recovery_result) {
        if (!acceptRecoveryFitnessLocked(result, rejection_detail)) {
          RCLCPP_WARN(
            get_logger(), "Recovery rejected: fitness=%.6f last_fitness=%.6f detail=%s",
            result.fitness, last_fitness_, rejection_detail.c_str());
          resetRecoveryLocked();
          recordFrameFailureLocked("recovery_rejected", rejection_detail);
          publishStatusLocked();
          return;
        }
        pending_recovery_pose_ = result.transform;
        pending_recovery_fitness_ = result.fitness;
        recovery_confirm_count_ = confirming_recovery ? recovery_confirm_count_ + 1 : 1;
        state_ = "recovering";
        tracking_ready_ = false;
        last_used_ndt_ = result.used_ndt;
        last_ndt_converged_ = result.ndt_converged;
        last_gicp_converged_ = result.gicp_converged;
        last_raw_source_points_ = result.raw_source_points;
        last_source_points_ = result.source_points;
        last_cloud_frame_ = frame.cloud_frame;
        last_used_odom_retry_ = result.used_odom_retry || result.odom_retry_failed;
        last_used_recovery_search_ = true;
        last_recovery_stage_ = result.recovery_stage;
        last_recovery_candidate_count_ = result.recovery_candidate_count;
        last_error_.clear();
        error_detail_ = "Recovery candidate awaiting confirmation.";
        if (elapsed_sec > 0.0) {
          frequency_hz_ = 1.0 / elapsed_sec;
        }
        const Pose2D recovery_pose = poseFromMatrix2D(result.transform);
        if (recovery_confirm_count_ < options_.recovery_confirm_frames) {
          RCLCPP_INFO(
            get_logger(),
            "Recovery candidate accepted pending confirmation: count=%d/%d fitness=%.6f "
            "last_fitness=%.6f pose=(x=%.3f y=%.3f yaw=%.1fdeg)",
            recovery_confirm_count_, options_.recovery_confirm_frames, result.fitness,
            last_fitness_, recovery_pose.x, recovery_pose.y,
            recovery_pose.yaw * 180.0 / 3.14159265358979323846);
          publishStatusLocked();
          return;
        }
        RCLCPP_INFO(
          get_logger(),
          "Recovery confirmed: count=%d/%d fitness=%.6f last_fitness=%.6f pose=(x=%.3f "
          "y=%.3f yaw=%.1fdeg)",
          recovery_confirm_count_, options_.recovery_confirm_frames, result.fitness, last_fitness_,
          recovery_pose.x, recovery_pose.y,
          recovery_pose.yaw * 180.0 / 3.14159265358979323846);
      }
      applySuccessfulRegistrationLocked(frame, result, elapsed_sec);
      should_publish_pose = true;
    }

    if (should_publish_pose) {
      publishPose(result.transform, frame.stamp);
      publishStatus();
    }
  }

  void applySuccessfulRegistrationLocked(
    const CloudFrame & frame, const RegistrationResult & result, const double elapsed_sec)
  {
    last_pose_ = result.transform;
    last_used_ndt_ = result.used_ndt;
    last_ndt_converged_ = result.ndt_converged;
    last_gicp_converged_ = result.gicp_converged;
    last_ndt_fitness_ = result.ndt_fitness;
    last_fitness_ = result.fitness;
    last_raw_source_points_ = result.raw_source_points;
    last_source_points_ = result.source_points;
    last_cloud_frame_ = frame.cloud_frame;
    last_success_odom_ = frame.odom;
    failed_frame_count_ = 0;
    tracking_ready_ = true;
    state_ = "localizing";
    last_used_odom_retry_ = result.used_odom_retry;
    last_used_recovery_search_ = result.used_recovery_search;
    last_recovery_stage_ = result.recovery_stage;
    last_recovery_candidate_count_ = result.recovery_candidate_count;
    consecutive_odom_retry_failures_ = 0;
    recovery_sweep_cursor_ = 0;
    recovery_sweep_last_pose_center_ = true;
    resetRecoveryLocked();
    last_error_.clear();
    error_detail_.clear();
    if (elapsed_sec > 0.0) {
      frequency_hz_ = 1.0 / elapsed_sec;
    }
  }

  void resetRecoveryLocked()
  {
    pending_recovery_pose_.reset();
    pending_recovery_fitness_ = std::numeric_limits<double>::quiet_NaN();
    recovery_confirm_count_ = 0;
  }

  void updateRecoveryProgressLocked(const RegistrationResult & result)
  {
    if (result.odom_retry_failed) {
      ++consecutive_odom_retry_failures_;
    }
    if (result.recovery_cursor_valid) {
      recovery_sweep_cursor_ = result.recovery_next_cursor;
      recovery_sweep_last_pose_center_ = result.recovery_center_last_pose;
    }
    if (result.used_odom_retry || result.odom_retry_failed) {
      last_used_odom_retry_ = true;
    }
    if (result.used_recovery_search) {
      last_used_recovery_search_ = true;
      last_recovery_stage_ = result.recovery_stage;
      last_recovery_candidate_count_ = result.recovery_candidate_count;
    }
  }

  bool acceptRecoveryFitnessLocked(
    const RegistrationResult & result, std::string & detail) const
  {
    if (!acceptAbsoluteFitnessLocked(result, "recovery candidate", detail)) {
      return false;
    }
    if (!std::isfinite(last_fitness_)) {
      return true;
    }
    const double ratio_limit = last_fitness_ * options_.recovery_fitness_ratio;
    const double absolute_limit = last_fitness_ + options_.recovery_fitness_abs;
    const double limit = std::max(ratio_limit, absolute_limit);
    if (result.fitness > limit) {
      std::ostringstream out;
      out << "Rejected recovery candidate because fitness exceeded strict limit: fitness="
          << std::setprecision(6) << result.fitness << " previous=" << last_fitness_
          << " limit=" << limit << ".";
      detail = out.str();
      return false;
    }
    return true;
  }

  bool acceptRegistrationLocked(
    const CloudFrame & frame, const RegistrationResult & result, std::string & detail,
    const bool allow_pose_jump) const
  {
    if (!acceptAbsoluteFitnessLocked(result, "converged registration", detail)) {
      return false;
    }

    if (!tracking_ready_ && !std::isfinite(last_fitness_)) {
      return true;
    }

    const Pose2D previous = poseFromMatrix2D(last_pose_);
    const Pose2D candidate = poseFromMatrix2D(result.transform);
    const double pose_jump_m = std::hypot(candidate.x - previous.x, candidate.y - previous.y);
    const double pose_jump_yaw = std::abs(normalizeAngle(candidate.yaw - previous.yaw));
    double allowed_jump_m = options_.max_pose_jump_m;
    double allowed_jump_yaw = options_.max_pose_jump_yaw_deg * 3.14159265358979323846 / 180.0;

    if (frame.odom.has_value() && last_success_odom_.has_value()) {
      const Pose2D & previous_odom = last_success_odom_->pose;
      const Pose2D & current_odom = frame.odom->pose;
      const double odom_delta_m =
        std::hypot(current_odom.x - previous_odom.x, current_odom.y - previous_odom.y);
      const double odom_delta_yaw =
        std::abs(normalizeAngle(current_odom.yaw - previous_odom.yaw));
      const double odom_jump_m =
        options_.odom_delta_scale * odom_delta_m + options_.odom_translation_margin_m;
      const double odom_jump_yaw =
        options_.odom_delta_scale * odom_delta_yaw +
        options_.odom_yaw_margin_deg * 3.14159265358979323846 / 180.0;
      allowed_jump_m = std::min(allowed_jump_m, odom_jump_m);
      allowed_jump_yaw = std::min(allowed_jump_yaw, odom_jump_yaw);
    }

    if (!allow_pose_jump && (pose_jump_m > allowed_jump_m || pose_jump_yaw > allowed_jump_yaw)) {
      std::ostringstream out;
      out << "Rejected converged registration because pose jump exceeded guard: "
          << "translation=" << std::setprecision(4) << pose_jump_m
          << "m allowed=" << allowed_jump_m
          << "m yaw=" << (pose_jump_yaw * 180.0 / 3.14159265358979323846)
          << "deg allowed=" << (allowed_jump_yaw * 180.0 / 3.14159265358979323846)
          << "deg.";
      detail = out.str();
      return false;
    }

    if (std::isfinite(last_fitness_) && std::isfinite(result.fitness)) {
      const double ratio_limit = last_fitness_ * options_.fitness_degrade_ratio;
      const double absolute_limit = last_fitness_ + options_.fitness_degrade_abs;
      if (result.fitness > ratio_limit && result.fitness > absolute_limit) {
        std::ostringstream out;
        out << "Rejected converged registration because fitness degraded: fitness="
            << std::setprecision(6) << result.fitness
            << " previous=" << last_fitness_
            << " ratioLimit=" << ratio_limit
            << " absoluteLimit=" << absolute_limit << ".";
        detail = out.str();
        return false;
      }
    }

    return true;
  }

  bool acceptAbsoluteFitnessLocked(
    const RegistrationResult & result, const std::string & context, std::string & detail) const
  {
    if (!std::isfinite(result.fitness)) {
      detail = "Rejected " + context + " because fitness is unavailable.";
      return false;
    }
    if (options_.fitness_max_abs > 0.0 && result.fitness > options_.fitness_max_abs) {
      std::ostringstream out;
      out << "Rejected " << context << " because fitness exceeded hard limit: fitness="
          << std::setprecision(6) << result.fitness << " limit=" << options_.fitness_max_abs
          << ".";
      detail = out.str();
      return false;
    }
    return true;
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

  std::optional<OdomFrame> latestOdomLocked() const
  {
    if (!latest_odom_.has_value()) {
      return std::nullopt;
    }
    const double age_sec =
      std::chrono::duration<double>(Clock::now() - latest_odom_->received_at).count();
    if (age_sec > options_.odom_max_age_sec) {
      return std::nullopt;
    }
    return latest_odom_;
  }

  std::optional<Eigen::Matrix4f> odomRetryGuessLocked(
    const std::optional<OdomFrame> & current_odom) const
  {
    if (!options_.use_odom_retry || !current_odom.has_value() || !last_success_odom_.has_value()) {
      return std::nullopt;
    }
    Eigen::Matrix4f guess =
      last_pose_ * odomDeltaCurrentToPrevious(last_success_odom_->pose, current_odom->pose);
    if (!matrixFinite(guess)) {
      return std::nullopt;
    }
    return guess;
  }

  bool odomRetryAvailableLocked() const
  {
    return options_.use_odom_retry && latestOdomLocked().has_value() &&
           last_success_odom_.has_value();
  }

  bool odomRetrySuppressedLocked() const
  {
    return options_.use_odom_retry &&
           consecutive_odom_retry_failures_ >= options_.recovery_after_failed_frames;
  }

  double odomAgeSecLocked() const
  {
    if (!latest_odom_.has_value()) {
      return std::numeric_limits<double>::quiet_NaN();
    }
    return std::chrono::duration<double>(Clock::now() - latest_odom_->received_at).count();
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
    out << "\"lost\":" << ((state_ == "lost" || (state_ == "error" && last_error_ == "registration_failed")) ? "true" : "false")
        << ",";
    out << "\"mapName\":" << jsonString(options_.map_name) << ",";
    out << "\"mapPath\":" << jsonString(options_.map_path) << ",";
    out << "\"backend\":" << jsonString(options_.registration_backend) << ",";
    out << "\"frameId\":" << jsonString(options_.map_frame) << ",";
    out << "\"baseFrame\":" << jsonString(options_.base_frame) << ",";
    out << "\"odomTopic\":" << jsonString(options_.odom_topic) << ",";
    out << "\"useOdomRetry\":" << (options_.use_odom_retry ? "true" : "false") << ",";
    out << "\"recoverySearchEnabled\":"
        << (options_.recovery_search_enabled ? "true" : "false") << ",";
    out << "\"odomRetryAvailable\":" << (odomRetryAvailableLocked() ? "true" : "false")
        << ",";
    out << "\"odomRetrySuppressed\":"
        << (odomRetrySuppressedLocked() ? "true" : "false") << ",";
    out << "\"consecutiveOdomRetryFailures\":" << consecutive_odom_retry_failures_ << ",";
    out << "\"usedOdomRetry\":" << (last_used_odom_retry_ ? "true" : "false") << ",";
    out << "\"usedRecoverySearch\":" << (last_used_recovery_search_ ? "true" : "false")
        << ",";
    out << "\"recoveryStage\":" << jsonString(last_recovery_stage_) << ",";
    out << "\"recoveryCandidateCount\":" << last_recovery_candidate_count_ << ",";
    out << "\"recoverySweepCursor\":" << recovery_sweep_cursor_ << ",";
    out << "\"recoverySweepLastPoseCenter\":"
        << (recovery_sweep_last_pose_center_ ? "true" : "false") << ",";
    out << "\"recoveryConfirmCount\":" << recovery_confirm_count_ << ",";
    out << "\"recoveryConfirmFrames\":" << options_.recovery_confirm_frames << ",";
    out << "\"pendingRecoveryFitness\":" << jsonNumber(pending_recovery_fitness_) << ",";
    out << "\"recoveryNearGicpOnlyEnabled\":"
        << (options_.recovery_near_gicp_only_enabled ? "true" : "false") << ",";
    out << "\"recoveryNearRadiusM\":" << jsonNumber(options_.recovery_near_radius_m) << ",";
    out << "\"recoveryNearXyStepM\":" << jsonNumber(options_.recovery_near_xy_step_m) << ",";
    out << "\"recoveryNearYawStepDeg\":"
        << jsonNumber(options_.recovery_near_yaw_step_deg) << ",";
    out << "\"recoveryFarRadiusM\":" << jsonNumber(options_.recovery_far_radius_m) << ",";
    out << "\"recoveryFarRadiusStepM\":"
        << jsonNumber(options_.recovery_far_radius_step_m) << ",";
    out << "\"recoveryFarYawStepDeg\":"
        << jsonNumber(options_.recovery_far_yaw_step_deg) << ",";
    out << "\"recoveryFarAngleCount\":" << options_.recovery_far_angle_count << ",";
    out << "\"odomAgeSec\":" << jsonNumber(odomAgeSecLocked()) << ",";
    out << "\"cloudFrame\":" << jsonString(last_cloud_frame_) << ",";
    out << "\"rawSourcePoints\":" << last_raw_source_points_ << ",";
    out << "\"sourcePoints\":" << last_source_points_ << ",";
    out << "\"rawMapPoints\":" << raw_map_points_ << ",";
    out << "\"mapPoints\":" << map_points_ << ",";
    out << "\"voxelLeaf\":" << jsonNumber(options_.voxel_leaf) << ",";
    out << "\"maxPoseJumpM\":" << jsonNumber(options_.max_pose_jump_m) << ",";
    out << "\"maxPoseJumpYawDeg\":" << jsonNumber(options_.max_pose_jump_yaw_deg) << ",";
    out << "\"odomTranslationMarginM\":"
        << jsonNumber(options_.odom_translation_margin_m) << ",";
    out << "\"odomYawMarginDeg\":" << jsonNumber(options_.odom_yaw_margin_deg) << ",";
    out << "\"odomDeltaScale\":" << jsonNumber(options_.odom_delta_scale) << ",";
    out << "\"fitnessMaxAbs\":" << jsonNumber(options_.fitness_max_abs) << ",";
    out << "\"fitnessDegradeRatio\":" << jsonNumber(options_.fitness_degrade_ratio) << ",";
    out << "\"fitnessDegradeAbs\":" << jsonNumber(options_.fitness_degrade_abs) << ",";
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
  std::optional<OdomFrame> latest_odom_;
  std::optional<OdomFrame> last_success_odom_;
  std::optional<Eigen::Matrix4f> pending_recovery_pose_;

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
  bool last_used_odom_retry_ = false;
  bool last_used_recovery_search_ = false;
  std::string last_recovery_stage_;
  int last_recovery_candidate_count_ = 0;
  int recovery_confirm_count_ = 0;
  int consecutive_odom_retry_failures_ = 0;
  std::size_t recovery_sweep_cursor_ = 0;
  bool recovery_sweep_last_pose_center_ = true;
  double last_ndt_fitness_ = std::numeric_limits<double>::quiet_NaN();
  double last_fitness_ = std::numeric_limits<double>::quiet_NaN();
  double pending_recovery_fitness_ = std::numeric_limits<double>::quiet_NaN();
  double frequency_hz_ = std::numeric_limits<double>::quiet_NaN();

  tf2_ros::Buffer tf_buffer_;
  tf2_ros::TransformListener tf_listener_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr cloud_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
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
