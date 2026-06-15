"""Build the observation message sent to the remote inference machine.

The observation gathers the latest camera frames, arm joint feedback and lift
height from the local ROS IO layer. Chassis velocity is intentionally NOT part
of the observation; velocity only appears as a command inside returned action
chunks.
"""

import base64
import os

from modules.control.piper.feedback import (
    joint_state_key_candidates,
    read_joint_state_candidate,
)
from modules.ros_io import get_camera_image_reader, get_ros_reader
from modules.inference.validation import GRIPPER_NAME, JOINT_NAMES


class ObservationBuildError(RuntimeError):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code
        self.detail = detail


# Camera mapping for v1: observation label -> (camera, kind).
CAMERA_MAP = {
    "front": ("camera_f", "color"),
    "left_wrist": ("camera_l", "color"),
    "right_wrist": ("camera_r", "color"),
}

# Joint-state read keys per arm. Defaults cover both Robot Station's double-arm
# remapping and externally launched Piper nodes that publish /puppet/joint_*.
LEFT_JOINT_STATE_KEYS = joint_state_key_candidates(
    "left",
    list_env="INFERENCE_LEFT_JOINT_STATE_KEYS",
    single_env="INFERENCE_LEFT_JOINT_STATE_KEY",
)
RIGHT_JOINT_STATE_KEYS = joint_state_key_candidates(
    "right",
    list_env="INFERENCE_RIGHT_JOINT_STATE_KEYS",
    single_env="INFERENCE_RIGHT_JOINT_STATE_KEY",
)
LEFT_JOINT_STATE_KEY = LEFT_JOINT_STATE_KEYS[0]
RIGHT_JOINT_STATE_KEY = RIGHT_JOINT_STATE_KEYS[0]
LIFT_STATE_KEY = os.environ.get("INFERENCE_LIFT_STATE_KEY", "lifting_motor_state")

FRAME_WAIT_SEC = float(os.environ.get("INFERENCE_FRAME_WAIT_SEC", "1.0"))
STATE_WAIT_SEC = float(os.environ.get("INFERENCE_STATE_WAIT_SEC", "0.5"))


def _encode_frame(camera, kind, reader):
    result = reader.read_frame(camera, kind, timeout_sec=FRAME_WAIT_SEC)
    if not result.get("ok"):
        raise ObservationBuildError(
            "INFER-OBS-CAMERA",
            f"Camera {camera}/{kind} unavailable: {result.get('detail', 'no frame')}.",
        )
    body = result.get("body")
    if not body:
        raise ObservationBuildError("INFER-OBS-CAMERA", f"Camera {camera}/{kind} returned an empty frame.")
    content_type = str(result.get("contentType", ""))
    if "jpeg" not in content_type and "jpg" not in content_type:
        raise ObservationBuildError(
            "INFER-OBS-CAMERA",
            f"Camera {camera}/{kind} frame is {content_type or 'unknown'}, expected JPEG.",
        )
    return base64.b64encode(body).decode("ascii")


def _arm_state(keys, side, reader):
    try:
        _, _, positions = read_joint_state_candidate(
            reader,
            side,
            keys,
            timeout_sec=STATE_WAIT_SEC,
            min_positions=7,
            accept_stale=True,
        )
    except Exception as exc:
        raise ObservationBuildError(
            "INFER-OBS-JOINT",
            str(exc),
        ) from exc
    arm = {name: float(positions[index]) for index, name in enumerate(JOINT_NAMES)}
    arm[GRIPPER_NAME] = float(positions[6])
    return arm


def _lift_state(reader):
    result = reader.read(LIFT_STATE_KEY, timeout_sec=STATE_WAIT_SEC)
    if not result.get("ok"):
        raise ObservationBuildError(
            "INFER-OBS-LIFT",
            f"Lift state ({LIFT_STATE_KEY}) unavailable: {result.get('detail', 'no data')}.",
        )
    data = result.get("data") or {}
    if "back_height" not in data:
        raise ObservationBuildError("INFER-OBS-LIFT", "Lift state does not expose back_height.")
    return {"height": float(data["back_height"]) / 1000.0}


def read_current_arm_positions(ros_reader=None):
    """Snapshot the current [j1..j6, gripper] feedback for both arms.

    Returns {"left": [7]|None, "right": [7]|None}; a side is None when its joint
    feedback is unavailable. Used by the executor to freeze masked joints in
    place at their current position.
    """

    ros_reader = ros_reader or get_ros_reader()
    out = {}
    for side, keys in (("left", LEFT_JOINT_STATE_KEYS), ("right", RIGHT_JOINT_STATE_KEYS)):
        try:
            _, _, positions = read_joint_state_candidate(
                ros_reader,
                side,
                keys,
                timeout_sec=STATE_WAIT_SEC,
                min_positions=7,
                accept_stale=True,
            )
        except Exception:
            out[side] = None
        else:
            out[side] = [float(positions[index]) for index in range(7)]
    return out


def build_observation(prompt, camera_reader=None, ros_reader=None):
    """Assemble the observation payload. Raises ObservationBuildError on any
    missing camera or state source so request-chunk fails with a clear reason."""

    camera_reader = camera_reader or get_camera_image_reader()
    ros_reader = ros_reader or get_ros_reader()

    images = {
        label: _encode_frame(camera, kind, camera_reader)
        for label, (camera, kind) in CAMERA_MAP.items()
    }
    state = {
        "left": _arm_state(LEFT_JOINT_STATE_KEYS, "left", ros_reader),
        "right": _arm_state(RIGHT_JOINT_STATE_KEYS, "right", ros_reader),
        "lift": _lift_state(ros_reader),
    }
    return {
        "type": "observation",
        "prompt": str(prompt or ""),
        "observation": {
            "images": images,
            "state": state,
        },
    }
