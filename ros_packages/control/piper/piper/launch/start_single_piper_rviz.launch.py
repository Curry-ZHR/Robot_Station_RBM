# piper_launch.py

from launch import LaunchDescription
# from launch_ros.actions import Node, IncludeLaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription  # 正确的导入方式
from launch_ros.actions import Node  # 保持不变
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory

import os

def generate_launch_description():
    # 获取piper_description包的路径
    piper_description_path = os.path.join(
        get_package_share_directory('piper_description'),
        'launch',
        'display_xacro.launch.py'
    )

    # 定义launch参数
    can_port_arg = DeclareLaunchArgument(
        'can_port',
        default_value='can0',
        description='CAN port for the robot arm'
    )

    auto_enable_arg = DeclareLaunchArgument(
        'auto_enable',
        default_value='true',
        description='Enable robot arm automatically'
    )

    # 包含 display_xacro.launch.py
    display_xacro_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(piper_description_path)
    )

    rviz_ctrl_flag_arg = DeclareLaunchArgument(
        'rviz_ctrl_flag',
        default_value='true',
        description='Start rviz flag.'
    )
    
    girpper_exist_arg = DeclareLaunchArgument(
        'girpper_exist',
        default_value='true',
        description='gripper'
    )

    joint_speed_percent_arg = DeclareLaunchArgument(
        'joint_speed_percent',
        default_value='10',
        description='Joint motion speed as a percentage of Piper default speed.'
    )

    max_joint_speed_deg_s_arg = DeclareLaunchArgument(
        'max_joint_speed_deg_s',
        default_value='5',
        description='Maximum smoother joint speed in degrees per second.'
    )

    smoother_publish_rate_hz_arg = DeclareLaunchArgument(
        'smoother_publish_rate_hz',
        default_value='50',
        description='Joint smoother publish rate in Hz.'
    )

    piper_smoother_node = Node(
        package='piper',
        executable='piper_joint_smoother',
        name='piper_joint_smoother',
        output='screen',
        parameters=[{
            'target_topic': '/joint_states',
            'feedback_topic': '/puppet/joint_left',
            'output_topic': '/joint_states_raw',
            'hold_topic': '/joint_states/hold',
            'publish_rate_hz': ParameterValue(LaunchConfiguration('smoother_publish_rate_hz'), value_type=float),
            'max_joint_speed_deg_s': ParameterValue(LaunchConfiguration('max_joint_speed_deg_s'), value_type=float),
        }],
    )
    
    # 定义机械臂节点
    piper_ctrl_node = Node(
        package='piper',
        executable='piper_single_ctrl',
        name='piper_ctrl_single_node',
        output='screen',
        parameters=[
            {'can_port': LaunchConfiguration('can_port')},
            {'auto_enable': LaunchConfiguration('auto_enable')},
            {'rviz_ctrl_flag':  LaunchConfiguration('rviz_ctrl_flag')},
            {'girpper_exist':  LaunchConfiguration('girpper_exist')},
            {'joint_speed_percent': ParameterValue(LaunchConfiguration('joint_speed_percent'), value_type=int)}
        ],
        remappings=[
            ('joint_ctrl_single', '/joint_states_raw')
        ]
    )

    # 返回LaunchDescription对象，包含以上所有元素
    return LaunchDescription([
        can_port_arg,
        auto_enable_arg,
        display_xacro_launch,
        rviz_ctrl_flag_arg,
        girpper_exist_arg,
        joint_speed_percent_arg,
        max_joint_speed_deg_s_arg,
        smoother_publish_rate_hz_arg,
        piper_smoother_node,
        piper_ctrl_node
    ])
