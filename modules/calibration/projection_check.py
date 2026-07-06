import json
import math
import time
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None

from modules.ros_io import (
    get_camera_image_reader,
    get_lidar_point_cloud_reader,
    get_ros_reader,
    get_tf_transform_reader,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = ROOT_DIR / "output" / "camera_projection_checks"

CAMERA_TARGETS = {
    "camera_f": {
        "label": "Front RGB",
        "displayName": "中间相机",
        "imageKind": "color",
        "cameraInfoKey": "camera_f_color_camera_info",
        "cameraInfoTopic": "/camera_f/color/camera_info",
        "parentFrame": "front_camera_link",
        "extrinsicFrame": "rgb_camera_f_link",
        "driverFrame": "camera_f_link",
        "targetFrame": "camera_f_color_optical_frame",
    },
    "camera_l": {
        "label": "Left RGB",
        "displayName": "左相机",
        "imageKind": "color",
        "cameraInfoKey": "camera_l_color_camera_info",
        "cameraInfoTopic": "/camera_l/color/camera_info",
        "parentFrame": "left/link6",
        "extrinsicFrame": "rgb_camera_l_link",
        "driverFrame": "camera_l_link",
        "targetFrame": "camera_l_color_optical_frame",
    },
    "camera_r": {
        "label": "Right RGB",
        "displayName": "右相机",
        "imageKind": "color",
        "cameraInfoKey": "camera_r_color_camera_info",
        "cameraInfoTopic": "/camera_r/color/camera_info",
        "parentFrame": "right/link6",
        "extrinsicFrame": "rgb_camera_r_link",
        "driverFrame": "camera_r_link",
        "targetFrame": "camera_r_color_optical_frame",
    },
}


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def _timestamp_slug(now=None):
    return time.strftime("%Y%m%d-%H%M%S", time.localtime(now or time.time()))


def _safe_filename_token(value):
    text = str(value or "").strip()
    return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in text) or "unknown"


def _require_cv2():
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV Python package cv2 is required to generate projection checks.") from exc
    return cv2


def _require_numpy():
    if np is None:
        raise RuntimeError("Python package numpy is required to generate projection checks.")
    return np


def _decode_image(image_result, cv2):
    body = image_result.get("body")
    if not body:
        raise ValueError(image_result.get("detail") or "Image payload is empty.")
    encoded = np.frombuffer(body, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image payload could not be decoded by OpenCV.")
    return image


def _camera_matrix(camera_info):
    data = camera_info.get("data") if isinstance(camera_info, dict) else None
    if not isinstance(data, dict):
        raise ValueError(camera_info.get("detail") or "CameraInfo data is missing.")

    k_values = data.get("k") or data.get("K")
    if not isinstance(k_values, (list, tuple)) or len(k_values) != 9:
        raise ValueError("CameraInfo.k must contain 9 values.")
    matrix = np.asarray(k_values, dtype=np.float64).reshape(3, 3)

    distortion = data.get("d") or data.get("D") or []
    if distortion is None:
        distortion = []
    distortion = np.asarray(distortion, dtype=np.float64).reshape(-1, 1)

    width = int(data.get("width") or 0)
    height = int(data.get("height") or 0)
    return matrix, distortion, width, height, str(data.get("distortion_model") or "")


def _point_cloud_xyz(lidar_result):
    body = lidar_result.get("body")
    if not body:
        raise ValueError(lidar_result.get("detail") or "Point cloud payload is empty.")
    usable_size = (len(body) // 16) * 16
    if usable_size <= 0:
        raise ValueError("Point cloud payload does not contain packed xyz/intensity points.")
    points = np.frombuffer(body[:usable_size], dtype="<f4").reshape(-1, 4)[:, :3].astype(np.float64)
    finite = np.isfinite(points).all(axis=1)
    return points[finite]


def _quaternion_to_matrix(rotation):
    x = float(rotation.get("x", 0.0) or 0.0)
    y = float(rotation.get("y", 0.0) or 0.0)
    z = float(rotation.get("z", 0.0) or 0.0)
    w = float(rotation.get("w", 1.0) or 1.0)
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm <= 0.0:
        return np.eye(3, dtype=np.float64)
    x /= norm
    y /= norm
    z /= norm
    w /= norm
    return np.asarray(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def _transform_points(points, transform):
    translation = transform.get("translation") or {}
    rotation = transform.get("rotation") or {}
    offset = np.asarray(
        [
            float(translation.get("x", 0.0) or 0.0),
            float(translation.get("y", 0.0) or 0.0),
            float(translation.get("z", 0.0) or 0.0),
        ],
        dtype=np.float64,
    )
    matrix = _quaternion_to_matrix(rotation)
    return points @ matrix.T + offset


def _project_points(points_camera, camera_matrix, distortion, image_shape, cv2):
    if points_camera.size == 0:
        return np.empty((0, 2), dtype=np.float64), np.empty((0,), dtype=np.float64)

    valid = np.isfinite(points_camera).all(axis=1) & (points_camera[:, 2] > 0.05)
    filtered = points_camera[valid]
    if filtered.size == 0:
        return np.empty((0, 2), dtype=np.float64), np.empty((0,), dtype=np.float64)

    image_points, _ = cv2.projectPoints(
        filtered.reshape(-1, 1, 3),
        np.zeros((3, 1), dtype=np.float64),
        np.zeros((3, 1), dtype=np.float64),
        camera_matrix,
        distortion,
    )
    image_points = image_points.reshape(-1, 2)
    height, width = image_shape[:2]
    inside = (
        np.isfinite(image_points).all(axis=1)
        & (image_points[:, 0] >= 0)
        & (image_points[:, 0] < width)
        & (image_points[:, 1] >= 0)
        & (image_points[:, 1] < height)
    )
    return image_points[inside], filtered[inside, 2]


def _draw_projection(image, image_points, depths, cv2, max_draw_points=25000):
    overlay = image.copy()
    if image_points.size == 0:
        cv2.putText(
            overlay,
            "No projected points inside image",
            (18, 32),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        return overlay

    if len(image_points) > max_draw_points:
        step = max(1, int(math.ceil(len(image_points) / float(max_draw_points))))
        image_points = image_points[::step]
        depths = depths[::step]

    low = float(np.percentile(depths, 2)) if len(depths) else 0.0
    high = float(np.percentile(depths, 98)) if len(depths) else 1.0
    if high <= low:
        high = low + 1.0
    normalized = np.clip((depths - low) * 255.0 / (high - low), 0, 255).astype(np.uint8)
    color_map = getattr(cv2, "COLORMAP_TURBO", cv2.COLORMAP_JET)
    colors = cv2.applyColorMap(normalized.reshape(-1, 1), color_map).reshape(-1, 3)

    for point, color in zip(image_points, colors):
        x = int(round(float(point[0])))
        y = int(round(float(point[1])))
        cv2.circle(overlay, (x, y), 2, (int(color[0]), int(color[1]), int(color[2])), -1, lineType=cv2.LINE_AA)
    return overlay


def _write_metadata(path, metadata):
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def create_projection_check(
    camera,
    camera_reader=None,
    lidar_reader=None,
    ros_reader=None,
    tf_reader=None,
    output_root=None,
    cloud_key="rslidar_points",
    max_points=60000,
    wait_sec=1.0,
):
    camera_key = str(camera or "").strip()
    target = CAMERA_TARGETS.get(camera_key)
    if target is None:
        return _result(
            False,
            "CAL-PROJ-UNKNOWN-CAMERA",
            f"Unknown camera for projection check: {camera_key}.",
            camera=camera_key,
            supportedCameras=sorted(CAMERA_TARGETS),
        )

    try:
        _require_numpy()
    except RuntimeError as exc:
        return _result(False, "CAL-PROJ-NUMPY", str(exc), camera=camera_key)
    try:
        cv2 = _require_cv2()
    except RuntimeError as exc:
        return _result(False, "CAL-PROJ-CV2", str(exc), camera=camera_key)

    camera_reader = camera_reader or get_camera_image_reader()
    lidar_reader = lidar_reader or get_lidar_point_cloud_reader()
    ros_reader = ros_reader or get_ros_reader()
    tf_reader = tf_reader or get_tf_transform_reader()

    image_result = camera_reader.read_frame(camera_key, target["imageKind"], timeout_sec=wait_sec)
    if not image_result.get("ok"):
        return _result(
            False,
            "CAL-PROJ-IMAGE",
            image_result.get("detail") or "Could not read RGB image.",
            camera=camera_key,
            imageResult=image_result,
        )

    camera_info = ros_reader.read(target["cameraInfoKey"], timeout_sec=wait_sec)
    if not camera_info.get("ok"):
        return _result(
            False,
            "CAL-PROJ-CAMERAINFO",
            camera_info.get("detail") or "Could not read CameraInfo.",
            camera=camera_key,
            cameraInfoKey=target["cameraInfoKey"],
            cameraInfoResult=camera_info,
        )

    lidar_result = lidar_reader.read_frame(cloud_key, timeout_sec=wait_sec, max_points=max_points)
    if not lidar_result.get("ok"):
        return _result(
            False,
            "CAL-PROJ-LIDAR",
            lidar_result.get("detail") or "Could not read point cloud.",
            camera=camera_key,
            cloud=cloud_key,
            lidarResult=lidar_result,
        )

    source_frame = str(lidar_result.get("frameId") or "").strip()
    if not source_frame:
        return _result(
            False,
            "CAL-PROJ-LIDAR",
            "Point cloud frame_id is empty; TF lookup cannot be performed.",
            camera=camera_key,
            cloud=cloud_key,
        )

    target_frame = target["targetFrame"]
    tf_result = tf_reader.lookup_transform(target_frame, source_frame, timeout_sec=wait_sec)
    if not tf_result.get("ok"):
        return _result(
            False,
            "CAL-PROJ-TF",
            tf_result.get("detail") or f"Could not lookup TF {source_frame} -> {target_frame}.",
            camera=camera_key,
            cloud=cloud_key,
            targetFrame=target_frame,
            sourceFrame=source_frame,
            tfResult=tf_result,
        )

    try:
        image = _decode_image(image_result, cv2)
        camera_matrix, distortion, info_width, info_height, distortion_model = _camera_matrix(camera_info)
        points = _point_cloud_xyz(lidar_result)
        points_camera = _transform_points(points, tf_result["transform"])
        image_points, depths = _project_points(points_camera, camera_matrix, distortion, image.shape, cv2)
        overlay = _draw_projection(image, image_points, depths, cv2)
    except Exception as exc:
        return _result(
            False,
            "CAL-PROJ-PROCESS",
            str(exc),
            camera=camera_key,
            cloud=cloud_key,
            targetFrame=target_frame,
            sourceFrame=source_frame,
        )

    output_dir = Path(output_root or DEFAULT_OUTPUT_ROOT).expanduser().resolve()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = _timestamp_slug()
        stem = f"{timestamp}_{_safe_filename_token(camera_key)}_{_safe_filename_token(cloud_key)}"
        image_path = output_dir / f"{stem}.png"
        metadata_path = output_dir / f"{stem}.json"
        if not cv2.imwrite(str(image_path), overlay):
            raise OSError(f"OpenCV failed to write {image_path}")

        metadata = {
            "ok": True,
            "camera": camera_key,
            "cameraLabel": target["label"],
            "cloud": cloud_key,
            "imagePath": str(image_path),
            "metadataPath": str(metadata_path),
            "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "targetFrame": target_frame,
            "sourceFrame": source_frame,
            "inputPointCount": int(points.shape[0]),
            "projectedPointCount": int(image_points.shape[0]),
            "drawnPointCount": int(min(image_points.shape[0], 25000)),
            "imageWidth": int(image.shape[1]),
            "imageHeight": int(image.shape[0]),
            "cameraInfoWidth": info_width,
            "cameraInfoHeight": info_height,
            "distortionModel": distortion_model,
            "imageAgeMs": image_result.get("ageMs"),
            "lidarAgeMs": lidar_result.get("ageMs"),
            "lidarStamp": lidar_result.get("stamp"),
            "tf": tf_result.get("transform"),
        }
        _write_metadata(metadata_path, metadata)
    except Exception as exc:
        return _result(
            False,
            "CAL-PROJ-SAVE",
            str(exc),
            camera=camera_key,
            cloud=cloud_key,
            targetFrame=target_frame,
            sourceFrame=source_frame,
        )

    detail = f"Projection check saved to {image_path}."
    if image_points.shape[0] == 0:
        detail = f"Projection check saved to {image_path}, but no LiDAR points landed inside the image."

    return _result(
        True,
        "CAL-PROJ-SAVED",
        detail,
        camera=camera_key,
        cloud=cloud_key,
        imagePath=str(image_path),
        metadataPath=str(metadata_path),
        outputDir=str(output_dir),
        targetFrame=target_frame,
        sourceFrame=source_frame,
        inputPointCount=int(points.shape[0]),
        projectedPointCount=int(image_points.shape[0]),
    )
