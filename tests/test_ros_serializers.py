import pytest

from modules.ros_io.serializers import message_to_plain


np = pytest.importorskip("numpy")


def test_message_to_plain_converts_numpy_arrays_to_lists():
    value = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    assert message_to_plain(value) == [1.0, 2.0, 3.0]


def test_message_to_plain_converts_camera_info_numpy_fields():
    sensor_msgs = pytest.importorskip("sensor_msgs.msg")
    camera_info = sensor_msgs.CameraInfo()
    camera_info.k[:] = [600.0, 0.0, 320.0, 0.0, 600.0, 240.0, 0.0, 0.0, 1.0]

    payload = message_to_plain(camera_info)

    assert payload["k"] == [600.0, 0.0, 320.0, 0.0, 600.0, 240.0, 0.0, 0.0, 1.0]
