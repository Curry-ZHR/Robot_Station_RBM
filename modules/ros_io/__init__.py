"""ROS topic IO helpers for Robot Station backend APIs."""

from modules.ros_io.reader import RosTopicReader
from modules.ros_io.runtime import RosRuntime
from modules.ros_io.image_reader import CameraImageReader
from modules.ros_io.lidar_reader import LidarPointCloudReader
from modules.ros_io.writer import RosTopicWriter


_runtime = RosRuntime()
_reader = RosTopicReader(_runtime)
_camera_image_reader = CameraImageReader(_runtime)
_lidar_point_cloud_reader = LidarPointCloudReader(_runtime)
_writer = RosTopicWriter(_runtime)


def get_ros_reader():
    return _reader


def get_ros_writer():
    return _writer


def get_camera_image_reader():
    return _camera_image_reader


def get_lidar_point_cloud_reader():
    return _lidar_point_cloud_reader


def get_ros_runtime():
    return _runtime


def shutdown_ros_io():
    _runtime.shutdown()
