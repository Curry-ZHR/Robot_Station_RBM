from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Declare the launch arguments
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

    piper_left_smoother_node = Node(
        package='piper',
        executable='piper_joint_smoother',
        name='piper_left_joint_smoother',
        output='screen',
        parameters=[{
            'target_topic': '/joint_left_states',
            'feedback_topic': '/puppet/joint_left',
            'output_topic': '/joint_left_states_raw',
            'hold_topic': '/joint_left_states/hold',
            'publish_rate_hz': ParameterValue(LaunchConfiguration('smoother_publish_rate_hz'), value_type=float),
            'max_joint_speed_deg_s': ParameterValue(LaunchConfiguration('max_joint_speed_deg_s'), value_type=float),
        }],
    )

    piper_right_smoother_node = Node(
        package='piper',
        executable='piper_joint_smoother',
        name='piper_right_joint_smoother',
        output='screen',
        parameters=[{
            'target_topic': '/joint_right_states',
            'feedback_topic': '/puppet/joint_right',
            'output_topic': '/joint_right_states_raw',
            'hold_topic': '/joint_right_states/hold',
            'publish_rate_hz': ParameterValue(LaunchConfiguration('smoother_publish_rate_hz'), value_type=float),
            'max_joint_speed_deg_s': ParameterValue(LaunchConfiguration('max_joint_speed_deg_s'), value_type=float),
        }],
    )

    # Define the node
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
        }],
        remappings=[
            ('pos_cmd', '/pos_left_cmd'),
            ('joint_ctrl_single', '/joint_left_states_raw'),
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
        }],
        remappings=[
            ('pos_cmd', '/pos_right_cmd'),
            ('joint_ctrl_single', '/joint_right_states_raw'),
        ]
    )

    # Return the LaunchDescription
    return LaunchDescription([
        can_left_port_arg,
        can_right_port_arg,
        auto_enable_arg,
        rviz_ctrl_flag_arg,
        girpper_exist_arg,
        joint_speed_percent_arg,
        max_joint_speed_deg_s_arg,
        smoother_publish_rate_hz_arg,
        piper_left_smoother_node,
        piper_right_smoother_node,
        piper_left_node,
        piper_right_node
    ])
