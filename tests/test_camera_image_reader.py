from modules.ros_io.image_reader import CAMERA_IMAGE_SPECS, CameraImageReader


class FakeRuntime:
    def __init__(self):
        self.subscriptions = []

    def create_subscription(self, key, message_type, topic, callback, qos_depth):
        self.subscriptions.append(
            {
                "key": key,
                "messageType": message_type,
                "topic": topic,
                "callback": callback,
                "qosDepth": qos_depth,
            }
        )


def test_wide_angle_camera_registers_only_color_feed():
    assert CAMERA_IMAGE_SPECS["camera_h_color"].topic == "/camera_h/color/image_raw/compressed"
    assert "camera_h_depth" not in CAMERA_IMAGE_SPECS
    assert "camera_h_ir" not in CAMERA_IMAGE_SPECS


def test_color_feed_list_includes_wide_angle_camera_first():
    runtime = FakeRuntime()
    reader = CameraImageReader(runtime)

    result = reader.list_images(kind="color")

    assert result["ok"] is True
    assert [feed["camera"] for feed in result["feeds"]] == ["camera_h", "camera_f", "camera_l", "camera_r"]
    assert [item["topic"] for item in runtime.subscriptions] == [
        "/camera_h/color/image_raw/compressed",
        "/camera_f/color/image_raw/compressed",
        "/camera_l/color/image_raw/compressed",
        "/camera_r/color/image_raw/compressed",
    ]


def test_depth_feed_list_remains_orbbec_only():
    runtime = FakeRuntime()
    reader = CameraImageReader(runtime)

    result = reader.list_images(kind="depth")

    assert result["ok"] is True
    assert [feed["camera"] for feed in result["feeds"]] == ["camera_f", "camera_l", "camera_r"]
