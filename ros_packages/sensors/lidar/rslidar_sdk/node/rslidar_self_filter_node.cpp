#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstddef>
#include <functional>
#include <iterator>
#include <memory>
#include <string>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/point_cloud2_iterator.hpp>
#include <yaml-cpp/yaml.h>

namespace
{

struct BoxMask
{
  std::string name;
  std::array<double, 3> min;
  std::array<double, 3> max;

  bool contains(double x, double y, double z) const
  {
    return min[0] <= x && x <= max[0] &&
           min[1] <= y && y <= max[1] &&
           min[2] <= z && z <= max[2];
  }
};

bool yamlReadBool(const YAML::Node& node, const std::string& key, bool fallback)
{
  if (!node || !node[key])
  {
    return fallback;
  }
  return node[key].as<bool>();
}

std::string yamlReadString(const YAML::Node& node, const std::string& key, const std::string& fallback)
{
  if (!node || !node[key])
  {
    return fallback;
  }
  return node[key].as<std::string>();
}

bool yamlReadVec3(const YAML::Node& node, std::array<double, 3>* value)
{
  if (!node || !node.IsSequence() || node.size() != 3)
  {
    return false;
  }

  for (std::size_t index = 0; index < 3; ++index)
  {
    (*value)[index] = node[index].as<double>();
  }
  return true;
}

}  // namespace

class RslidarSelfFilterNode : public rclcpp::Node
{
public:
  RslidarSelfFilterNode()
  : Node("rslidar_self_filter_node")
  {
    declare_parameter<std::string>("config_path", "");
    const std::string config_path = get_parameter("config_path").as_string();
    loadConfig(config_path);

    auto qos = rclcpp::QoS(rclcpp::KeepLast(1));
    qos.reliable();
    qos.durability_volatile();
    publisher_ = create_publisher<sensor_msgs::msg::PointCloud2>(output_topic_, qos);
    subscription_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      input_topic_,
      qos,
      std::bind(&RslidarSelfFilterNode::handleCloud, this, std::placeholders::_1));

    RCLCPP_INFO(
      get_logger(),
      "LiDAR self-filter %s: %s -> %s, boxes=%zu, drop_nonfinite=%s",
      enabled_ ? "enabled" : "disabled",
      input_topic_.c_str(),
      output_topic_.c_str(),
      boxes_.size(),
      drop_nonfinite_ ? "true" : "false");
  }

private:
  void loadConfig(const std::string& config_path)
  {
    if (config_path.empty())
    {
      RCLCPP_WARN(get_logger(), "config_path is empty; using default LiDAR self-filter settings.");
      return;
    }

    try
    {
      const YAML::Node root = YAML::LoadFile(config_path);
      const YAML::Node filter = root["self_filter"];
      if (!filter)
      {
        RCLCPP_WARN(get_logger(), "self_filter section is missing in %s; passing clouds through.", config_path.c_str());
        enabled_ = false;
        return;
      }

      enabled_ = yamlReadBool(filter, "enabled", enabled_);
      input_topic_ = yamlReadString(filter, "input_topic", input_topic_);
      output_topic_ = yamlReadString(filter, "output_topic", output_topic_);
      drop_nonfinite_ = yamlReadBool(filter, "drop_nonfinite", drop_nonfinite_);

      const YAML::Node boxes = filter["boxes"];
      if (boxes && boxes.IsSequence())
      {
        for (std::size_t index = 0; index < boxes.size(); ++index)
        {
          const YAML::Node box_node = boxes[index];
          BoxMask box;
          box.name = yamlReadString(box_node, "name", "box_" + std::to_string(index));
          if (!yamlReadVec3(box_node["min"], &box.min) || !yamlReadVec3(box_node["max"], &box.max))
          {
            RCLCPP_WARN(get_logger(), "Ignoring self_filter box %zu because min/max is not a 3-value list.", index);
            continue;
          }

          for (std::size_t axis = 0; axis < 3; ++axis)
          {
            if (box.max[axis] < box.min[axis])
            {
              std::swap(box.min[axis], box.max[axis]);
            }
          }
          boxes_.push_back(box);
        }
      }
    }
    catch (const std::exception& exc)
    {
      RCLCPP_ERROR(
        get_logger(),
        "Failed to load LiDAR self-filter config from %s: %s. Passing clouds through.",
        config_path.c_str(),
        exc.what());
      enabled_ = false;
    }
  }

  bool insideAnyBox(double x, double y, double z) const
  {
    for (const BoxMask& box : boxes_)
    {
      if (box.contains(x, y, z))
      {
        return true;
      }
    }
    return false;
  }

  void handleCloud(const sensor_msgs::msg::PointCloud2::SharedPtr message)
  {
    if (!enabled_ || (boxes_.empty() && !drop_nonfinite_))
    {
      publisher_->publish(*message);
      return;
    }

    if (message->width == 0 || message->height == 0 || message->point_step == 0)
    {
      publisher_->publish(*message);
      return;
    }

    sensor_msgs::msg::PointCloud2 filtered;
    filtered.header = message->header;
    filtered.fields = message->fields;
    filtered.is_bigendian = message->is_bigendian;
    filtered.point_step = message->point_step;
    filtered.height = 1;
    filtered.is_dense = drop_nonfinite_ ? true : message->is_dense;
    filtered.data.reserve(message->data.size());

    std::size_t removed_self = 0;
    std::size_t removed_nonfinite = 0;

    try
    {
      sensor_msgs::PointCloud2ConstIterator<float> iter_x(*message, "x");
      sensor_msgs::PointCloud2ConstIterator<float> iter_y(*message, "y");
      sensor_msgs::PointCloud2ConstIterator<float> iter_z(*message, "z");

      const std::size_t point_count = static_cast<std::size_t>(message->width) * static_cast<std::size_t>(message->height);
      for (std::size_t point_index = 0; point_index < point_count; ++point_index, ++iter_x, ++iter_y, ++iter_z)
      {
        const float x = *iter_x;
        const float y = *iter_y;
        const float z = *iter_z;
        const bool finite = std::isfinite(x) && std::isfinite(y) && std::isfinite(z);

        if (drop_nonfinite_ && !finite)
        {
          ++removed_nonfinite;
          continue;
        }

        if (finite && insideAnyBox(x, y, z))
        {
          ++removed_self;
          continue;
        }

        const std::size_t row = point_index / static_cast<std::size_t>(message->width);
        const std::size_t column = point_index % static_cast<std::size_t>(message->width);
        const std::size_t source_offset =
          row * static_cast<std::size_t>(message->row_step) + column * static_cast<std::size_t>(message->point_step);
        const std::size_t source_end = source_offset + static_cast<std::size_t>(message->point_step);
        if (source_end <= message->data.size())
        {
          filtered.data.insert(
            filtered.data.end(),
            message->data.begin() + static_cast<std::ptrdiff_t>(source_offset),
            message->data.begin() + static_cast<std::ptrdiff_t>(source_end));
        }
      }
    }
    catch (const std::exception& exc)
    {
      RCLCPP_WARN_THROTTLE(
        get_logger(),
        *get_clock(),
        5000,
        "Failed to filter LiDAR cloud, publishing the original frame: %s",
        exc.what());
      publisher_->publish(*message);
      return;
    }

    filtered.width = static_cast<std::uint32_t>(filtered.data.size() / static_cast<std::size_t>(filtered.point_step));
    filtered.row_step = filtered.width * filtered.point_step;

    RCLCPP_DEBUG_THROTTLE(
      get_logger(),
      *get_clock(),
      2000,
      "LiDAR self-filter removed %zu self points and %zu non-finite points from %u source points.",
      removed_self,
      removed_nonfinite,
      message->width * message->height);

    publisher_->publish(filtered);
  }

  bool enabled_ = true;
  bool drop_nonfinite_ = true;
  std::string input_topic_ = "/rslidar_points_raw";
  std::string output_topic_ = "/rslidar_points";
  std::vector<BoxMask> boxes_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr publisher_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr subscription_;
};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<RslidarSelfFilterNode>());
  rclcpp::shutdown();
  return 0;
}
