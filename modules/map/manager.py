import json
import os
import shutil
import signal
import struct
import subprocess
import threading
import time
from pathlib import Path

from modules.logger import get_logger


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_TMP_DIR = ROOT_DIR / "modules" / "map" / "data" / "tmp"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "modules" / "map" / "data"
DEFAULT_MAPPER_COMMAND = (
    "ros2",
    "run",
    "robot_station_mapper",
    "robot_station_mapper_cli",
)
LOGGER = get_logger()
MAPPING_PROGRESS_LABELS = {
    "capturing": "采集点云",
    "filtering": "合并点云",
    "registering": "配准中",
    "registering_ndt": "NDT 配准",
    "registering_gicp": "GICP 配准",
    "writing_map": "写入地图",
    "done": "完成",
    "failed": "失败",
}
PCD_FLOAT32_FIELDS = ("x", "y", "z", "intensity")
PCD_FIELD_FORMATS = {
    ("F", 4): "f",
    ("F", 8): "d",
    ("I", 1): "b",
    ("I", 2): "h",
    ("I", 4): "i",
    ("U", 1): "B",
    ("U", 2): "H",
    ("U", 4): "I",
}


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def mapping_result_status(result):
    if result.get("ok"):
        return 200
    mapping = {
        "MAP-ACTION": 400,
        "MAP-PAYLOAD": 400,
        "MAP-NOSESSION": 409,
        "MAP-BUSY": 409,
        "MAP-NOKEYFRAME": 409,
        "MAP-NOTFOUND": 404,
        "MAP-PCD": 422,
        "MAP-HISTORY": 500,
        "MAP-DEPENDENCY": 503,
        "MAP-CAPTURE-FAILED": 500,
        "MAP-SAVE-FAILED": 500,
    }
    return mapping.get(result.get("code", ""), 500)


MAPPING_SAVED_FIELDS = ("savedAt", "savedMapPath", "savedPackagePath", "savedMapPackage")


def _clamp_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _clamp_float(value, default, minimum, maximum):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _clean_topic(value, default):
    text = str(value or "").strip()
    if not text:
        return default
    return text if text.startswith("/") else f"/{text}"


def _safe_map_stem(value, default):
    text = str(value or default or "").strip()
    if text.lower().endswith(".pcd"):
        text = text[:-4]
    stem = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in text)
    stem = stem.strip(" .")
    if not stem:
        stem = str(default or "mapping").strip() or "mapping"
    if stem in {"tmp", "tmp_map"}:
        stem = f"{stem}_saved"
    return stem


def _session_id():
    return time.strftime("%Y%m%d_%H%M%S")


def _number_or_none(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def _remove_path(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _parse_pcd_number(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _pcd_error(message):
    raise ValueError(message)


def _read_pcd_payload(path):
    header = {}
    header_order = []
    with Path(path).open("rb") as handle:
        while True:
            raw_line = handle.readline()
            if raw_line == b"":
                _pcd_error("PCD header is missing DATA line.")
            text = raw_line.decode("ascii", errors="replace").strip()
            if not text or text.startswith("#"):
                continue
            parts = text.split()
            key = parts[0].upper()
            values = parts[1:]
            header[key] = values
            header_order.append(key)
            if key == "DATA":
                break
        data = handle.read()

    if "DATA" not in header_order:
        _pcd_error("PCD header is missing DATA line.")
    data_kind = (header.get("DATA") or [""])[0].lower()
    if data_kind not in {"binary", "ascii"}:
        _pcd_error(f"Unsupported PCD DATA mode: {data_kind or 'unknown'}.")

    fields = header.get("FIELDS") or []
    if not fields:
        _pcd_error("PCD header is missing FIELDS.")
    sizes = [_parse_pcd_number(value, 0) for value in (header.get("SIZE") or [])]
    types = [str(value).upper() for value in (header.get("TYPE") or [])]
    counts = [_parse_pcd_number(value, 1) for value in (header.get("COUNT") or [])] or [1] * len(fields)
    if not (len(fields) == len(sizes) == len(types) == len(counts)):
        _pcd_error("PCD field metadata is inconsistent.")

    point_count = _parse_pcd_number((header.get("POINTS") or [None])[0], 0)
    if point_count <= 0:
        width = _parse_pcd_number((header.get("WIDTH") or [None])[0], 0)
        height = _parse_pcd_number((header.get("HEIGHT") or [1])[0], 1)
        point_count = max(0, width * height)
    if point_count <= 0:
        _pcd_error("PCD file does not declare any points.")

    offsets = {}
    point_step = 0
    for field, size, count in zip(fields, sizes, counts):
        offsets[field] = point_step
        point_step += size * count
    if point_step <= 0:
        _pcd_error("PCD point step is invalid.")
    missing = [field for field in ("x", "y", "z") if field not in offsets]
    if missing:
        _pcd_error(f"PCD file missing required field(s): {', '.join(missing)}.")

    if data_kind == "ascii":
        body = bytearray(point_count * 16)
        rows = data.decode("ascii", errors="replace").splitlines()
        written = 0
        for row in rows:
            if not row.strip() or row.lstrip().startswith("#"):
                continue
            values = row.split()
            if len(values) < len(fields):
                continue
            row_values = {field: values[index] for index, field in enumerate(fields)}
            x = float(row_values["x"])
            y = float(row_values["y"])
            z = float(row_values["z"])
            intensity = float(row_values.get("intensity", 0.0))
            struct.pack_into("<ffff", body, written * 16, x, y, z, intensity)
            written += 1
            if written >= point_count:
                break
        return bytes(body[:written * 16]), written, point_count

    expected_bytes = point_count * point_step
    if len(data) < expected_bytes:
        _pcd_error("PCD binary payload is shorter than the declared point count.")
    payload = data[:expected_bytes]

    direct_layout = (
        point_step == 16
        and all(field in offsets for field in PCD_FLOAT32_FIELDS)
        and all(types[fields.index(field)] == "F" and sizes[fields.index(field)] == 4 and counts[fields.index(field)] == 1 for field in PCD_FLOAT32_FIELDS)
        and [offsets[field] for field in PCD_FLOAT32_FIELDS] == [0, 4, 8, 12]
    )
    if direct_layout:
        return payload, point_count, point_count

    unpackers = {}
    for field in ("x", "y", "z", "intensity"):
        if field not in offsets:
            continue
        index = fields.index(field)
        fmt = PCD_FIELD_FORMATS.get((types[index], sizes[index]))
        if fmt is None:
            _pcd_error(f"Unsupported PCD field format for {field}.")
        unpackers[field] = struct.Struct("<" + fmt)

    body = bytearray(point_count * 16)
    written = 0
    for point_index in range(point_count):
        base = point_index * point_step
        try:
            x = float(unpackers["x"].unpack_from(payload, base + offsets["x"])[0])
            y = float(unpackers["y"].unpack_from(payload, base + offsets["y"])[0])
            z = float(unpackers["z"].unpack_from(payload, base + offsets["z"])[0])
            intensity = 0.0
            if "intensity" in unpackers:
                intensity = float(unpackers["intensity"].unpack_from(payload, base + offsets["intensity"])[0])
        except (KeyError, struct.error) as exc:
            _pcd_error(f"Failed to read PCD point payload: {exc}")
        struct.pack_into("<ffff", body, written * 16, x, y, z, intensity)
        written += 1
    return bytes(body), written, point_count


def _progress_payload(phase, settings=None, raw=None, detail=None):
    settings = settings or {}
    raw = raw or {}
    phase = str(phase or "capturing").strip() or "capturing"
    label = MAPPING_PROGRESS_LABELS.get(phase, phase)
    target = _number_or_none(raw.get("targetFrames")) or _number_or_none(settings.get("frameCount")) or 10
    captured = _number_or_none(raw.get("capturedFrames"))
    if detail is None:
        if phase == "capturing" and captured is not None:
            detail = f"正在采集点云：{int(captured)}/{int(target)} 帧。"
        elif phase == "capturing":
            detail = f"正在采集 {int(target)} 帧点云。"
        elif phase == "filtering":
            detail = "正在合并并降采样点云。"
        elif phase == "registering":
            detail = "正在进行 NDT/GICP 配准。"
        elif phase == "registering_ndt":
            detail = "正在进行 NDT 粗配准。"
        elif phase == "registering_gicp":
            detail = "正在进行 GICP 精配准。"
        elif phase == "writing_map":
            detail = "正在写入 keyframe 和临时地图。"
        elif phase == "done":
            detail = "点云 keyframe 已写入地图。"
        elif phase == "failed":
            detail = "点云建图失败。"
        else:
            detail = label
    progress = {
        "phase": phase,
        "label": label,
        "detail": detail,
        "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if captured is not None:
        progress["capturedFrames"] = int(captured)
    if target is not None:
        progress["targetFrames"] = int(target)
    return progress


class MappingManager:
    def __init__(self, tmp_root=None, output_root=None, mapper_command=None):
        self.tmp_root = Path(tmp_root or os.environ.get("ROBOT_STATION_MAPPING_TMP_DIR", DEFAULT_TMP_DIR))
        self.output_root = Path(output_root or os.environ.get("ROBOT_STATION_MAPPING_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))
        command_text = os.environ.get("ROBOT_STATION_MAPPER_COMMAND", "")
        if mapper_command is not None:
            self.mapper_command = tuple(mapper_command)
        elif command_text.strip():
            self.mapper_command = tuple(command_text.split())
        else:
            self.mapper_command = DEFAULT_MAPPER_COMMAND
        self._lock = threading.RLock()
        self._session = None
        self._job_thread = None
        self._job_process = None
        self._resetting = False

    def status(self):
        with self._lock:
            self._refresh_progress_locked()
            return _result(
                True,
                "MAP-STATUS",
                "Mapping status loaded.",
                session=self._session_payload_locked(),
                busy=self._is_busy_locked(),
                tmpRoot=str(self.tmp_root),
                outputRoot=str(self.output_root),
                mapperCommand=list(self.mapper_command),
            )

    def read_map_frame(self):
        with self._lock:
            if self._session is None:
                return _result(False, "MAP-NOSESSION", "No mapping session is active.")
            session = dict(self._session)

        map_path = Path(session.get("tmpMapPath", ""))
        session_dir = Path(session.get("sessionDir", ""))
        try:
            resolved_map = map_path.resolve()
            resolved_map.relative_to(session_dir.resolve())
        except Exception:
            return _result(False, "MAP-NOTFOUND", "Temporary map path is outside the active mapping session.")
        if not resolved_map.exists():
            return _result(False, "MAP-NOTFOUND", "Temporary map file does not exist.")
        if not resolved_map.is_file():
            return _result(False, "MAP-NOTFOUND", "Temporary map path is not a file.")

        try:
            body, point_count, source_point_count = _read_pcd_payload(resolved_map)
        except ValueError as exc:
            return _result(False, "MAP-PCD", f"Temporary map PCD could not be read: {exc}")
        except OSError as exc:
            return _result(False, "MAP-NOTFOUND", f"Temporary map file could not be read: {exc}")

        stat_result = resolved_map.stat()
        return _result(
            True,
            "MAP-MAP-FRAME",
            "Temporary mapping point cloud loaded.",
            body=body,
            contentType="application/octet-stream",
            pointCount=point_count,
            sourcePointCount=source_point_count,
            strideFloats=4,
            fields=list(PCD_FLOAT32_FIELDS),
            sessionId=session.get("id", ""),
            captureCount=int(session.get("captureCount", 0) or 0),
            sizeBytes=int(stat_result.st_size),
            mtimeMs=int(stat_result.st_mtime * 1000),
            mapPath=str(resolved_map),
        )

    def start(self, payload=None):
        payload = payload or {}
        if not isinstance(payload, dict):
            return _result(False, "MAP-PAYLOAD", "Payload must be a JSON object.")
        with self._lock:
            if self._is_busy_locked():
                return _result(False, "MAP-BUSY", "Mapping capture is running.", session=self._session_payload_locked())
            temp_cleanup = self._clear_tmp_root()
            if temp_cleanup["errors"]:
                return _result(
                    False,
                    "MAP-TMP-CLEANUP",
                    "Failed to clear temporary mapping files.",
                    tempCleanup=temp_cleanup,
                    session=self._session_payload_locked(),
                )

            session_id = str(payload.get("sessionId") or _session_id()).strip() or _session_id()
            session_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in session_id)
            session_dir = self.tmp_root / session_id
            keyframe_dir = session_dir / "keyframes"
            history_dir = session_dir / ".history"
            session_dir.mkdir(parents=True, exist_ok=True)
            keyframe_dir.mkdir(parents=True, exist_ok=True)
            history_dir.mkdir(parents=True, exist_ok=True)

            settings = self._settings_from_payload(payload)
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            self._session = {
                "id": session_id,
                "status": "ready",
                "detail": "建图会话已创建。",
                "createdAt": now,
                "updatedAt": now,
                "sessionDir": str(session_dir),
                "keyframeDir": str(keyframe_dir),
                "historyDir": str(history_dir),
                "tmpMapPath": str(session_dir / "map_tmp.pcd"),
                "manifestPath": str(session_dir / "manifest.json"),
                "lastResultPath": str(session_dir / "last_result.json"),
                "progressPath": str(session_dir / "progress.json"),
                "logPath": str(session_dir / "mapper.log"),
                "settings": settings,
                "keyframes": [],
                "deleteHistory": [],
                "lastResult": None,
                "lastError": "",
                "captureCount": 0,
                "progress": None,
            }
            self._write_manifest_locked()
            return _result(
                True,
                "MAP-STARTED",
                "Mapping session started.",
                session=self._session_payload_locked(),
                tempCleanup=temp_cleanup,
            )

    def capture(self, payload=None):
        payload = payload or {}
        if not isinstance(payload, dict):
            return _result(False, "MAP-PAYLOAD", "Payload must be a JSON object.")
        with self._lock:
            if self._session is None:
                return _result(False, "MAP-NOSESSION", "Start a mapping session before capturing point clouds.")
            if self._is_busy_locked():
                return _result(False, "MAP-BUSY", "Mapping capture is already running.", session=self._session_payload_locked())

            settings = {
                **self._session.get("settings", {}),
                **self._settings_from_payload(payload, base=self._session.get("settings", {})),
            }
            self._session["settings"] = settings
            self._session["status"] = "capturing"
            self._session["progress"] = _progress_payload("capturing", settings=settings, raw={"capturedFrames": 0})
            self._session["detail"] = self._session["progress"]["detail"]
            self._session["lastError"] = ""
            self._session["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
            progress_path = Path(self._session["progressPath"])
            try:
                progress_path.unlink()
            except FileNotFoundError:
                pass
            self._write_manifest_locked()
            rollback = self._capture_rollback_locked()
            session_snapshot = dict(self._session)
            session_snapshot["_rollback"] = rollback

            self._job_thread = threading.Thread(
                target=self._run_capture_job,
                args=(session_snapshot, settings),
                name="mapping_capture_job",
                daemon=True,
            )
            self._job_thread.start()
            return _result(True, "MAP-CAPTURE-STARTED", "Mapping capture started.", session=self._session_payload_locked())

    def save(self, payload=None):
        payload = payload or {}
        if not isinstance(payload, dict):
            return _result(False, "MAP-PAYLOAD", "Payload must be a JSON object.")
        with self._lock:
            if self._session is None:
                return _result(False, "MAP-NOSESSION", "No mapping session is active.")
            if self._is_busy_locked():
                return _result(False, "MAP-BUSY", "Mapping capture is running.", session=self._session_payload_locked())
            source = Path(self._session["tmpMapPath"])
            if not source.exists():
                return _result(False, "MAP-NOTFOUND", "Temporary map file does not exist.", session=self._session_payload_locked())
            safe_stem = _safe_map_stem(payload.get("name"), self._session["id"])
            self.output_root.mkdir(parents=True, exist_ok=True)
            package_dir = self.output_root / safe_stem
            staging_dir = self.output_root / f".{safe_stem}.saving"
            map_destination = package_dir / "map.pcd"
            try:
                if staging_dir.exists():
                    _remove_path(staging_dir)
                staging_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, staging_dir / "map.pcd")

                session_dir = Path(self._session["sessionDir"])
                package_files = {
                    "statePath": ("state.txt", "state.txt"),
                    "lastResultPath": ("last_result.json", "last_result.json"),
                    "logPath": ("mapper.log", "mapper.log"),
                }
                package = {
                    "format": "robot_station_map_package",
                    "version": 1,
                    "path": str(package_dir),
                    "mapPath": str(map_destination),
                    "manifestPath": str(package_dir / "manifest.json"),
                }
                for field, (source_name, destination_name) in package_files.items():
                    file_source = session_dir / source_name
                    if file_source.exists() and file_source.is_file():
                        shutil.copy2(file_source, staging_dir / destination_name)
                        package[field] = str(package_dir / destination_name)

                keyframe_source = Path(self._session.get("keyframeDir", session_dir / "keyframes"))
                if keyframe_source.exists() and keyframe_source.is_dir():
                    shutil.copytree(keyframe_source, staging_dir / "keyframes")
                    package["keyframeDir"] = str(package_dir / "keyframes")

                now = time.strftime("%Y-%m-%d %H:%M:%S")
                package_manifest = self._session_payload_locked()
                package_manifest.update(
                    {
                        "status": "saved",
                        "detail": f"地图包已保存到 {package_dir}。",
                        "savedAt": now,
                        "updatedAt": now,
                        "savedMapPath": str(map_destination),
                        "savedPackagePath": str(package_dir),
                        "savedMapPackage": package,
                    }
                )
                (staging_dir / "manifest.json").write_text(
                    json.dumps(package_manifest, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

                if package_dir.exists():
                    _remove_path(package_dir)
                staging_dir.replace(package_dir)
            except Exception as exc:
                try:
                    if staging_dir.exists():
                        _remove_path(staging_dir)
                except Exception:
                    LOGGER.exception("Failed to clear incomplete mapping save package: %s", staging_dir)
                LOGGER.exception("Failed to save mapping package")
                return _result(
                    False,
                    "MAP-SAVE-FAILED",
                    f"Failed to save mapping package: {exc}",
                    session=self._session_payload_locked(),
                )

            self._session["status"] = "saved"
            self._session["detail"] = f"地图包已保存到 {package_dir}。"
            self._session["savedAt"] = package_manifest["savedAt"]
            self._session["savedMapPath"] = str(map_destination)
            self._session["savedPackagePath"] = str(package_dir)
            self._session["savedMapPackage"] = package
            self._session["updatedAt"] = package_manifest["updatedAt"]
            self._write_manifest_locked()
            return _result(
                True,
                "MAP-SAVED",
                "Mapping package saved.",
                session=self._session_payload_locked(),
                path=str(map_destination),
                packagePath=str(package_dir),
                package=package,
            )

    def delete_last(self, payload=None):
        payload = payload or {}
        if not isinstance(payload, dict):
            return _result(False, "MAP-PAYLOAD", "Payload must be a JSON object.")
        with self._lock:
            if self._session is None:
                return _result(False, "MAP-NOSESSION", "No mapping session is active.")
            if self._is_busy_locked():
                return _result(False, "MAP-BUSY", "Mapping capture is running.", session=self._session_payload_locked())

            keyframes = [dict(entry) for entry in self._session.get("keyframes", []) if isinstance(entry, dict)]
            if not keyframes:
                return _result(False, "MAP-NOKEYFRAME", "No mapping keyframe is available to delete.", session=self._session_payload_locked())

            history = [entry for entry in self._session.get("deleteHistory", []) if isinstance(entry, dict)]
            if not history:
                return _result(False, "MAP-HISTORY", "No previous mapping snapshot is available.", session=self._session_payload_locked())

            history_entry = history[-1]
            snapshot = self._read_history_snapshot_locked(history_entry)
            if not isinstance(snapshot, dict):
                return _result(False, "MAP-HISTORY", "Previous mapping snapshot could not be read.", session=self._session_payload_locked())

            deleted_keyframe = dict(snapshot.get("deletedKeyframe") or history_entry.get("keyframe") or keyframes[-1])
            self._restore_capture_rollback_locked(snapshot)
            history.pop()
            self._session["deleteHistory"] = history
            self._session["status"] = "ready"
            self._session["progress"] = None
            self._session["lastError"] = ""
            index = deleted_keyframe.get("index")
            index_text = f" #{index}" if index is not None else ""
            self._session["detail"] = f"已删除上一帧 keyframe{index_text}。"
            self._session["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self._write_manifest_locked()
            return _result(
                True,
                "MAP-DELETE-LAST",
                "Last mapping keyframe deleted.",
                session=self._session_payload_locked(),
                deletedKeyframe=deleted_keyframe,
            )

    def reset(self, payload=None):
        payload = payload or {}
        if not isinstance(payload, dict):
            return _result(False, "MAP-PAYLOAD", "Payload must be a JSON object.")
        clear_tmp = bool(payload.get("clearTmp", payload.get("removeFiles", True)))
        with self._lock:
            if self._resetting:
                return _result(False, "MAP-BUSY", "Mapping reset is already running.", session=self._session_payload_locked())
            self._resetting = True
            job_process = self._job_process
            job_thread = self._job_thread
            self._session = None
            self._job_thread = None
            self._job_process = None
        try:
            self._terminate_job_process(job_process)
            if job_thread is not None and job_thread is not threading.current_thread() and job_thread.is_alive():
                job_thread.join(timeout=5.0)
            temp_cleanup = {"removed": 0, "errors": []}
            if clear_tmp:
                temp_cleanup = self._clear_tmp_root()
            if temp_cleanup["errors"]:
                return _result(
                    False,
                    "MAP-TMP-CLEANUP",
                    "Mapping session was reset, but temporary files could not be fully cleared.",
                    session=None,
                    tempCleanup=temp_cleanup,
                )
            return _result(True, "MAP-RESET", "Mapping session reset.", session=None, tempCleanup=temp_cleanup)
        finally:
            with self._lock:
                self._resetting = False

    def _settings_from_payload(self, payload, base=None):
        base = base or {}
        return {
            "frameCount": _clamp_int(payload.get("frameCount", base.get("frameCount", 10)), 10, 1, 200),
            "cloudTopic": _clean_topic(payload.get("cloudTopic", base.get("cloudTopic", "/rslidar_points")), "/rslidar_points"),
            "odomTopic": _clean_topic(payload.get("odomTopic", base.get("odomTopic", "/odom")), "/odom"),
            "baseFrame": str(payload.get("baseFrame", base.get("baseFrame", "base_link")) or "base_link").strip(),
            "captureTimeoutSec": _clamp_float(payload.get("captureTimeoutSec", base.get("captureTimeoutSec", 20.0)), 20.0, 2.0, 120.0),
            "voxelLeafM": _clamp_float(payload.get("voxelLeafM", base.get("voxelLeafM", 0.02)), 0.02, 0.005, 0.20),
            "ndtResolutionM": _clamp_float(payload.get("ndtResolutionM", base.get("ndtResolutionM", 0.5)), 0.5, 0.05, 5.0),
            "gicpMaxCorrespondenceM": _clamp_float(
                payload.get("gicpMaxCorrespondenceM", base.get("gicpMaxCorrespondenceM", 0.20)),
                0.20,
                0.02,
                2.0,
            ),
        }

    def _run_capture_job(self, session, settings):
        session_dir = Path(session["sessionDir"])
        log_path = Path(session["logPath"])
        result_path = Path(session["lastResultPath"])
        with self._lock:
            if not self._session_matches_locked(session):
                return
        command = [
            *self.mapper_command,
            "--session-dir",
            str(session_dir),
            "--frames",
            str(settings["frameCount"]),
            "--cloud-topic",
            settings["cloudTopic"],
            "--odom-topic",
            settings["odomTopic"],
            "--base-frame",
            settings["baseFrame"],
            "--capture-timeout-sec",
            str(settings["captureTimeoutSec"]),
            "--progress-path",
            str(session["progressPath"]),
            "--voxel-leaf",
            str(settings["voxelLeafM"]),
            "--ndt-resolution",
            str(settings["ndtResolutionM"]),
            "--gicp-max-correspondence",
            str(settings["gicpMaxCorrespondenceM"]),
        ]
        started_at = time.strftime("%Y-%m-%d %H:%M:%S")
        process = None
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(f"\n[{started_at}] {' '.join(command)}\n")
                process = subprocess.Popen(
                    command,
                    cwd=str(ROOT_DIR),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    start_new_session=True,
                )
                with self._lock:
                    if not self._session_matches_locked(session):
                        should_cancel = True
                    else:
                        should_cancel = False
                        self._job_process = process
                if should_cancel:
                    self._terminate_job_process(process)
                    return
                return_code = process.wait()
        except FileNotFoundError as exc:
            self._finish_capture(session, False, "MAP-DEPENDENCY", f"Mapper command is not available: {exc}", None)
            return
        except Exception as exc:
            LOGGER.exception("Mapping capture failed")
            self._finish_capture(session, False, "MAP-CAPTURE-FAILED", str(exc), None)
            return
        finally:
            with self._lock:
                if self._job_process is process:
                    self._job_process = None

        result = self._read_json_file(result_path)
        if return_code != 0:
            detail = result.get("detail") if isinstance(result, dict) else ""
            self._finish_capture(session, False, "MAP-CAPTURE-FAILED", detail or f"Mapper exited with code {return_code}.", result)
            return
        if not isinstance(result, dict):
            self._finish_capture(session, False, "MAP-CAPTURE-FAILED", "Mapper did not write last_result.json.", None)
            return
        self._finish_capture(session, True, "MAP-CAPTURED", "Point cloud keyframe captured and registered.", result)

    def _finish_capture(self, session, ok, code, detail, result):
        with self._lock:
            if not self._session_matches_locked(session):
                return
            rollback = session.get("_rollback")
            if not ok:
                self._restore_capture_rollback_locked(rollback)
            self._session["status"] = "ready" if ok else "failed"
            self._session["progress"] = _progress_payload(
                "done" if ok else "failed",
                settings=self._session.get("settings", {}),
                detail=detail,
            )
            self._session["detail"] = detail
            if ok:
                self._session["lastResult"] = result
            self._session["lastError"] = "" if ok else detail
            self._session["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
            keyframe = None
            if ok and isinstance(result, dict):
                self._clear_saved_metadata_locked()
                self._session["captureCount"] = int(self._session.get("captureCount", 0) or 0) + 1
                keyframe = result.get("keyframe")
                if isinstance(keyframe, dict):
                    existing = [entry for entry in self._session.get("keyframes", []) if entry.get("index") != keyframe.get("index")]
                    existing.append(keyframe)
                    self._session["keyframes"] = sorted(existing, key=lambda item: int(item.get("index", 0) or 0))
                    self._push_delete_history_locked(rollback, keyframe)
                else:
                    self._clear_capture_rollback_locked(rollback)
            self._write_manifest_locked()

    def _capture_rollback_locked(self):
        if self._session is None:
            return None
        session_dir = Path(self._session["sessionDir"])
        backup_dir = session_dir / ".rollback"
        try:
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            LOGGER.warning("Failed to prepare mapping rollback directory: %s", exc)
            return None

        files = {}
        for name in ("map_tmp.pcd", "state.txt", "last_result.json"):
            source = session_dir / name
            backup = backup_dir / name
            if source.exists() and source.is_file():
                try:
                    shutil.copy2(source, backup)
                    files[name] = True
                except Exception as exc:
                    LOGGER.warning("Failed to back up mapping file %s: %s", source, exc)
                    files[name] = False
            else:
                files[name] = False

        keyframes = [dict(entry) for entry in self._session.get("keyframes", []) if isinstance(entry, dict)]
        return {
            "backupDir": str(backup_dir),
            "files": files,
            "keyframes": keyframes,
            "lastResult": self._session.get("lastResult"),
            "captureCount": int(self._session.get("captureCount", 0) or 0),
            "savedFields": {field: self._session.get(field) for field in MAPPING_SAVED_FIELDS if field in self._session},
        }

    def _push_delete_history_locked(self, rollback, keyframe):
        if self._session is None or not isinstance(rollback, dict) or not isinstance(keyframe, dict):
            self._clear_capture_rollback_locked(rollback)
            return None

        session_dir = Path(self._session["sessionDir"])
        source_dir = self._capture_rollback_dir(rollback, session_dir)
        history_dir = Path(self._session.get("historyDir", session_dir / ".history"))
        history = [entry for entry in self._session.get("deleteHistory", []) if isinstance(entry, dict)]
        history_id = self._delete_history_id(history_dir, history, keyframe)
        backup_dir = history_dir / history_id

        try:
            history_dir.mkdir(parents=True, exist_ok=True)
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            if source_dir and source_dir.exists():
                shutil.move(str(source_dir), str(backup_dir))
            else:
                backup_dir.mkdir(parents=True, exist_ok=True)

            snapshot = dict(rollback)
            snapshot["backupDir"] = str(backup_dir)
            snapshot["deletedKeyframe"] = dict(keyframe)
            (backup_dir / "snapshot.json").write_text(
                json.dumps(snapshot, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            entry = {
                "id": history_id,
                "keyframe": dict(keyframe),
                "backupDir": str(backup_dir),
            }
            history.append(entry)
            self._session["deleteHistory"] = history
            return entry
        except Exception as exc:
            LOGGER.warning("Failed to store mapping delete history: %s", exc)
            try:
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
            except Exception:
                LOGGER.warning("Failed to clear incomplete mapping history directory: %s", backup_dir)
            self._clear_capture_rollback_locked(rollback, session_dir=session_dir)
            return None

    def _delete_history_id(self, history_dir, history, keyframe):
        try:
            keyframe_index = int(keyframe.get("index"))
        except (TypeError, ValueError):
            keyframe_index = len(history)
        base = f"undo_{len(history):04d}_keyframe_{keyframe_index:03d}"
        candidate = base
        suffix = 1
        while (history_dir / candidate).exists():
            candidate = f"{base}_{suffix}"
            suffix += 1
        return candidate

    def _read_history_snapshot_locked(self, history_entry):
        if self._session is None or not isinstance(history_entry, dict):
            return None
        session_dir = Path(self._session["sessionDir"])
        backup_dir = self._capture_rollback_dir(history_entry, session_dir)
        if not backup_dir:
            return None
        snapshot_path = backup_dir / "snapshot.json"
        snapshot = self._read_json_file(snapshot_path)
        if not isinstance(snapshot, dict):
            return None
        snapshot["backupDir"] = str(backup_dir)
        return snapshot

    def _restore_capture_rollback_locked(self, rollback):
        if self._session is None or not isinstance(rollback, dict):
            return
        session_dir = Path(self._session["sessionDir"])
        backup_dir = self._capture_rollback_dir(rollback, session_dir)
        files = rollback.get("files") if isinstance(rollback.get("files"), dict) else {}

        for name in ("map_tmp.pcd", "state.txt", "last_result.json"):
            destination = session_dir / name
            backup = backup_dir / name if backup_dir else None
            try:
                if files.get(name) and backup and backup.exists():
                    shutil.copy2(backup, destination)
                elif destination.exists():
                    destination.unlink()
            except Exception as exc:
                LOGGER.warning("Failed to restore mapping file %s: %s", destination, exc)

        accepted_paths = {
            str(Path(entry.get("path", "")).resolve())
            for entry in rollback.get("keyframes", [])
            if isinstance(entry, dict) and entry.get("path")
        }
        keyframe_dir = Path(self._session.get("keyframeDir", session_dir / "keyframes"))
        if keyframe_dir.exists():
            for path in keyframe_dir.glob("keyframe_*.pcd"):
                try:
                    if str(path.resolve()) not in accepted_paths:
                        path.unlink()
                except Exception as exc:
                    LOGGER.warning("Failed to remove rolled-back keyframe %s: %s", path, exc)

        self._session["keyframes"] = [dict(entry) for entry in rollback.get("keyframes", []) if isinstance(entry, dict)]
        self._session["lastResult"] = rollback.get("lastResult")
        self._session["captureCount"] = int(rollback.get("captureCount", 0) or 0)
        self._restore_saved_metadata_locked(rollback)
        self._clear_capture_rollback_locked(rollback, session_dir=session_dir)

    def _clear_saved_metadata_locked(self):
        if self._session is None:
            return
        for field in MAPPING_SAVED_FIELDS:
            self._session.pop(field, None)

    def _restore_saved_metadata_locked(self, snapshot):
        if self._session is None:
            return
        saved_fields = snapshot.get("savedFields") if isinstance(snapshot, dict) else None
        for field in MAPPING_SAVED_FIELDS:
            if isinstance(saved_fields, dict) and field in saved_fields:
                self._session[field] = saved_fields[field]
            else:
                self._session.pop(field, None)

    def _capture_rollback_dir(self, rollback, session_dir):
        raw_path = rollback.get("backupDir") if isinstance(rollback, dict) else ""
        if not raw_path:
            return None
        backup_dir = Path(raw_path)
        try:
            backup_dir.resolve().relative_to(session_dir.resolve())
        except Exception:
            LOGGER.warning("Ignoring invalid mapping rollback directory: %s", backup_dir)
            return None
        return backup_dir

    def _clear_capture_rollback_locked(self, rollback, session_dir=None):
        if self._session is None or not isinstance(rollback, dict):
            return
        session_dir = Path(session_dir or self._session["sessionDir"])
        backup_dir = self._capture_rollback_dir(rollback, session_dir)
        if not backup_dir:
            return
        try:
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
        except Exception as exc:
            LOGGER.warning("Failed to clear mapping rollback directory %s: %s", backup_dir, exc)

    def _read_json_file(self, path):
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            return None

    def _refresh_progress_locked(self):
        if self._session is None or not self._is_busy_locked():
            return
        progress_path = self._session.get("progressPath")
        if not progress_path:
            return
        raw = self._read_json_file(progress_path)
        if not isinstance(raw, dict):
            return
        progress = _progress_payload(raw.get("phase"), settings=self._session.get("settings", {}), raw=raw)
        previous = dict(self._session.get("progress") or {})
        previous.pop("updatedAt", None)
        comparable = dict(progress)
        comparable.pop("updatedAt", None)
        if comparable == previous:
            return
        self._session["progress"] = progress
        self._session["detail"] = progress["detail"]
        self._session["updatedAt"] = progress["updatedAt"]
        self._write_manifest_locked()

    def _is_busy_locked(self):
        return self._resetting or (self._job_thread is not None and self._job_thread.is_alive())

    def _session_matches_locked(self, session):
        return self._session is not None and self._session.get("id") == session.get("id")

    def _clear_tmp_root(self):
        cleanup = {"removed": 0, "errors": []}
        self.tmp_root.mkdir(parents=True, exist_ok=True)
        for path in list(self.tmp_root.iterdir()):
            try:
                _remove_path(path)
                cleanup["removed"] += 1
            except FileNotFoundError:
                pass
            except Exception as exc:
                LOGGER.exception("Failed to remove temporary mapping path: %s", path)
                cleanup["errors"].append({"path": str(path), "error": str(exc)})
        return cleanup

    def _terminate_job_process(self, process):
        if process is None or process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except Exception:
            try:
                process.terminate()
            except Exception:
                LOGGER.exception("Failed to terminate mapping process")
                return
        try:
            process.wait(timeout=3.0)
            return
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except Exception:
            try:
                process.kill()
            except Exception:
                LOGGER.exception("Failed to kill mapping process")
                return
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            LOGGER.warning("Mapping process did not exit after kill")

    def _session_payload_locked(self):
        if self._session is None:
            return None
        payload = dict(self._session)
        busy = self._is_busy_locked()
        delete_history = [
            self._delete_history_entry_payload(entry)
            for entry in self._session.get("deleteHistory", [])
            if isinstance(entry, dict)
        ]
        payload["deleteHistory"] = delete_history
        payload["deleteDepth"] = len(delete_history)
        payload["canDeleteLast"] = bool(delete_history and payload.get("keyframes") and not busy)
        payload["busy"] = busy
        return payload

    def _delete_history_entry_payload(self, entry):
        keyframe = entry.get("keyframe") if isinstance(entry, dict) else None
        payload = {"id": str(entry.get("id") or "")} if isinstance(entry, dict) else {"id": ""}
        if isinstance(keyframe, dict):
            payload["keyframe"] = dict(keyframe)
        return payload

    def _write_manifest_locked(self):
        if self._session is None:
            return
        path = Path(self._session["manifestPath"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._session_payload_locked(), ensure_ascii=False, indent=2), encoding="utf-8")


_manager = None
_manager_lock = threading.Lock()


def get_mapping_manager():
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = MappingManager()
        return _manager
