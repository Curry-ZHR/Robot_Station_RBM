from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    # Declare arguments
    front_serial_arg = DeclareLaunchArgument(
        'front_serial', default_value='CC1T35300M9'
    )
    left_serial_arg = DeclareLaunchArgument(
        'left_serial', default_value='CC16353006W'
    )
    right_serial_arg = DeclareLaunchArgument(
        'right_serial', default_value='CC1635300EB'
    )

    # Include launch files
    package_dir = get_package_share_directory('orbbec_camera')
    launch_file_dir = os.path.join(package_dir, 'launch')
    launch1_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_file_dir, 'dabai.launch.py')
        ),
        launch_arguments={
            'camera_name': 'camera_f',
            'serial_number': LaunchConfiguration('front_serial'),
            'device_num': '3',
            # 'sync_mode': 'standalone'
        }.items(),
    )

    launch2_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_file_dir, 'dabai.launch.py')
        ),
        launch_arguments={
            'camera_name': 'camera_l',
            'serial_number': LaunchConfiguration('left_serial'),
            'device_num': '3',
            # 'sync_mode': 'standalone'
        }.items(),
    )

    launch3_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_file_dir, 'dabai.launch.py')
        ),
        launch_arguments={
            'camera_name': 'camera_r',
            'serial_number': LaunchConfiguration('right_serial'),
            'device_num': '3',
            # 'sync_mode': 'standalone'
        }.items(),
    )

    # If you need more cameras, just add more launch_include here, and change the usb_port and device_num

    # Launch description
    ld = LaunchDescription([
        front_serial_arg,
        left_serial_arg,
        right_serial_arg,
        GroupAction([launch1_include]),
        GroupAction([launch2_include]),
        GroupAction([launch3_include])
    ])

    return ld
