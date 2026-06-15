import base64

import pytest

from modules.inference.observation import ObservationBuildError, build_observation


JPEG_BODY = b"\xff\xd8\xff\xe0jpegbody"


class FakeCameraReader:
    def __init__(self, frames=None):
        self.frames = frames or {}

    def read_frame(self, camera, kind, timeout_sec=0.0):
        key = f"{camera}_{kind}"
        if key in self.frames:
            return self.frames[key]
        return {"ok": True, "body": JPEG_BODY, "contentType": "image/jpeg"}


class FakeRosReader:
    def __init__(self, data):
        self.data = data

    def read(self, key, timeout_sec=0.0):
        if key in self.data:
            return self.data[key]
        return {"ok": False, "detail": f"no data for {key}"}


def _joint_state(values):
    return {"ok": True, "data": {"position": values}}


def _default_ros_reader():
    return FakeRosReader(
        {
            "piper_left_joint_state_double": _joint_state([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.05]),
            "piper_right_joint_state_double": _joint_state([-0.1, -0.2, -0.3, -0.4, -0.5, -0.6, 0.04]),
            "lifting_motor_state": {"ok": True, "data": {"back_height": 420}},
        }
    )


def test_build_observation_success():
    obs = build_observation("grasp the bottle", camera_reader=FakeCameraReader(), ros_reader=_default_ros_reader())
    assert obs["type"] == "observation"
    assert obs["prompt"] == "grasp the bottle"
    images = obs["observation"]["images"]
    assert set(images) == {"front", "left_wrist", "right_wrist"}
    assert base64.b64decode(images["front"]) == JPEG_BODY

    state = obs["observation"]["state"]
    assert state["left"]["joint1"] == pytest.approx(0.1)
    assert state["left"]["gripper"] == pytest.approx(0.05)
    assert state["right"]["joint6"] == pytest.approx(-0.6)
    # back_height is millimetres; observation reports metres.
    assert state["lift"]["height"] == pytest.approx(0.42)
    # Observation must NOT include chassis velocity in v1.
    assert "speed" not in state


def test_build_observation_falls_back_to_external_piper_joint_topics():
    ros = FakeRosReader(
        {
            "piper_left_joint_state": _joint_state([0.7, 0.2, 0.3, 0.4, 0.5, 0.6, 0.05]),
            "piper_right_joint_state": _joint_state([-0.7, -0.2, -0.3, -0.4, -0.5, -0.6, 0.04]),
            "lifting_motor_state": {"ok": True, "data": {"back_height": 420}},
        }
    )

    obs = build_observation("grasp the bottle", camera_reader=FakeCameraReader(), ros_reader=ros)
    state = obs["observation"]["state"]

    assert state["left"]["joint1"] == pytest.approx(0.7)
    assert state["right"]["joint1"] == pytest.approx(-0.7)


def test_build_observation_prefers_fresh_external_topic_over_stale_remap():
    ros = FakeRosReader(
        {
            "piper_left_joint_state_double": {**_joint_state([9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), "stale": True},
            "piper_right_joint_state_double": {**_joint_state([-9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]), "stale": True},
            "piper_left_joint_state": _joint_state([0.8, 0.2, 0.3, 0.4, 0.5, 0.6, 0.05]),
            "piper_right_joint_state": _joint_state([-0.8, -0.2, -0.3, -0.4, -0.5, -0.6, 0.04]),
            "lifting_motor_state": {"ok": True, "data": {"back_height": 420}},
        }
    )

    obs = build_observation("grasp the bottle", camera_reader=FakeCameraReader(), ros_reader=ros)
    state = obs["observation"]["state"]

    assert state["left"]["joint1"] == pytest.approx(0.8)
    assert state["right"]["joint1"] == pytest.approx(-0.8)


def test_missing_camera_raises():
    reader = FakeCameraReader({"camera_f_color": {"ok": False, "detail": "no frame"}})
    with pytest.raises(ObservationBuildError) as exc:
        build_observation("x", camera_reader=reader, ros_reader=_default_ros_reader())
    assert exc.value.code == "INFER-OBS-CAMERA"


def test_non_jpeg_camera_raises():
    reader = FakeCameraReader({"camera_l_color": {"ok": True, "body": b"\x89PNG", "contentType": "image/png"}})
    with pytest.raises(ObservationBuildError) as exc:
        build_observation("x", camera_reader=reader, ros_reader=_default_ros_reader())
    assert exc.value.code == "INFER-OBS-CAMERA"


def test_missing_joint_state_raises():
    ros = FakeRosReader(
        {
            "piper_right_joint_state_double": _joint_state([0.0] * 7),
            "lifting_motor_state": {"ok": True, "data": {"back_height": 0}},
        }
    )
    with pytest.raises(ObservationBuildError) as exc:
        build_observation("x", camera_reader=FakeCameraReader(), ros_reader=ros)
    assert exc.value.code == "INFER-OBS-JOINT"


def test_short_joint_state_raises():
    ros = _default_ros_reader()
    ros.data["piper_left_joint_state_double"] = _joint_state([0.0, 0.0, 0.0])
    with pytest.raises(ObservationBuildError) as exc:
        build_observation("x", camera_reader=FakeCameraReader(), ros_reader=ros)
    assert exc.value.code == "INFER-OBS-JOINT"
