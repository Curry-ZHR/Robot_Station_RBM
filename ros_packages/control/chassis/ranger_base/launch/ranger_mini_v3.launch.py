import os
import launch
import launch_ros

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='false',
                                             description='Use simulation clock if true')

    port_name_arg = DeclareLaunchArgument('port_name', default_value='can_chassis',
                                         description='CAN bus name, e.g. can_chassis')
    odom_frame_arg = DeclareLaunchArgument('odom_frame', default_value='odom',
                                           description='Odometry frame id')
    base_link_frame_arg = DeclareLaunchArgument('base_frame', default_value='base_link',
                                                description='Base link frame id')
    odom_topic_arg = DeclareLaunchArgument('odom_topic_name', default_value='odom',
                                           description='Odometry topic name')

    simulated_robot_arg = DeclareLaunchArgument('simulated_robot', default_value='false',
                                                   description='Whether running with simulator')
    publish_odom_tf_arg = DeclareLaunchArgument('publish_odom_tf', default_value='false',
                                                 description='Simulation control loop update rate')
    update_rate_arg = DeclareLaunchArgument('update_rate', default_value='50',
                                                 description='Simulation control loop update rate')
    robot_model_arg = DeclareLaunchArgument('robot_model', default_value='ranger_mini_v3',
                                           description='robot motion model')
    chassis_smoother_publish_rate_hz_arg = DeclareLaunchArgument(
        'chassis_smoother_publish_rate_hz',
        default_value='50',
        description='Chassis velocity smoother publish rate in Hz'
    )
    chassis_smoother_linear_accel_mps2_arg = DeclareLaunchArgument(
        'chassis_smoother_linear_accel_mps2',
        default_value='0.25',
        description='Maximum chassis linear acceleration in m/s^2'
    )
    chassis_smoother_linear_decel_mps2_arg = DeclareLaunchArgument(
        'chassis_smoother_linear_decel_mps2',
        default_value='0.60',
        description='Maximum chassis linear deceleration in m/s^2'
    )
    chassis_smoother_angular_accel_rad_s2_arg = DeclareLaunchArgument(
        'chassis_smoother_angular_accel_rad_s2',
        default_value='0.80',
        description='Maximum chassis angular acceleration in rad/s^2'
    )
    chassis_smoother_angular_decel_rad_s2_arg = DeclareLaunchArgument(
        'chassis_smoother_angular_decel_rad_s2',
        default_value='1.50',
        description='Maximum chassis angular deceleration in rad/s^2'
    )
    chassis_smoother_watchdog_timeout_sec_arg = DeclareLaunchArgument(
        'chassis_smoother_watchdog_timeout_sec',
        default_value='0.25',
        description='Seconds without target velocity before smoothing toward zero'
    )
    chassis_smoother_linear_deadband_mps_arg = DeclareLaunchArgument(
        'chassis_smoother_linear_deadband_mps',
        default_value='0.005',
        description='Linear velocity deadband in m/s'
    )
    chassis_smoother_angular_deadband_rad_s_arg = DeclareLaunchArgument(
        'chassis_smoother_angular_deadband_rad_s',
        default_value='0.01',
        description='Angular velocity deadband in rad/s'
    )
    chassis_raw_action_topic_arg = DeclareLaunchArgument(
        'chassis_raw_action_topic',
        default_value='/action/chassis',
        description='Dataset action topic for raw chassis target velocity JSON'
    )
    chassis_smoothed_action_topic_arg = DeclareLaunchArgument(
        'chassis_smoothed_action_topic',
        default_value='/action/chassis_smoothed',
        description='Dataset action topic for smoothed chassis velocity JSON'
    )
    chassis_velocity_smoother_node = launch_ros.actions.Node(
        package='ranger_base',
        executable='chassis_velocity_smoother_node',
        name='chassis_velocity_smoother',
        output='screen',
        parameters=[{
            'target_topic': '/cmd_vel',
            'output_topic': '/cmd_vel_smoothed',
            'raw_action_topic': launch.substitutions.LaunchConfiguration('chassis_raw_action_topic'),
            'smoothed_action_topic': launch.substitutions.LaunchConfiguration('chassis_smoothed_action_topic'),
            'publish_rate_hz': ParameterValue(LaunchConfiguration('chassis_smoother_publish_rate_hz'), value_type=float),
            'linear_accel_mps2': ParameterValue(LaunchConfiguration('chassis_smoother_linear_accel_mps2'), value_type=float),
            'linear_decel_mps2': ParameterValue(LaunchConfiguration('chassis_smoother_linear_decel_mps2'), value_type=float),
            'angular_accel_rad_s2': ParameterValue(LaunchConfiguration('chassis_smoother_angular_accel_rad_s2'), value_type=float),
            'angular_decel_rad_s2': ParameterValue(LaunchConfiguration('chassis_smoother_angular_decel_rad_s2'), value_type=float),
            'watchdog_timeout_sec': ParameterValue(LaunchConfiguration('chassis_smoother_watchdog_timeout_sec'), value_type=float),
            'linear_deadband_mps': ParameterValue(LaunchConfiguration('chassis_smoother_linear_deadband_mps'), value_type=float),
            'angular_deadband_rad_s': ParameterValue(LaunchConfiguration('chassis_smoother_angular_deadband_rad_s'), value_type=float),
        }],
    )
    ranger_base_node = launch_ros.actions.Node(
        package='ranger_base',
        executable='ranger_base_node',
        output='screen',
        emulate_tty=True,
        parameters=[{
                'use_sim_time': launch.substitutions.LaunchConfiguration('use_sim_time'),
                'port_name': launch.substitutions.LaunchConfiguration('port_name'),                
                'odom_frame': launch.substitutions.LaunchConfiguration('odom_frame'),
                'base_frame': launch.substitutions.LaunchConfiguration('base_frame'),
                'odom_topic_name': launch.substitutions.LaunchConfiguration('odom_topic_name'),
                'simulated_robot': launch.substitutions.LaunchConfiguration('simulated_robot'),
                'publish_odom_tf': launch.substitutions.LaunchConfiguration('publish_odom_tf'),
                'update_rate': launch.substitutions.LaunchConfiguration('update_rate'),
                'robot_model': launch.substitutions.LaunchConfiguration('robot_model'),
        }],
        remappings=[
            ('/cmd_vel', '/cmd_vel_smoothed'),
        ])

    return LaunchDescription([
        use_sim_time_arg,
        port_name_arg,        
        odom_frame_arg,
        base_link_frame_arg,
        odom_topic_arg,
        simulated_robot_arg,
        publish_odom_tf_arg,
        update_rate_arg,
        robot_model_arg,
        chassis_smoother_publish_rate_hz_arg,
        chassis_smoother_linear_accel_mps2_arg,
        chassis_smoother_linear_decel_mps2_arg,
        chassis_smoother_angular_accel_rad_s2_arg,
        chassis_smoother_angular_decel_rad_s2_arg,
        chassis_smoother_watchdog_timeout_sec_arg,
        chassis_smoother_linear_deadband_mps_arg,
        chassis_smoother_angular_deadband_rad_s_arg,
        chassis_raw_action_topic_arg,
        chassis_smoothed_action_topic_arg,
        chassis_velocity_smoother_node,
        ranger_base_node
    ])
