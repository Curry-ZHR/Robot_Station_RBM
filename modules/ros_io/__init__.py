"""ROS topic IO helpers for Robot Station backend APIs."""

from modules.ros_io.reader import RosTopicReader
from modules.ros_io.runtime import RosRuntime
from modules.ros_io.writer import RosTopicWriter


_runtime = RosRuntime()
_reader = RosTopicReader(_runtime)
_writer = RosTopicWriter(_runtime)


def get_ros_reader():
    return _reader


def get_ros_writer():
    return _writer


def shutdown_ros_io():
    _runtime.shutdown()

