from modules.ros_io.writer import RosTopicWriter


class RuntimeThatShouldNotPublish:
    def now_msg(self):
        raise AssertionError("piper_enable_all=false should not create a ROS message")

    def get_publisher(self, *args, **kwargs):
        raise AssertionError("piper_enable_all=false should not request a ROS publisher")


def test_piper_enable_false_is_noop(monkeypatch):
    def fail_import(message_type):
        raise AssertionError(f"unexpected ROS message import: {message_type}")

    monkeypatch.setattr("modules.ros_io.writer.import_message_class", fail_import)
    writer = RosTopicWriter(RuntimeThatShouldNotPublish())

    result = writer.publish("piper_enable_all", {"enabled": False})

    assert result["ok"] is True
    assert result["code"] == "ROS-W-NOOP"
    assert result["topic"] == "/enable_flag"
