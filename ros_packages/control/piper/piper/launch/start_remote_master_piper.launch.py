from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    can_left_port_arg = DeclareLaunchArgument(
        'can_left_port',
        default_value='can_left',
        description='CAN left port to be used by the Piper node.'
    )
    can_right_port_arg = DeclareLaunchArgument(
        'can_right_port',
        default_value='can_right',
        description='CAN right port to be used by the Piper node.'
    )
    auto_enable_arg = DeclareLaunchArgument(
        'auto_enable',
        default_value='true',
        description='Automatically enable the Piper node.'
    )
    rviz_ctrl_flag_arg = DeclareLaunchArgument(
        'rviz_ctrl_flag',
        default_value='false',
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

    piper_left_node = Node(
        package='piper',
        executable='piper_single_ctrl',
        name='piper_left_ctrl_node',
        output='screen',
        parameters=[{
            'can_port': LaunchConfiguration('can_left_port'),
            'auto_enable': LaunchConfiguration('auto_enable'),
            'rviz_ctrl_flag': LaunchConfiguration('rviz_ctrl_flag'),
            'girpper_exist': LaunchConfiguration('girpper_exist'),
            'piper_name': 'left',
            'joint_speed_percent': ParameterValue(LaunchConfiguration('joint_speed_percent'), value_type=int),
            'joint_state_topic': '/puppet/joint_left',
            'joint_command_topic': '/master/joint_left',
            'joint_control_echo_topic': '/master/joint_left',
            'publish_joint_control_echo': False,
        }],
        remappings=[
            ('pos_cmd', '/pos_left_cmd'),
        ]
    )

    piper_right_node = Node(
        package='piper',
        executable='piper_single_ctrl',
        name='piper_right_ctrl_node',
        output='screen',
        parameters=[{
            'can_port': LaunchConfiguration('can_right_port'),
            'auto_enable': LaunchConfiguration('auto_enable'),
            'rviz_ctrl_flag': LaunchConfiguration('rviz_ctrl_flag'),
            'girpper_exist': LaunchConfiguration('girpper_exist'),
            'piper_name': 'right',
            'joint_speed_percent': ParameterValue(LaunchConfiguration('joint_speed_percent'), value_type=int),
            'joint_state_topic': '/puppet/joint_right',
            'joint_command_topic': '/master/joint_right',
            'joint_control_echo_topic': '/master/joint_right',
            'publish_joint_control_echo': False,
        }],
        remappings=[
            ('pos_cmd', '/pos_right_cmd'),
        ]
    )

    return LaunchDescription([
        can_left_port_arg,
        can_right_port_arg,
        auto_enable_arg,
        rviz_ctrl_flag_arg,
        girpper_exist_arg,
        joint_speed_percent_arg,
        piper_left_node,
        piper_right_node,
    ])
