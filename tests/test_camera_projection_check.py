import json
from pathlib import Path

import numpy as np
import pytest

from modules.calibration.projection_check import create_projection_check


cv2 = pytest.importorskip("cv2")


class FakeCameraReader:
    def __init__(self, body):
        self.body = body

    def read_frame(self, camera, kind, timeout_sec=0.0):
        return {
            "ok": True,
            "code": "CAM-R-FRAME",
            "detail": "frame",
            "body": self.body,
            "ageMs": 12,
        }


class FakeRosReader:
    def read(self, key, timeout_sec=0.0):
        return {
            "ok": True,
            "code": "ROS-R-OK",
            "detail": "camera info",
            "data": {
                "width": 100,
                "height": 80,
                "distortion_model": "plumb_bob",
                "k": [80.0, 0.0, 50.0, 0.0, 80.0, 40.0, 0.0, 0.0, 1.0],
                "d": [0.0, 0.0, 0.0, 0.0, 0.0],
            },
        }


class FakeLidarReader:
    def __init__(self, body):
        self.body = body

    def read_frame(self, key, timeout_sec=0.0, max_points=None):
        return {
            "ok": True,
            "code": "LDR-R-FRAME",
            "detail": "cloud",
            "body": self.body,
            "frameId": "rslidar",
            "pointCount": 4,
            "sourcePointCount": 4,
            "stamp": "1.000000000",
            "ageMs": 8,
        }


class FakeTfReader:
    def lookup_transform(self, target_frame, source_frame, timeout_sec=0.0):
        return {
            "ok": True,
            "code": "TF-R-OK",
            "detail": "tf",
            "transform": {
                "targetFrame": target_frame,
                "sourceFrame": source_frame,
                "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                "stamp": "1.000000000",
            },
        }


def encoded_test_image():
    image = np.zeros((80, 100, 3), dtype=np.uint8)
    image[:, :] = (24, 32, 40)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    return encoded.tobytes()


def packed_test_points():
    points = np.asarray(
        [
            [0.0, 0.0, 2.0, 1.0],
            [0.2, 0.0, 2.0, 1.0],
            [-0.2, 0.1, 2.0, 1.0],
            [3.0, 3.0, 1.0, 1.0],
        ],
        dtype="<f4",
    )
    return points.tobytes()


def test_create_projection_check_saves_overlay_and_metadata(tmp_path):
    result = create_projection_check(
        camera="camera_f",
        camera_reader=FakeCameraReader(encoded_test_image()),
        lidar_reader=FakeLidarReader(packed_test_points()),
        ros_reader=FakeRosReader(),
        tf_reader=FakeTfReader(),
        output_root=tmp_path,
    )

    assert result["ok"] is True
    assert result["code"] == "CAL-PROJ-SAVED"
    assert result["projectedPointCount"] > 0

    image_path = Path(result["imagePath"])
    metadata_path = Path(result["metadataPath"])
    assert image_path.exists()
    assert metadata_path.exists()

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["camera"] == "camera_f"
    assert metadata["targetFrame"] == "camera_f_color_optical_frame"
    assert metadata["sourceFrame"] == "rslidar"
    assert metadata["projectedPointCount"] == result["projectedPointCount"]


def test_create_projection_check_rejects_unknown_camera(tmp_path):
    result = create_projection_check(camera="camera_x", output_root=tmp_path)

    assert result["ok"] is False
    assert result["code"] == "CAL-PROJ-UNKNOWN-CAMERA"
