import math
from types import SimpleNamespace

import backend.server as server
from modules.ros_io.commands import build_command


class FakePoseWithCovarianceStamped:
    def __init__(self):
        self.header = SimpleNamespace(frame_id="", stamp=None)
        self.pose = SimpleNamespace(
            pose=SimpleNamespace(
                position=SimpleNamespace(x=None, y=None, z=None),
                orientation=SimpleNamespace(x=None, y=None, z=None, w=None),
            ),
            covariance=[],
        )


def _handler(path, payload):
    handler = object.__new__(server.RobotStationHandler)
    handler.path = path
    handler.read_json_body = lambda: payload
    return handler


def test_initial_pose_builder_uses_map_frame_yaw_degrees_and_default_covariance():
    message = build_command(
        "initial_pose",
        {"x": 1.2, "y": -0.4, "z": 0, "yawDeg": 90},
        FakePoseWithCovarianceStamped,
        stamp="stamp",
    )

    assert message.header.stamp == "stamp"
    assert message.header.frame_id == "map"
    assert message.pose.pose.position.x == 1.2
    assert message.pose.pose.position.y == -0.4
    assert message.pose.pose.position.z == 0.0
    assert message.pose.pose.orientation.x == 0.0
    assert message.pose.pose.orientation.y == 0.0
    assert message.pose.pose.orientation.z == math.sin(math.radians(90) / 2)
    assert message.pose.pose.orientation.w == math.cos(math.radians(90) / 2)
    assert len(message.pose.covariance) == 36
    assert message.pose.covariance[0] == 0.25
    assert message.pose.covariance[7] == 0.25
    assert message.pose.covariance[35] == math.radians(15.0) ** 2


def test_initial_pose_builder_accepts_nested_pose_frame_and_custom_covariance():
    covariance = [0.0] * 36
    covariance[0] = 1.0
    covariance[7] = 2.0
    covariance[35] = 3.0

    message = build_command(
        "initial_pose",
        {"pose": {"x": 2, "y": 3, "yawRad": math.pi}, "frameId": "custom_map", "covariance": covariance},
        FakePoseWithCovarianceStamped,
    )

    assert message.header.frame_id == "custom_map"
    assert message.pose.pose.position.x == 2.0
    assert message.pose.pose.position.y == 3.0
    assert message.pose.pose.orientation.z == math.sin(math.pi / 2)
    assert message.pose.pose.orientation.w == math.cos(math.pi / 2)
    assert message.pose.covariance == covariance


def test_localization_initial_pose_endpoint_publishes_ros_action(monkeypatch):
    payload = {"x": 1.0, "y": 2.0, "yawDeg": 45}
    responses = []
    published = []
    handler = _handler("/api/localization/initial-pose", payload)

    class FakeWriter:
        def publish(self, key, command):
            published.append((key, command))
            return {
                "ok": True,
                "code": "ROS-W-PUBLISHED",
                "detail": "published",
                "topic": "/initialpose",
            }

    handler.write_json = lambda response, status=200, headers=None: responses.append((response, status))
    monkeypatch.setattr(server, "get_ros_writer", lambda: FakeWriter())
    monkeypatch.setattr(server, "log_action_result", lambda *args, **kwargs: None)

    server.RobotStationHandler.do_POST(handler)

    assert published == [("localization_initial_pose", payload)]
    assert responses == [
        (
            {
                "ok": True,
                "code": "ROS-W-PUBLISHED",
                "detail": "published",
                "topic": "/initialpose",
            },
            200,
        )
    ]
