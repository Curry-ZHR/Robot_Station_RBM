import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_wide_angle_camera(context, bringup_share):
    configured_device = LaunchConfiguration("wide_angle_device").perform(context)
    resolved_device = os.path.realpath(configured_device)
    return [
        Node(
            package="usb_cam",
            executable="usb_cam_node_exe",
            namespace="camera_h/color",
            name="wide_angle_camera",
            output="screen",
            parameters=[
                os.path.join(bringup_share, "config", "wide_angle_camera.yaml"),
                {"video_device": resolved_device},
            ],
        )
    ]


def generate_launch_description():
    bringup_share = get_package_share_directory("robot_station_camera_bringup")
    orbbec_share = get_package_share_directory("orbbec_camera")

    front_serial = DeclareLaunchArgument("front_serial", default_value="CC136530352")
    left_serial = DeclareLaunchArgument("left_serial", default_value="CC1365303LY")
    right_serial = DeclareLaunchArgument("right_serial", default_value="CC136530160")
    wide_angle_device = DeclareLaunchArgument(
        "wide_angle_device",
        default_value="/dev/v4l/by-id/usb-LRCP_ZWAK_LRCP_U3-JX02_SN0001-video-index0",
    )

    orbbec_cameras = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(orbbec_share, "launch", "multi_camera.launch.py")),
        launch_arguments={
            "front_serial": LaunchConfiguration("front_serial"),
            "left_serial": LaunchConfiguration("left_serial"),
            "right_serial": LaunchConfiguration("right_serial"),
        }.items(),
    )

    wide_angle_camera = OpaqueFunction(
        function=launch_wide_angle_camera,
        kwargs={"bringup_share": bringup_share},
    )

    return LaunchDescription(
        [
            front_serial,
            left_serial,
            right_serial,
            wide_angle_device,
            orbbec_cameras,
            wide_angle_camera,
        ]
    )
