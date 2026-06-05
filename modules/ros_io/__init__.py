"""ROS topic IO helpers for Robot Station backend APIs."""

from modules.ros_io.reader import RosTopicReader
from modules.ros_io.runtime import RosRuntime
from modules.ros_io.image_reader import CameraImageReader
from modules.ros_io.lidar_reader import LidarPointCloudReader
from modules.ros_io.writer import RosTopicWriter


_state_runtime = RosRuntime("robot_station_state_bridge", num_threads=2)
_camera_runtime = RosRuntime("robot_station_camera_bridge", num_threads=2)
_lidar_runtime = RosRuntime("robot_station_lidar_bridge", num_threads=2)
_command_runtime = RosRuntime("robot_station_command_bridge", num_threads=2)

_reader = RosTopicReader(_state_runtime)
_camera_image_reader = CameraImageReader(_camera_runtime)
_lidar_point_cloud_reader = LidarPointCloudReader(_lidar_runtime)
_writer = RosTopicWriter(_command_runtime)


def get_ros_reader():
    return _reader


def get_ros_writer():
    return _writer


def get_camera_image_reader():
    return _camera_image_reader


def get_lidar_point_cloud_reader():
    return _lidar_point_cloud_reader


def get_ros_runtime():
    return _command_runtime


def shutdown_ros_io():
    for runtime in (_state_runtime, _camera_runtime, _lidar_runtime, _command_runtime):
        runtime.shutdown()
