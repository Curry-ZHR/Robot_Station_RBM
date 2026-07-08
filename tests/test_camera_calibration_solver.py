import json
import math

import numpy as np
import pytest

from modules.calibration.solver import solve_camera_extrinsics


pytest.importorskip("cv2")


def rpy_matrix(roll, pitch, yaw):
    cr = math.cos(roll)
    sr = math.sin(roll)
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    cy = math.cos(yaw)
    sy = math.sin(yaw)
    return np.asarray(
        [
            [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr],
        ],
        dtype=np.float64,
    )


def transform(translation, rpy):
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = rpy_matrix(*rpy)
    matrix[:3, 3] = np.asarray(translation, dtype=np.float64)
    return matrix


def quaternion_from_matrix(rotation):
    trace = float(np.trace(rotation))
    if trace > 0.0:
        scale = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * scale
        x = (rotation[2, 1] - rotation[1, 2]) / scale
        y = (rotation[0, 2] - rotation[2, 0]) / scale
        z = (rotation[1, 0] - rotation[0, 1]) / scale
    else:
        index = int(np.argmax(np.diag(rotation)))
        if index == 0:
            scale = math.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2]) * 2.0
            w = (rotation[2, 1] - rotation[1, 2]) / scale
            x = 0.25 * scale
            y = (rotation[0, 1] + rotation[1, 0]) / scale
            z = (rotation[0, 2] + rotation[2, 0]) / scale
        elif index == 1:
            scale = math.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2]) * 2.0
            w = (rotation[0, 2] - rotation[2, 0]) / scale
            x = (rotation[0, 1] + rotation[1, 0]) / scale
            y = 0.25 * scale
            z = (rotation[1, 2] + rotation[2, 1]) / scale
        else:
            scale = math.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1]) * 2.0
            w = (rotation[1, 0] - rotation[0, 1]) / scale
            x = (rotation[0, 2] + rotation[2, 0]) / scale
            y = (rotation[1, 2] + rotation[2, 1]) / scale
            z = 0.25 * scale
    return {"x": x, "y": y, "z": z, "w": w}


def plain_transform(matrix, target_frame="base_link", source_frame="camera_parent"):
    return {
        "targetFrame": target_frame,
        "sourceFrame": source_frame,
        "translation": {
            "x": float(matrix[0, 3]),
            "y": float(matrix[1, 3]),
            "z": float(matrix[2, 3]),
        },
        "rotation": quaternion_from_matrix(matrix[:3, :3]),
        "stamp": "1.000000000",
    }


def write_sample(root, camera, index, base_to_parent, camera_to_board):
    metadata = {
        "ok": True,
        "valid": True,
        "id": f"sample_{index}",
        "camera": camera,
        "createdAt": "2026-07-06 00:00:00",
        "board": {
            "type": "checkerboard",
            "columns": 11,
            "rows": 8,
            "squareSizeMm": 3.0,
        },
        "baseFrame": "base_link",
        "parentFrame": "front_camera_link",
        "extrinsicFrame": "rgb_camera_f_link",
        "driverFrame": "camera_f_link",
        "targetFrame": "camera_f_color_optical_frame",
        "parentTransform": plain_transform(base_to_parent, source_frame="front_camera_link"),
        "boardPoseCamera": {
            "translation": [float(value) for value in camera_to_board[:3, 3].tolist()],
            "rotationMatrix": [[float(value) for value in row] for row in camera_to_board[:3, :3].tolist()],
            "reprojectionRmsPx": 0.2,
        },
    }
    (root / f"sample_{index}.json").write_text(json.dumps(metadata), encoding="utf-8")


def checkerboard_flip_transform(columns=11, rows=8, square_size_m=0.003):
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = np.diag([-1.0, -1.0, 1.0])
    matrix[:3, 3] = [(columns - 1) * square_size_m, (rows - 1) * square_size_m, 0.0]
    return matrix


class IdentityTfReader:
    def lookup_transform(self, target_frame, source_frame, timeout_sec=0.0):
        return {
            "ok": True,
            "transform": {
                "targetFrame": target_frame,
                "sourceFrame": source_frame,
                "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
            },
        }


def matrix_from_config_transform(entry):
    return transform(
        (
            entry["translation"]["x"],
            entry["translation"]["y"],
            entry["translation"]["z"],
        ),
        (
            entry["rotation"]["roll"],
            entry["rotation"]["pitch"],
            entry["rotation"]["yaw"],
        ),
    )


def test_solve_camera_extrinsics_recovers_parent_to_camera_transform(tmp_path):
    parent_to_camera = transform((0.07, -0.04, 0.12), (0.12, -0.18, 0.09))
    base_to_board = transform((0.42, 0.18, 0.65), (0.25, -0.08, 0.18))
    poses = [
        ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ((0.04, 0.01, -0.02), (0.32, 0.08, 0.21)),
        ((-0.03, 0.04, 0.02), (-0.22, 0.35, -0.12)),
        ((0.02, -0.05, 0.01), (0.14, -0.31, 0.38)),
        ((-0.04, -0.02, 0.03), (-0.35, -0.18, 0.24)),
        ((0.03, 0.03, -0.04), (0.28, 0.31, -0.27)),
    ]
    for index, (translation, rpy) in enumerate(poses):
        base_to_parent = transform(translation, rpy)
        camera_to_board = np.linalg.inv(parent_to_camera) @ np.linalg.inv(base_to_parent) @ base_to_board
        write_sample(tmp_path, "camera_f", index, base_to_parent, camera_to_board)

    result = solve_camera_extrinsics(
        camera="camera_f",
        output_root=tmp_path,
        config={"enabled": False, "transforms": []},
        min_samples=4,
        tf_reader=IdentityTfReader(),
        enable=True,
    )

    assert result["ok"] is True
    assert result["config"]["enabled"] is True
    primary = next(item for item in result["config"]["transforms"] if item["childFrame"] == "rgb_camera_f_link")
    solved = matrix_from_config_transform(primary)

    assert np.linalg.norm(solved[:3, 3] - parent_to_camera[:3, 3]) < 1e-5
    rotation_delta = solved[:3, :3] @ parent_to_camera[:3, :3].T
    assert abs(math.acos(max(-1.0, min(1.0, (np.trace(rotation_delta) - 1.0) / 2.0)))) < 1e-5


def test_solve_camera_extrinsics_rejects_checkerboard_180_degree_flips(tmp_path):
    parent_to_camera = transform((0.07, -0.04, 0.12), (0.12, -0.18, 0.09))
    base_to_board = transform((0.42, 0.18, 0.65), (0.25, -0.08, 0.18))
    board_flip = checkerboard_flip_transform()
    poses = [
        ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ((0.04, 0.01, -0.02), (0.32, 0.08, 0.21)),
        ((-0.03, 0.04, 0.02), (-0.22, 0.35, -0.12)),
        ((0.02, -0.05, 0.01), (0.14, -0.31, 0.38)),
        ((-0.04, -0.02, 0.03), (-0.35, -0.18, 0.24)),
        ((0.03, 0.03, -0.04), (0.28, 0.31, -0.27)),
    ]
    for index, (translation, rpy) in enumerate(poses):
        base_to_parent = transform(translation, rpy)
        camera_to_board = np.linalg.inv(parent_to_camera) @ np.linalg.inv(base_to_parent) @ base_to_board
        if index % 2 == 1:
            camera_to_board = camera_to_board @ board_flip
        write_sample(tmp_path, "camera_f", index, base_to_parent, camera_to_board)

    result = solve_camera_extrinsics(
        camera="camera_f",
        output_root=tmp_path,
        config={"enabled": False, "transforms": []},
        min_samples=4,
        tf_reader=IdentityTfReader(),
        enable=True,
        method="park",
    )

    assert result["ok"] is False
    assert result["code"] == "CAL-SOLVE-INCOMPLETE"
    camera_result = result["cameraResults"][0]
    assert camera_result["code"] == "CAL-SOLVE-BOARD-FLIP"
    assert camera_result["boardPoseNormalization"]["enabled"] is True
    assert camera_result["boardPoseNormalization"]["flippedSampleCount"] > 0
    assert camera_result["boardPoseNormalization"]["anchorSample"] == "sample_0"
    assert not result.get("config")


def test_solve_camera_extrinsics_rejects_insufficient_samples(tmp_path):
    result = solve_camera_extrinsics(camera="camera_f", output_root=tmp_path, min_samples=4)

    assert result["ok"] is False
    assert result["code"] == "CAL-SOLVE-INCOMPLETE"
    assert result["cameraResults"][0]["code"] == "CAL-SOLVE-SAMPLES"
