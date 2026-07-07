from types import SimpleNamespace

from sensor_msgs.msg import JointState

from modules.robot_description.joint_state_bridge import (
    BASE_JOINT_NAMES,
    _lifting_joint_position,
    _prefix_joint_state,
    _side_joint_names,
)


def test_prefix_joint_state_maps_piper_feedback_to_robot_description_names():
    source = JointState()
    source.position = [1.0, 2.0, -1.0, 0.5, -0.25, 0.75, 0.04]

    output = _prefix_joint_state(source, "left", gripper_scale=1.0)

    assert output.name == _side_joint_names("left")
    assert list(output.position) == [1.0, 2.0, -1.0, 0.5, -0.25, 0.75, 0.04, -0.04]
    assert list(output.velocity) == []
    assert list(output.effort) == []


def test_prefix_joint_state_defaults_missing_values_and_clamps_gripper():
    source = JointState()
    source.position = [float("nan"), 0.2, 0.3, 0.4, 0.5, 0.6, 1.0]

    output = _prefix_joint_state(source, "right", gripper_scale=2.0)

    assert output.name == _side_joint_names("right")
    assert list(output.position) == [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.05, -0.05]


def test_default_joint_state_includes_lifting_joint_for_arm_tf_chain():
    assert "lifting_joint" in BASE_JOINT_NAMES


def test_lifting_joint_position_maps_feedback_height_mm_to_urdf_meters():
    message = SimpleNamespace(back_height=420)

    assert _lifting_joint_position(message) == 0.42


def test_lifting_joint_position_clamps_to_configured_travel():
    assert _lifting_joint_position(SimpleNamespace(back_height=-10)) == 0.0
    assert _lifting_joint_position(SimpleNamespace(back_height=900)) == 0.75
