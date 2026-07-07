import json
import math
import time
from pathlib import Path

from modules.calibration.projection_check import CAMERA_TARGETS, ROOT_DIR


DEFAULT_SOLVE_MIN_SAMPLES = 12


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def _require_numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Python package numpy is required to solve camera calibration.") from exc
    return np


def _require_cv2():
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV Python package cv2 is required to solve camera calibration.") from exc
    return cv2


def _number(value, default=0.0):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    return parsed if math.isfinite(parsed) else float(default)


def _sample_root(output_root=None):
    return Path(output_root or ROOT_DIR / "output" / "camera_calibration_samples").expanduser().resolve()


def _load_sample_metadata(output_root, camera):
    root = _sample_root(output_root)
    if not root.exists():
        return []

    samples = []
    for metadata_path in sorted(root.glob("*.json"), key=lambda path: path.stat().st_mtime):
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if metadata.get("camera") != camera or not metadata.get("valid", False):
            continue
        if not isinstance(metadata.get("parentTransform"), dict):
            continue
        if not isinstance(metadata.get("boardPoseCamera"), dict):
            continue
        metadata["_metadataPath"] = str(metadata_path)
        samples.append(metadata)
    return samples


def _quat_to_matrix(rotation, np):
    x = _number(rotation.get("x"), 0.0)
    y = _number(rotation.get("y"), 0.0)
    z = _number(rotation.get("z"), 0.0)
    w = _number(rotation.get("w"), 1.0)
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


def _plain_transform_to_matrix(transform, np):
    matrix = np.eye(4, dtype=np.float64)
    translation = transform.get("translation") or {}
    rotation = transform.get("rotation") or {}
    matrix[:3, :3] = _quat_to_matrix(rotation, np)
    matrix[:3, 3] = [
        _number(translation.get("x"), 0.0),
        _number(translation.get("y"), 0.0),
        _number(translation.get("z"), 0.0),
    ]
    return matrix


def _rpy_to_matrix(roll, pitch, yaw, np):
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


def _matrix_to_rpy(rotation):
    sy = math.sqrt(rotation[0, 0] * rotation[0, 0] + rotation[1, 0] * rotation[1, 0])
    singular = sy < 1e-9
    if not singular:
        roll = math.atan2(rotation[2, 1], rotation[2, 2])
        pitch = math.atan2(-rotation[2, 0], sy)
        yaw = math.atan2(rotation[1, 0], rotation[0, 0])
    else:
        roll = math.atan2(-rotation[1, 2], rotation[1, 1])
        pitch = math.atan2(-rotation[2, 0], sy)
        yaw = 0.0
    return roll, pitch, yaw


def _config_transform_to_matrix(transform, np):
    matrix = np.eye(4, dtype=np.float64)
    translation = transform.get("translation") or {}
    rotation = transform.get("rotation") or {}
    matrix[:3, 3] = [
        _number(translation.get("x"), 0.0),
        _number(translation.get("y"), 0.0),
        _number(translation.get("z"), 0.0),
    ]
    matrix[:3, :3] = _rpy_to_matrix(
        _number(rotation.get("roll"), 0.0),
        _number(rotation.get("pitch"), 0.0),
        _number(rotation.get("yaw"), 0.0),
        np,
    )
    return matrix


def _board_pose_to_matrix(board_pose, np):
    rotation = board_pose.get("rotationMatrix")
    translation = board_pose.get("translation")
    if not isinstance(rotation, list) or not isinstance(translation, list):
        raise ValueError("Sample boardPoseCamera is missing rotationMatrix or translation.")
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = np.asarray(rotation, dtype=np.float64).reshape(3, 3)
    matrix[:3, 3] = np.asarray(translation, dtype=np.float64).reshape(3)
    return matrix


def _matrix_to_transform(name, parent, child, matrix, **metadata):
    roll, pitch, yaw = _matrix_to_rpy(matrix[:3, :3])
    transform = {
        "name": name,
        "parentFrame": parent,
        "childFrame": child,
        "translation": {
            "x": float(matrix[0, 3]),
            "y": float(matrix[1, 3]),
            "z": float(matrix[2, 3]),
        },
        "rotation": {
            "roll": float(roll),
            "pitch": float(pitch),
            "yaw": float(yaw),
        },
    }
    transform.update({key: value for key, value in metadata.items() if value is not None})
    return transform


def _transform_field(transform, *names):
    if not isinstance(transform, dict):
        return ""
    for name in names:
        value = transform.get(name)
        if value is not None:
            return str(value).strip().lstrip("/")
    return ""


def _find_transform(transforms, parent, child):
    for transform in transforms:
        if _transform_field(transform, "parentFrame", "parent_frame", "parent") != parent:
            continue
        if _transform_field(transform, "childFrame", "child_frame", "child") != child:
            continue
        return transform
    return None


def _hand_eye_method(method, cv2):
    key = str(method or "tsai").strip().lower()
    mapping = {
        "tsai": getattr(cv2, "CALIB_HAND_EYE_TSAI", 0),
        "park": getattr(cv2, "CALIB_HAND_EYE_PARK", 1),
        "horaud": getattr(cv2, "CALIB_HAND_EYE_HORAUD", 2),
        "andreff": getattr(cv2, "CALIB_HAND_EYE_ANDREFF", 3),
        "daniilidis": getattr(cv2, "CALIB_HAND_EYE_DANIILIDIS", 4),
    }
    return key if key in mapping else "tsai", mapping.get(key, mapping["tsai"])


def _rotation_angle(rotation):
    trace = float(rotation[0, 0] + rotation[1, 1] + rotation[2, 2])
    value = max(-1.0, min(1.0, (trace - 1.0) / 2.0))
    return math.acos(value)


def _solve_metrics(samples, parent_to_optical, np):
    board_poses = []
    reprojection = []
    for sample in samples:
        base_to_parent = _plain_transform_to_matrix(sample["parentTransform"], np)
        camera_to_board = _board_pose_to_matrix(sample["boardPoseCamera"], np)
        board_poses.append(base_to_parent @ parent_to_optical @ camera_to_board)
        rms = sample.get("boardPoseCamera", {}).get("reprojectionRmsPx")
        if rms is not None:
            reprojection.append(_number(rms, 0.0))

    reference = board_poses[0]
    translation_errors = []
    rotation_errors = []
    for pose in board_poses[1:]:
        delta = np.linalg.inv(reference) @ pose
        translation_errors.append(float(np.linalg.norm(delta[:3, 3])))
        rotation_errors.append(float(_rotation_angle(delta[:3, :3])))

    translation_rms = math.sqrt(sum(value * value for value in translation_errors) / len(translation_errors)) if translation_errors else 0.0
    rotation_rms = math.sqrt(sum(value * value for value in rotation_errors) / len(rotation_errors)) if rotation_errors else 0.0
    return {
        "sampleCount": len(samples),
        "reprojectionRmsPx": sum(reprojection) / len(reprojection) if reprojection else None,
        "boardTranslationRmsM": translation_rms,
        "boardRotationRmsDeg": math.degrees(rotation_rms),
    }


def _standard_driver_to_optical(np):
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = _rpy_to_matrix(-math.pi / 2.0, 0.0, -math.pi / 2.0, np)
    return matrix


def _driver_to_target_matrix(target, tf_reader, wait_sec, np):
    if tf_reader is not None:
        result = tf_reader.lookup_transform(target["driverFrame"], target["targetFrame"], timeout_sec=wait_sec)
        if result.get("ok") and isinstance(result.get("transform"), dict):
            return _plain_transform_to_matrix(result["transform"], np), "tf", ""
        detail = result.get("detail") or result.get("code") or "unknown TF lookup error"
        return _standard_driver_to_optical(np), "fallback", detail
    return _standard_driver_to_optical(np), "fallback", "TF reader was not provided."


def _identity_bridge(camera_key, target):
    return {
        "name": f"rgb_{camera_key}_to_driver_{camera_key}",
        "parentFrame": target["extrinsicFrame"],
        "childFrame": target["driverFrame"],
        "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
        "rotation": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
    }


def solve_single_camera(
    camera,
    *,
    output_root=None,
    config=None,
    method="tsai",
    min_samples=DEFAULT_SOLVE_MIN_SAMPLES,
    tf_reader=None,
    wait_sec=0.5,
):
    camera_key = str(camera or "").strip()
    target = CAMERA_TARGETS.get(camera_key)
    if target is None:
        return _result(
            False,
            "CAL-SOLVE-UNKNOWN-CAMERA",
            f"Unknown camera for calibration solve: {camera_key}.",
            camera=camera_key,
            supportedCameras=sorted(CAMERA_TARGETS),
        )

    try:
        np = _require_numpy()
    except RuntimeError as exc:
        return _result(False, "CAL-SOLVE-NUMPY", str(exc), camera=camera_key)
    try:
        cv2 = _require_cv2()
    except RuntimeError as exc:
        return _result(False, "CAL-SOLVE-CV2", str(exc), camera=camera_key)

    samples = _load_sample_metadata(output_root, camera_key)
    min_count = max(3, int(min_samples or DEFAULT_SOLVE_MIN_SAMPLES))
    if len(samples) < min_count:
        return _result(
            False,
            "CAL-SOLVE-SAMPLES",
            f"{camera_key} needs at least {min_count} valid samples, found {len(samples)}.",
            camera=camera_key,
            sampleCount=len(samples),
            minSamples=min_count,
        )

    method_key, method_flag = _hand_eye_method(method, cv2)
    try:
        base_to_parent = [_plain_transform_to_matrix(sample["parentTransform"], np) for sample in samples]
        camera_to_board = [_board_pose_to_matrix(sample["boardPoseCamera"], np) for sample in samples]
        rotations_gripper_to_base = [matrix[:3, :3] for matrix in base_to_parent]
        translations_gripper_to_base = [matrix[:3, 3].reshape(3, 1) for matrix in base_to_parent]
        rotations_target_to_camera = [matrix[:3, :3] for matrix in camera_to_board]
        translations_target_to_camera = [matrix[:3, 3].reshape(3, 1) for matrix in camera_to_board]
        rotation, translation = cv2.calibrateHandEye(
            rotations_gripper_to_base,
            translations_gripper_to_base,
            rotations_target_to_camera,
            translations_target_to_camera,
            method=method_flag,
        )
    except Exception as exc:
        return _result(False, "CAL-SOLVE-PROCESS", str(exc), camera=camera_key, sampleCount=len(samples))

    parent_to_optical = np.eye(4, dtype=np.float64)
    parent_to_optical[:3, :3] = np.asarray(rotation, dtype=np.float64).reshape(3, 3)
    parent_to_optical[:3, 3] = np.asarray(translation, dtype=np.float64).reshape(3)
    if not np.isfinite(parent_to_optical).all():
        return _result(False, "CAL-SOLVE-PROCESS", "OpenCV returned a non-finite transform.", camera=camera_key)

    transforms = config.get("transforms", []) if isinstance(config, dict) else []
    bridge = _find_transform(transforms, target["extrinsicFrame"], target["driverFrame"]) or _identity_bridge(camera_key, target)
    extrinsic_to_driver = _config_transform_to_matrix(bridge, np)
    driver_to_target, driver_target_source, driver_target_warning = _driver_to_target_matrix(target, tf_reader, wait_sec, np)
    parent_to_extrinsic = parent_to_optical @ np.linalg.inv(extrinsic_to_driver @ driver_to_target)
    solved_at = time.strftime("%Y-%m-%d %H:%M:%S")
    metrics = _solve_metrics(samples, parent_to_optical, np)

    primary = _matrix_to_transform(
        f"{target['parentFrame'].replace('/', '_')}_to_{target['extrinsicFrame']}",
        target["parentFrame"],
        target["extrinsicFrame"],
        parent_to_extrinsic,
        source="robot_station_calibration",
        solvedAt=solved_at,
        method=method_key,
        sampleCount=len(samples),
    )
    bridge = dict(bridge)
    bridge.setdefault("source", "robot_station_calibration")

    warnings = []
    if driver_target_warning:
        warnings.append(
            f"{camera_key}: driver->optical TF unavailable ({driver_target_warning}); used standard optical-frame rotation fallback."
        )

    return _result(
        True,
        "CAL-SOLVE-OK",
        f"{camera_key} camera extrinsic solved from {len(samples)} samples.",
        camera=camera_key,
        method=method_key,
        sampleCount=len(samples),
        metrics=metrics,
        primaryTransform=primary,
        bridgeTransform=bridge,
        driverTargetSource=driver_target_source,
        parentToOptical=_matrix_to_transform(
            f"{target['parentFrame'].replace('/', '_')}_to_{target['targetFrame']}",
            target["parentFrame"],
            target["targetFrame"],
            parent_to_optical,
        ),
        warnings=warnings,
    )


def _merge_transforms(existing_config, solved_results):
    existing = existing_config.get("transforms", []) if isinstance(existing_config, dict) else []
    solved_pairs = set()
    additions = []
    for result in solved_results:
        for key in ("primaryTransform", "bridgeTransform"):
            transform = result.get(key)
            if not isinstance(transform, dict):
                continue
            parent = _transform_field(transform, "parentFrame", "parent_frame", "parent")
            child = _transform_field(transform, "childFrame", "child_frame", "child")
            solved_pairs.add((parent, child))
            additions.append(transform)

    kept = []
    for transform in existing:
        if not isinstance(transform, dict):
            continue
        parent = _transform_field(transform, "parentFrame", "parent_frame", "parent")
        child = _transform_field(transform, "childFrame", "child_frame", "child")
        if (parent, child) in solved_pairs:
            continue
        kept.append(transform)
    return kept + additions


def solve_camera_extrinsics(
    *,
    camera="all",
    output_root=None,
    config=None,
    method="tsai",
    min_samples=DEFAULT_SOLVE_MIN_SAMPLES,
    tf_reader=None,
    wait_sec=0.5,
    enable=None,
    allow_partial=False,
):
    config = dict(config or {"enabled": False, "transforms": []})
    requested = str(camera or "all").strip()
    cameras = list(CAMERA_TARGETS) if requested in {"", "all", "*"} else [requested]
    results = [
        solve_single_camera(
            camera_key,
            output_root=output_root,
            config=config,
            method=method,
            min_samples=min_samples,
            tf_reader=tf_reader,
            wait_sec=wait_sec,
        )
        for camera_key in cameras
    ]

    solved = [result for result in results if result.get("ok")]
    failed = [result for result in results if not result.get("ok")]
    if failed and (not solved or not allow_partial):
        return _result(
            False,
            "CAL-SOLVE-INCOMPLETE",
            "Camera calibration solve did not complete for all requested cameras.",
            camera=requested,
            cameraResults=results,
            solvedCameras=[result["camera"] for result in solved],
            failedCameras=[result.get("camera", "") for result in failed],
        )

    output_config = dict(config)
    output_config["transforms"] = _merge_transforms(config, solved)
    if enable is not None:
        output_config["enabled"] = bool(enable)

    warnings = []
    for result in solved:
        warnings.extend(result.get("warnings") or [])
    return _result(
        True,
        "CAL-SOLVE-OK",
        f"Solved {len(solved)} camera extrinsic set(s).",
        camera=requested,
        cameraResults=results,
        solvedCameras=[result["camera"] for result in solved],
        failedCameras=[result.get("camera", "") for result in failed],
        config=output_config,
        warnings=warnings,
    )
