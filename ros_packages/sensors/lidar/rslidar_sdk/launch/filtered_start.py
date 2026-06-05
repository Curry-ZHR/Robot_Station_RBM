from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    default_config = get_package_share_directory("rslidar_sdk") + "/config/config.yaml"
    config_path = LaunchConfiguration("config_path")

    return LaunchDescription([
        DeclareLaunchArgument(
            "config_path",
            default_value=default_config,
            description="Path to the rslidar_sdk YAML config.",
        ),
        Node(
            package="rslidar_sdk",
            executable="rslidar_sdk_node",
            output="screen",
            parameters=[{"config_path": config_path}],
        ),
        Node(
            package="rslidar_sdk",
            executable="rslidar_self_filter_node",
            output="screen",
            parameters=[{"config_path": config_path}],
        ),
    ])
