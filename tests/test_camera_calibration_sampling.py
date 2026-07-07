import json
from pathlib import Path

import numpy as np
import pytest

from modules.calibration.sampling import clear_calibration_samples, capture_calibration_sample, list_calibration_samples


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
            "contentType": "image/jpeg",
            "format": "jpeg",
            "ageMs": 18,
            "sequence": 7,
        }


class FakeRosReader:
    def __init__(self, width=560, height=440):
        self.width = width
        self.height = height

    def read(self, key, timeout_sec=0.0):
        return {
            "ok": True,
            "code": "ROS-R-OK",
            "detail": "camera info",
            "key": key,
            "topic": f"/{key}",
            "ageMs": 21,
            "stale": False,
            "sequence": 4,
            "data": {
                "width": self.width,
                "height": self.height,
                "distortion_model": "plumb_bob",
                "k": [600.0, 0.0, self.width / 2.0, 0.0, 600.0, self.height / 2.0, 0.0, 0.0, 1.0],
                "d": [0.0, 0.0, 0.0, 0.0, 0.0],
            },
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
                "translation": {"x": 0.1, "y": 0.2, "z": 0.3},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                "stamp": "1.000000000",
            },
        }


def encoded_checkerboard(columns=11, rows=8, square_px=40, margin_px=40):
    image_width = (columns + 1) * square_px + margin_px * 2
    image_height = (rows + 1) * square_px + margin_px * 2
    image = np.full((image_height, image_width, 3), 255, dtype=np.uint8)
    for row in range(rows + 1):
        for column in range(columns + 1):
            color = 0 if (row + column) % 2 == 0 else 255
            x0 = margin_px + column * square_px
            y0 = margin_px + row * square_px
            image[y0:y0 + square_px, x0:x0 + square_px] = color
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    return encoded.tobytes(), image_width, image_height


def encoded_blank_image(width=560, height=440):
    image = np.full((height, width, 3), 240, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    return encoded.tobytes()


def test_capture_calibration_sample_saves_image_overlay_and_metadata(tmp_path):
    body, width, height = encoded_checkerboard()
    result = capture_calibration_sample(
        camera="camera_f",
        board={"type": "checkerboard", "columns": 11, "rows": 8, "squareSizeMm": 3.0},
        camera_reader=FakeCameraReader(body),
        ros_reader=FakeRosReader(width, height),
        tf_reader=FakeTfReader(),
        output_root=tmp_path,
    )

    assert result["ok"] is True
    assert result["code"] == "CAL-SAMPLE-SAVED"
    assert result["sample"]["cornerCount"] == 88
    assert result["sample"]["expectedCornerCount"] == 88

    image_path = Path(result["sample"]["imagePath"])
    overlay_path = Path(result["sample"]["overlayPath"])
    metadata_path = Path(result["sample"]["metadataPath"])
    assert image_path.exists()
    assert overlay_path.exists()
    assert metadata_path.exists()

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["camera"] == "camera_f"
    assert metadata["baseFrame"] == "base_link"
    assert metadata["parentFrame"] == "front_camera_link"
    assert metadata["cornerCount"] == 88
    assert metadata["boardPoseCamera"]["reprojectionRmsPx"] >= 0.0

    samples = list_calibration_samples(output_root=tmp_path)
    assert samples["perCamera"]["camera_f"]["count"] == 1
    assert samples["total"] == 1


def test_capture_calibration_sample_rejects_images_without_checkerboard(tmp_path):
    result = capture_calibration_sample(
        camera="camera_f",
        board={"type": "checkerboard", "columns": 11, "rows": 8, "squareSizeMm": 3.0},
        camera_reader=FakeCameraReader(encoded_blank_image()),
        ros_reader=FakeRosReader(),
        tf_reader=FakeTfReader(),
        output_root=tmp_path,
    )

    assert result["ok"] is False
    assert result["code"] == "CAL-SAMPLE-CORNERS"
    assert not list(tmp_path.glob("*.json"))


def test_clear_calibration_samples_removes_only_requested_camera_files(tmp_path):
    body, width, height = encoded_checkerboard()
    front_result = capture_calibration_sample(
        camera="camera_f",
        board={"type": "checkerboard", "columns": 11, "rows": 8, "squareSizeMm": 3.0},
        camera_reader=FakeCameraReader(body),
        ros_reader=FakeRosReader(width, height),
        tf_reader=FakeTfReader(),
        output_root=tmp_path,
    )
    left_result = capture_calibration_sample(
        camera="camera_l",
        board={"type": "checkerboard", "columns": 11, "rows": 8, "squareSizeMm": 3.0},
        camera_reader=FakeCameraReader(body),
        ros_reader=FakeRosReader(width, height),
        tf_reader=FakeTfReader(),
        output_root=tmp_path,
    )
    assert front_result["ok"] is True
    assert left_result["ok"] is True

    front_paths = [
        Path(front_result["sample"]["imagePath"]),
        Path(front_result["sample"]["overlayPath"]),
        Path(front_result["sample"]["metadataPath"]),
    ]
    left_paths = [
        Path(left_result["sample"]["imagePath"]),
        Path(left_result["sample"]["overlayPath"]),
        Path(left_result["sample"]["metadataPath"]),
    ]

    result = clear_calibration_samples("camera_f", output_root=tmp_path)

    assert result["ok"] is True
    assert result["code"] == "CAL-SAMPLES-CLEARED"
    assert result["deletedSampleCount"] == 1
    assert result["sampling"]["perCamera"]["camera_f"]["count"] == 0
    assert result["sampling"]["perCamera"]["camera_l"]["count"] == 1
    assert all(not path.exists() for path in front_paths)
    assert all(path.exists() for path in left_paths)
