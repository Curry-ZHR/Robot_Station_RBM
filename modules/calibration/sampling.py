import json
import math
import time
from pathlib import Path

from modules.calibration.projection_check import (
    CAMERA_TARGETS,
    ROOT_DIR,
    _camera_matrix,
    _decode_image,
    _require_cv2,
    _require_numpy,
    _safe_filename_token,
    _timestamp_slug,
)
from modules.ros_io import get_camera_image_reader, get_ros_reader, get_tf_transform_reader


DEFAULT_SAMPLE_ROOT = ROOT_DIR / "output" / "camera_calibration_samples"
DEFAULT_BOARD_CONFIG = {
    "type": "checkerboard",
    "columns": 11,
    "rows": 8,
    "squareSizeMm": 3.0,
    "tagSizeMm": 0.0,
    "dictionary": "DICT_4X4_50",
}
DEFAULT_TARGET_SAMPLES_PER_CAMERA = 24


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def _number_or_default(value, default, minimum=None, maximum=None):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = float(default)
    if not math.isfinite(parsed):
        parsed = float(default)
    if minimum is not None:
        parsed = max(float(minimum), parsed)
    if maximum is not None:
        parsed = min(float(maximum), parsed)
    return parsed


def _int_or_default(value, default, minimum=None, maximum=None):
    return int(round(_number_or_default(value, default, minimum=minimum, maximum=maximum)))


def normalize_board_config(payload=None):
    raw = payload if isinstance(payload, dict) else {}
    board = dict(DEFAULT_BOARD_CONFIG)
    aliases = {
        "type": ("type", "boardType", "pattern"),
        "columns": ("columns", "cols", "innerColumns", "innerCols"),
        "rows": ("rows", "innerRows"),
        "squareSizeMm": ("squareSizeMm", "square_size_mm", "squareSize"),
        "tagSizeMm": ("tagSizeMm", "tag_size_mm", "tagSize"),
        "dictionary": ("dictionary", "arucoDictionary", "tagDictionary"),
    }
    for key, names in aliases.items():
        for name in names:
            if raw.get(name) is not None:
                board[key] = raw.get(name)
                break

    board["type"] = str(board["type"] or "checkerboard").strip().lower()
    board["columns"] = _int_or_default(board["columns"], DEFAULT_BOARD_CONFIG["columns"], minimum=2, maximum=80)
    board["rows"] = _int_or_default(board["rows"], DEFAULT_BOARD_CONFIG["rows"], minimum=2, maximum=80)
    board["squareSizeMm"] = _number_or_default(
        board["squareSizeMm"],
        DEFAULT_BOARD_CONFIG["squareSizeMm"],
        minimum=0.001,
        maximum=1000.0,
    )
    board["tagSizeMm"] = _number_or_default(board.get("tagSizeMm"), 0.0, minimum=0.0, maximum=1000.0)
    board["dictionary"] = str(board.get("dictionary") or DEFAULT_BOARD_CONFIG["dictionary"]).strip()
    return board


def _image_extension(image_result):
    content_type = str(image_result.get("contentType") or "").lower()
    format_name = str(image_result.get("format") or "").lower()
    if "png" in content_type or "png" in format_name:
        return ".png"
    if "jpeg" in content_type or "jpg" in content_type or "jpeg" in format_name or "jpg" in format_name:
        return ".jpg"
    return ".img"


def _detect_checkerboard(image, board, cv2, np):
    columns = int(board["columns"])
    rows = int(board["rows"])
    pattern_size = (columns, rows)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
    found, corners = cv2.findChessboardCorners(gray, pattern_size, flags)
    if not found and hasattr(cv2, "findChessboardCornersSB"):
        found, corners = cv2.findChessboardCornersSB(gray, pattern_size)
    if not found or corners is None:
        return {
            "found": False,
            "expectedCornerCount": columns * rows,
            "detectedCornerCount": 0,
            "corners": [],
        }

    corners = np.asarray(corners, dtype=np.float32).reshape(-1, 1, 2)
    try:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.001)
        corners = cv2.cornerSubPix(gray, corners, (7, 7), (-1, -1), criteria)
    except Exception:
        pass

    return {
        "found": True,
        "expectedCornerCount": columns * rows,
        "detectedCornerCount": int(corners.shape[0]),
        "corners": corners,
    }


def _object_points(board, np):
    columns = int(board["columns"])
    rows = int(board["rows"])
    square_size_m = float(board["squareSizeMm"]) / 1000.0
    points = np.zeros((columns * rows, 3), dtype=np.float32)
    points[:, :2] = np.mgrid[0:columns, 0:rows].T.reshape(-1, 2)
    points *= square_size_m
    return points


def _solve_board_pose(board, corners, camera_matrix, distortion, cv2, np):
    object_points = _object_points(board, np)
    if len(corners) != len(object_points):
        return None

    ok, rvec, tvec = cv2.solvePnP(object_points, corners, camera_matrix, distortion, flags=cv2.SOLVEPNP_ITERATIVE)
    if not ok:
        return None

    projected, _ = cv2.projectPoints(object_points, rvec, tvec, camera_matrix, distortion)
    residual = projected.reshape(-1, 2) - corners.reshape(-1, 2)
    reprojection_rms = float(np.sqrt(np.mean(np.sum(residual * residual, axis=1))))
    rotation_matrix, _ = cv2.Rodrigues(rvec)
    return {
        "translation": [float(value) for value in tvec.reshape(-1).tolist()],
        "rotationVector": [float(value) for value in rvec.reshape(-1).tolist()],
        "rotationMatrix": [[float(value) for value in row] for row in rotation_matrix.tolist()],
        "reprojectionRmsPx": reprojection_rms,
    }


def _draw_checkerboard_overlay(image, board, corners, found, cv2):
    overlay = image.copy()
    pattern_size = (int(board["columns"]), int(board["rows"]))
    if found:
        cv2.drawChessboardCorners(overlay, pattern_size, corners, found)
        return overlay
    cv2.putText(
        overlay,
        "Checkerboard not detected",
        (18, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )
    return overlay


def _camera_info_summary(camera_info, camera_matrix, width, height, distortion_model):
    return {
        "key": camera_info.get("key"),
        "topic": camera_info.get("topic"),
        "ageMs": camera_info.get("ageMs"),
        "stale": camera_info.get("stale"),
        "sequence": camera_info.get("sequence"),
        "width": int(width),
        "height": int(height),
        "distortionModel": distortion_model,
        "k": [float(value) for value in camera_matrix.reshape(-1).tolist()],
    }


def _relative_sample_path(path, output_root):
    try:
        return Path(path).expanduser().resolve().relative_to(Path(output_root).expanduser().resolve()).as_posix()
    except ValueError:
        return ""


def _sample_item_from_metadata(metadata_path, output_root):
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        metadata = {}

    stem = metadata_path.stem
    image_path = Path(metadata.get("imagePath") or output_root / f"{stem}.jpg")
    overlay_path = Path(metadata.get("overlayPath") or output_root / f"{stem}_corners.png")
    if not image_path.is_absolute():
        image_path = output_root / image_path
    if not overlay_path.is_absolute():
        overlay_path = output_root / overlay_path

    return {
        "id": metadata.get("id") or stem,
        "camera": metadata.get("camera", ""),
        "displayName": metadata.get("displayName", ""),
        "createdAt": metadata.get("createdAt", ""),
        "imagePath": str(image_path),
        "overlayPath": str(overlay_path),
        "metadataPath": str(metadata_path),
        "imageRelativePath": _relative_sample_path(image_path, output_root),
        "overlayRelativePath": _relative_sample_path(overlay_path, output_root),
        "metadataRelativePath": _relative_sample_path(metadata_path, output_root),
        "imageAgeMs": metadata.get("imageAgeMs"),
        "cameraInfoAgeMs": metadata.get("cameraInfo", {}).get("ageMs") if isinstance(metadata.get("cameraInfo"), dict) else None,
        "parentFrame": metadata.get("parentFrame", ""),
        "baseFrame": metadata.get("baseFrame", ""),
        "parentTfStamp": metadata.get("parentTransform", {}).get("stamp") if isinstance(metadata.get("parentTransform"), dict) else "",
        "cornerCount": metadata.get("cornerCount"),
        "expectedCornerCount": metadata.get("expectedCornerCount"),
        "reprojectionRmsPx": metadata.get("boardPoseCamera", {}).get("reprojectionRmsPx")
        if isinstance(metadata.get("boardPoseCamera"), dict)
        else None,
        "valid": bool(metadata.get("valid", False)),
    }


def list_calibration_samples(output_root=None, limit=240, target_per_camera=DEFAULT_TARGET_SAMPLES_PER_CAMERA):
    root = Path(output_root or DEFAULT_SAMPLE_ROOT).expanduser().resolve()
    items = []
    if root.exists():
        metadata_files = sorted(root.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        for metadata_path in metadata_files[: max(1, int(limit))]:
            items.append(_sample_item_from_metadata(metadata_path, root))

    per_camera = {}
    for camera_key in CAMERA_TARGETS:
        camera_items = [item for item in items if item.get("camera") == camera_key and item.get("valid")]
        per_camera[camera_key] = {
            "count": len(camera_items),
            "targetCount": int(target_per_camera),
            "latest": camera_items[0] if camera_items else None,
        }

    total = sum(entry["count"] for entry in per_camera.values())
    return {
        "ok": True,
        "code": "CAL-SAMPLES-LIST",
        "detail": "Camera calibration samples listed.",
        "outputDir": str(root),
        "targetCount": int(target_per_camera),
        "totalTargetCount": int(target_per_camera) * len(CAMERA_TARGETS),
        "total": total,
        "perCamera": per_camera,
        "samples": items,
    }


def _sample_file_candidates(metadata_path, metadata, output_root):
    stem = metadata_path.stem
    candidates = [metadata_path]
    for key, fallback_name in (
        ("imagePath", f"{stem}.jpg"),
        ("overlayPath", f"{stem}_corners.png"),
    ):
        raw_path = metadata.get(key) if isinstance(metadata, dict) else None
        path = Path(raw_path) if raw_path else output_root / fallback_name
        if not path.is_absolute():
            path = output_root / path
        candidates.append(path)
    return candidates


def _path_inside_root(path, root):
    resolved = Path(path).expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def clear_calibration_samples(camera, output_root=None, target_per_camera=DEFAULT_TARGET_SAMPLES_PER_CAMERA):
    camera_key = str(camera or "").strip()
    clear_all = camera_key in {"all", "*"}
    if not clear_all and camera_key not in CAMERA_TARGETS:
        return _result(False, "CAL-SAMPLES-UNKNOWN-CAMERA", f"Unknown calibration camera: {camera_key}", camera=camera_key)

    root = Path(output_root or DEFAULT_SAMPLE_ROOT).expanduser().resolve()
    deleted_files = []
    skipped_files = []
    errors = []
    deleted_sample_count = 0

    if root.exists():
        for metadata_path in sorted(root.glob("*.json")):
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                metadata = {}

            metadata_camera = str(metadata.get("camera") or "").strip() if isinstance(metadata, dict) else ""
            if not clear_all and metadata_camera != camera_key:
                continue

            deleted_metadata = False
            seen_paths = set()
            for candidate in _sample_file_candidates(metadata_path, metadata, root):
                safe_path = _path_inside_root(candidate, root)
                if safe_path is None:
                    skipped_files.append(str(candidate))
                    continue
                if safe_path in seen_paths:
                    continue
                seen_paths.add(safe_path)
                if not safe_path.exists():
                    continue
                try:
                    safe_path.unlink()
                except OSError as exc:
                    errors.append(f"{safe_path}: {exc}")
                    continue
                deleted_files.append(str(safe_path))
                if safe_path == metadata_path.resolve():
                    deleted_metadata = True
            if deleted_metadata:
                deleted_sample_count += 1

    samples = list_calibration_samples(output_root=root, target_per_camera=target_per_camera)
    if errors:
        return _result(
            False,
            "CAL-SAMPLES-CLEAR",
            f"Failed to delete {len(errors)} calibration sample file(s).",
            camera="all" if clear_all else camera_key,
            deletedSampleCount=deleted_sample_count,
            deletedFileCount=len(deleted_files),
            deletedFiles=deleted_files,
            skippedFiles=skipped_files,
            errors=errors,
            sampling=samples,
        )

    label = "all cameras" if clear_all else camera_key
    return _result(
        True,
        "CAL-SAMPLES-CLEARED",
        f"Cleared {deleted_sample_count} calibration sample(s) for {label}.",
        camera="all" if clear_all else camera_key,
        deletedSampleCount=deleted_sample_count,
        deletedFileCount=len(deleted_files),
        deletedFiles=deleted_files,
        skippedFiles=skipped_files,
        sampling=samples,
    )


def capture_calibration_sample(
    camera,
    board=None,
    base_frame="base_link",
    wait_sec=1.0,
    output_root=None,
    camera_reader=None,
    ros_reader=None,
    tf_reader=None,
):
    camera_key = str(camera or "").strip()
    target = CAMERA_TARGETS.get(camera_key)
    if target is None:
        return _result(
            False,
            "CAL-SAMPLE-UNKNOWN-CAMERA",
            f"Unknown camera for calibration sampling: {camera_key}.",
            camera=camera_key,
            supportedCameras=sorted(CAMERA_TARGETS),
        )

    board_config = normalize_board_config(board)
    if board_config["type"] not in {"checkerboard", "chessboard"}:
        return _result(
            False,
            "CAL-SAMPLE-BOARD",
            f"Unsupported calibration board type for sampling: {board_config['type']}.",
            camera=camera_key,
            board=board_config,
        )

    try:
        np = _require_numpy()
    except RuntimeError as exc:
        return _result(False, "CAL-SAMPLE-NUMPY", str(exc), camera=camera_key)
    try:
        cv2 = _require_cv2()
    except RuntimeError as exc:
        return _result(False, "CAL-SAMPLE-CV2", str(exc), camera=camera_key)

    camera_reader = camera_reader or get_camera_image_reader()
    ros_reader = ros_reader or get_ros_reader()
    tf_reader = tf_reader or get_tf_transform_reader()
    wait_sec = _number_or_default(wait_sec, 1.0, minimum=0.0, maximum=10.0)
    base_frame = str(base_frame or "base_link").strip() or "base_link"

    image_result = camera_reader.read_frame(camera_key, target["imageKind"], timeout_sec=wait_sec)
    if not image_result.get("ok"):
        return _result(
            False,
            "CAL-SAMPLE-IMAGE",
            image_result.get("detail") or "Could not read RGB image.",
            camera=camera_key,
            imageResult=image_result,
        )

    camera_info = ros_reader.read(target["cameraInfoKey"], timeout_sec=wait_sec)
    if not camera_info.get("ok"):
        return _result(
            False,
            "CAL-SAMPLE-CAMERAINFO",
            camera_info.get("detail") or "Could not read CameraInfo.",
            camera=camera_key,
            cameraInfoKey=target["cameraInfoKey"],
            cameraInfoResult=camera_info,
        )

    parent_tf = tf_reader.lookup_transform(base_frame, target["parentFrame"], timeout_sec=wait_sec)
    if not parent_tf.get("ok"):
        return _result(
            False,
            "CAL-SAMPLE-TF",
            parent_tf.get("detail") or f"Could not lookup TF {target['parentFrame']} -> {base_frame}.",
            camera=camera_key,
            baseFrame=base_frame,
            parentFrame=target["parentFrame"],
            tfResult=parent_tf,
        )

    try:
        image = _decode_image(image_result, cv2)
        camera_matrix, distortion, info_width, info_height, distortion_model = _camera_matrix(camera_info)
        detection = _detect_checkerboard(image, board_config, cv2, np)
        if not detection["found"]:
            return _result(
                False,
                "CAL-SAMPLE-CORNERS",
                "Checkerboard corners were not detected in the RGB image.",
                camera=camera_key,
                board=board_config,
                expectedCornerCount=detection["expectedCornerCount"],
                detectedCornerCount=detection["detectedCornerCount"],
            )
        board_pose = _solve_board_pose(board_config, detection["corners"], camera_matrix, distortion, cv2, np)
        overlay = _draw_checkerboard_overlay(image, board_config, detection["corners"], True, cv2)
    except Exception as exc:
        return _result(False, "CAL-SAMPLE-PROCESS", str(exc), camera=camera_key, board=board_config)

    output_dir = Path(output_root or DEFAULT_SAMPLE_ROOT).expanduser().resolve()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = _timestamp_slug()
        sample_id = f"{timestamp}_{_safe_filename_token(camera_key)}"
        image_path = output_dir / f"{sample_id}{_image_extension(image_result)}"
        overlay_path = output_dir / f"{sample_id}_corners.png"
        metadata_path = output_dir / f"{sample_id}.json"
        image_path.write_bytes(image_result.get("body") or b"")
        if not cv2.imwrite(str(overlay_path), overlay):
            raise OSError(f"OpenCV failed to write {overlay_path}")

        corners = detection["corners"].reshape(-1, 2)
        metadata = {
            "ok": True,
            "valid": True,
            "id": sample_id,
            "camera": camera_key,
            "label": target["label"],
            "displayName": target["displayName"],
            "createdAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "board": board_config,
            "imagePath": str(image_path),
            "overlayPath": str(overlay_path),
            "metadataPath": str(metadata_path),
            "imageWidth": int(image.shape[1]),
            "imageHeight": int(image.shape[0]),
            "imageAgeMs": image_result.get("ageMs"),
            "imageSequence": image_result.get("sequence"),
            "cameraInfo": _camera_info_summary(camera_info, camera_matrix, info_width, info_height, distortion_model),
            "baseFrame": base_frame,
            "parentFrame": target["parentFrame"],
            "extrinsicFrame": target["extrinsicFrame"],
            "driverFrame": target["driverFrame"],
            "targetFrame": target["targetFrame"],
            "parentTransform": parent_tf.get("transform"),
            "cornerCount": int(detection["detectedCornerCount"]),
            "expectedCornerCount": int(detection["expectedCornerCount"]),
            "corners": [[float(x), float(y)] for x, y in corners.tolist()],
            "boardPoseCamera": board_pose,
        }
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        return _result(False, "CAL-SAMPLE-SAVE", str(exc), camera=camera_key, board=board_config)

    samples = list_calibration_samples(output_root=output_dir)
    item = _sample_item_from_metadata(metadata_path, output_dir)
    return _result(
        True,
        "CAL-SAMPLE-SAVED",
        f"Camera calibration sample saved to {metadata_path}.",
        camera=camera_key,
        board=board_config,
        sample=item,
        sampling=samples,
    )
