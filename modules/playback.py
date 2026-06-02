"""State/action playback dataset readers.

This module intentionally ignores images and never publishes robot commands.
It only converts local data files into the JSON frame shape consumed by the
frontend playback view.
"""

from __future__ import annotations

import bisect
import math
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = ROOT_DIR.parent

SUPPORTED_SUFFIXES = {".hdf5", ".h5", ".parquet", ".mcap"}
STATE_DIM = 14
ACTION_DIM = 18
ARM_DIM = 7
DEFAULT_FPS = 30.0

HDF5_STATE_LEFT = "arm/jointStatePosition/puppetLeft"
HDF5_STATE_RIGHT = "arm/jointStatePosition/puppetRight"
HDF5_ACTION_LEFT = "arm/jointStatePosition/masterLeft"
HDF5_ACTION_RIGHT = "arm/jointStatePosition/masterRight"
HDF5_LIFT = "lift/motor/column"
HDF5_CHASSIS_ACTION = "robotBase/action/chassis"
HDF5_TIMESTAMP = "timestamp"

MCAP_STATE_LEFT = "/puppet/joint_left"
MCAP_STATE_RIGHT = "/puppet/joint_right"
MCAP_ACTION_LEFT = "/master/joint_left"
MCAP_ACTION_RIGHT = "/master/joint_right"
MCAP_JOINT_TOPICS = {
    MCAP_STATE_LEFT,
    MCAP_STATE_RIGHT,
    MCAP_ACTION_LEFT,
    MCAP_ACTION_RIGHT,
}

PARQUET_STATE_COLUMNS = ("observation.state", "state")
PARQUET_ACTION_COLUMNS = ("action", "target", "command")
PARQUET_TIME_COLUMNS = ("timestamp", "seconds", "time", "elapsedSec")
PARQUET_FRAME_COLUMNS = ("frame_index", "frameIndex", "index")


class PlaybackLoadError(Exception):
    def __init__(self, code: str, detail: str, status: int = 500):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status = status


def playback_result_status(result: dict[str, Any]) -> int:
    if result.get("ok"):
        return 200
    code = result.get("code", "")
    if code == "PLAYBACK-NOTFOUND":
        return 404
    if code in {"PLAYBACK-PATH", "PLAYBACK-UNSUPPORTED", "PLAYBACK-NODATA"}:
        return 400
    if code == "PLAYBACK-DEPENDENCY":
        return 503
    return 500


def load_playback_dataset(payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload or {}
    try:
        path = resolve_playback_path(payload.get("path"))
        suffix = path.suffix.lower()
        if suffix in {".hdf5", ".h5"}:
            dataset = read_hdf5_playback(path)
        elif suffix == ".parquet":
            dataset = read_parquet_playback(path)
        elif suffix == ".mcap":
            dataset = read_mcap_playback(path)
        else:
            raise PlaybackLoadError(
                "PLAYBACK-UNSUPPORTED",
                f"Unsupported playback data suffix: {suffix or '<none>'}",
                status=400,
            )
        return {"ok": True, "dataset": dataset}
    except PlaybackLoadError as exc:
        return {"ok": False, "code": exc.code, "detail": exc.detail}
    except Exception as exc:  # Keep the HTTP server alive on malformed files.
        return {"ok": False, "code": "PLAYBACK-READ", "detail": str(exc)}


def resolve_playback_path(raw_path: Any) -> Path:
    path_text = str(raw_path or "").strip()
    if not path_text:
        raise PlaybackLoadError("PLAYBACK-PATH", "Missing playback file path.", status=400)
    candidate = Path(path_text).expanduser()
    if not candidate.is_absolute():
        candidate = (WORKSPACE_DIR / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.exists():
        raise PlaybackLoadError("PLAYBACK-NOTFOUND", f"Playback file does not exist: {candidate}", status=404)
    if candidate.is_dir():
        mcap_files = sorted(candidate.glob("*.mcap"))
        if len(mcap_files) == 1:
            candidate = mcap_files[0].resolve()
        else:
            raise PlaybackLoadError("PLAYBACK-PATH", f"Playback path is a directory, not a data file: {candidate}", status=400)
    if candidate.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise PlaybackLoadError(
            "PLAYBACK-UNSUPPORTED",
            f"Unsupported playback data suffix: {candidate.suffix or '<none>'}",
            status=400,
        )
    return candidate


def read_hdf5_playback(path: Path) -> dict[str, Any]:
    try:
        import h5py
    except ImportError as exc:
        raise PlaybackLoadError("PLAYBACK-DEPENDENCY", "Reading HDF5 playback files requires h5py.", status=503) from exc

    with h5py.File(path, "r") as handle:
        state_left = hdf5_array(handle, HDF5_STATE_LEFT)
        state_right = hdf5_array(handle, HDF5_STATE_RIGHT)
        action_left = hdf5_array(handle, HDF5_ACTION_LEFT)
        action_right = hdf5_array(handle, HDF5_ACTION_RIGHT)
        lift = hdf5_array(handle, HDF5_LIFT)
        chassis = hdf5_array(handle, HDF5_CHASSIS_ACTION)
        timestamps = hdf5_array(handle, HDF5_TIMESTAMP)
        source_rows = hdf5_size(handle)

    lengths = [
        array_length(state_left),
        array_length(state_right),
        array_length(action_left),
        array_length(action_right),
        array_length(timestamps),
    ]
    row_count = min([length for length in lengths if length > 0], default=0)
    if row_count <= 0:
        raise PlaybackLoadError("PLAYBACK-NODATA", "HDF5 file has no readable state/action rows.", status=400)

    timestamp_values = vector_series(timestamps, row_count, width=1)
    base_timestamp = first_finite([row[0] for row in timestamp_values])
    fps = fps_from_timestamps([row[0] for row in timestamp_values]) or DEFAULT_FPS

    frames = []
    for index in range(row_count):
        state = vector_at(state_left, index, ARM_DIM) + vector_at(state_right, index, ARM_DIM)
        action = (
            vector_at(action_left, index, ARM_DIM)
            + vector_at(action_right, index, ARM_DIM)
            + [lift_height_m_at(lift, index)]
            + vector_at(chassis, index, 3, fill=0.0)
        )
        timestamp = timestamp_values[index][0]
        seconds = seconds_from_timestamp(timestamp, base_timestamp, index, fps)
        frames.append(
            {
                "seconds": seconds,
                "timestamp": timestamp,
                "frameIndex": index,
                "state": state,
                "action": action,
            }
        )

    return playback_dataset(path, "hdf5", frames, fps=fps, rows=source_rows or row_count)


def read_parquet_playback(path: Path) -> dict[str, Any]:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise PlaybackLoadError(
            "PLAYBACK-DEPENDENCY",
            "Reading Parquet playback files requires pyarrow. Install backend/requirements.txt before loading .parquet.",
            status=503,
        ) from exc

    parquet_file = pq.ParquetFile(path)
    column_names = set(parquet_file.schema.names)
    state_column = first_existing(column_names, PARQUET_STATE_COLUMNS)
    action_column = first_existing(column_names, PARQUET_ACTION_COLUMNS)
    timestamp_column = first_existing(column_names, PARQUET_TIME_COLUMNS)
    frame_column = first_existing(column_names, PARQUET_FRAME_COLUMNS)
    if not state_column and not action_column:
        raise PlaybackLoadError("PLAYBACK-NODATA", "Parquet file has no state/action columns.", status=400)

    columns = [column for column in [state_column, action_column, timestamp_column, frame_column] if column]
    table = parquet_file.read(columns=columns)
    rows = table.to_pylist()
    if not rows:
        raise PlaybackLoadError("PLAYBACK-NODATA", "Parquet file has no rows.", status=400)

    timestamps = [number_or_none(row.get(timestamp_column)) if timestamp_column else None for row in rows]
    base_timestamp = first_finite(timestamps)
    fps = fps_from_timestamps(timestamps) or DEFAULT_FPS
    frames = []
    for index, row in enumerate(rows):
        state = normalize_state_vector(row.get(state_column)) if state_column else None
        action = normalize_action_vector(row.get(action_column)) if action_column else None
        if state is None and action is None:
            continue
        timestamp = timestamps[index]
        frames.append(
            {
                "seconds": seconds_from_timestamp(timestamp, base_timestamp, index, fps),
                "timestamp": timestamp,
                "frameIndex": int(row.get(frame_column)) if frame_column and row.get(frame_column) is not None else index,
                "state": state,
                "action": action,
            }
        )

    if not frames:
        raise PlaybackLoadError("PLAYBACK-NODATA", "Parquet file has no readable state/action rows.", status=400)
    return playback_dataset(path, "parquet", frames, fps=fps, rows=len(rows))


def read_mcap_playback(path: Path) -> dict[str, Any]:
    try:
        import rosbag2_py
        from rclpy.serialization import deserialize_message
        from sensor_msgs.msg import JointState
    except ImportError as exc:
        raise PlaybackLoadError(
            "PLAYBACK-DEPENDENCY",
            "Reading MCAP playback files requires the ROS 2 Python environment. Start Robot Station with run.sh.",
            status=503,
        ) from exc

    samples = {topic: [] for topic in MCAP_JOINT_TOPICS}
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=str(mcap_rosbag_uri(path)), storage_id="mcap"),
        rosbag2_py.ConverterOptions(input_serialization_format="cdr", output_serialization_format="cdr"),
    )
    reader.set_filter(rosbag2_py.StorageFilter(topics=sorted(MCAP_JOINT_TOPICS)))
    while reader.has_next():
        topic, data, timestamp_ns = reader.read_next()
        if topic not in samples:
            continue
        message = deserialize_message(data, JointState)
        samples[topic].append((float(timestamp_ns) / 1_000_000_000.0, vector_from_values(message.position, ARM_DIM)))

    state_left = samples[MCAP_STATE_LEFT]
    state_right = samples[MCAP_STATE_RIGHT]
    action_left = samples[MCAP_ACTION_LEFT]
    action_right = samples[MCAP_ACTION_RIGHT]
    if not state_left or not state_right or not action_left or not action_right:
        raise PlaybackLoadError("PLAYBACK-NODATA", "MCAP file is missing one or more joint state/action topics.", status=400)

    frame_times = [timestamp for timestamp, _values in state_left]
    base_timestamp = frame_times[0]
    fps = fps_from_timestamps(frame_times) or DEFAULT_FPS
    right_times, right_values = split_samples(state_right)
    action_left_times, action_left_values = split_samples(action_left)
    action_right_times, action_right_values = split_samples(action_right)

    frames = []
    for index, (timestamp, left_state) in enumerate(state_left):
        right_state = latest_value_at(right_times, right_values, timestamp)
        left_action = latest_value_at(action_left_times, action_left_values, timestamp)
        right_action = latest_value_at(action_right_times, action_right_values, timestamp)
        if right_state is None or left_action is None or right_action is None:
            continue
        frames.append(
            {
                "seconds": max(0.0, timestamp - base_timestamp),
                "timestamp": timestamp,
                "frameIndex": index,
                "state": left_state + right_state,
                "action": left_action + right_action + [0.0, 0.0, 0.0, 0.0],
            }
        )

    if not frames:
        raise PlaybackLoadError("PLAYBACK-NODATA", "MCAP file has no aligned state/action frames.", status=400)
    return playback_dataset(path, "mcap", frames, fps=fps, rows=len(frames))


def playback_dataset(path: Path, source_type: str, frames: list[dict[str, Any]], fps: float, rows: int) -> dict[str, Any]:
    duration_sec = frames[-1]["seconds"] if len(frames) > 1 else len(frames) / max(1.0, fps)
    return {
        "name": path.name,
        "path": str(path),
        "sourceType": source_type,
        "fps": fps,
        "rows": rows,
        "durationSec": max(0.001, duration_sec),
        "stateDim": STATE_DIM,
        "actionDim": ACTION_DIM,
        "frames": frames,
    }


def hdf5_array(handle: Any, key: str) -> Any:
    if key not in handle:
        return None
    return handle[key][()]


def hdf5_size(handle: Any) -> int | None:
    if "size" not in handle:
        return None
    return int(handle["size"][()])


def array_length(values: Any) -> int:
    if values is None:
        return 0
    shape = getattr(values, "shape", None)
    if shape:
        return int(shape[0]) if len(shape) else 1
    try:
        return len(values)
    except TypeError:
        return 1


def vector_series(values: Any, length: int, width: int) -> list[list[float | None]]:
    return [vector_at(values, index, width, fill=None) for index in range(length)]


def vector_at(values: Any, index: int, width: int, fill: float | None = 0.0) -> list[float | None]:
    if values is None or index >= array_length(values):
        return [fill for _ in range(width)]
    row = values[index] if array_length(values) > 1 else values
    return vector_from_values(row, width, fill=fill)


def vector_from_values(values: Any, width: int, fill: float | None = 0.0) -> list[float | None]:
    if values is None:
        return [fill for _ in range(width)]
    if hasattr(values, "tolist"):
        values = values.tolist()
    if not isinstance(values, (list, tuple)):
        values = [values]
    output = [number_or_none(value) for value in values[:width]]
    while len(output) < width:
        output.append(fill)
    return output


def scalar_at(values: Any, index: int, default: float = 0.0) -> float:
    row = vector_at(values, index, 1, fill=default)
    value = row[0]
    return default if value is None else float(value)


def lift_height_m_at(values: Any, index: int) -> float:
    # HDF5 lift/motor/column uses the same millimeter scale as the lifting service.
    return scalar_at(values, index, default=0.0) / 1000.0


def normalize_state_vector(values: Any) -> list[float] | None:
    vector = vector_from_values(values, STATE_DIM, fill=None)
    if len(vector) < STATE_DIM or any(value is None for value in vector[:STATE_DIM]):
        return None
    return [float(value) for value in vector[:STATE_DIM]]


def normalize_action_vector(values: Any) -> list[float] | None:
    vector = vector_from_values(values, ACTION_DIM, fill=0.0)
    if len(vector) < STATE_DIM or any(value is None for value in vector[:STATE_DIM]):
        return None
    return [float(value or 0.0) for value in vector[:ACTION_DIM]]


def number_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def first_finite(values: list[float | None]) -> float | None:
    for value in values:
        if value is not None and math.isfinite(float(value)):
            return float(value)
    return None


def fps_from_timestamps(timestamps: list[float | None]) -> float | None:
    clean = [float(value) for value in timestamps if value is not None and math.isfinite(float(value))]
    if len(clean) < 2:
        return None
    deltas = [b - a for a, b in zip(clean, clean[1:]) if b > a]
    if not deltas:
        return None
    deltas.sort()
    median = deltas[len(deltas) // 2]
    if median <= 0:
        return None
    return max(0.001, min(1000.0, 1.0 / median))


def seconds_from_timestamp(timestamp: float | None, base_timestamp: float | None, index: int, fps: float) -> float:
    if timestamp is not None:
        if base_timestamp is not None and timestamp > 100000:
            return max(0.0, float(timestamp) - float(base_timestamp))
        return max(0.0, float(timestamp))
    return float(index) / max(1.0, fps)


def first_existing(names: set[str], candidates: tuple[str, ...]) -> str | None:
    return next((candidate for candidate in candidates if candidate in names), None)


def mcap_rosbag_uri(path: Path) -> Path:
    if path.is_dir():
        return path
    if (path.parent / "metadata.yaml").exists():
        return path.parent
    return path


def split_samples(samples: list[tuple[float, list[float | None]]]) -> tuple[list[float], list[list[float | None]]]:
    return [sample[0] for sample in samples], [sample[1] for sample in samples]


def latest_value_at(times: list[float], values: list[list[float | None]], timestamp: float) -> list[float | None] | None:
    index = bisect.bisect_right(times, timestamp) - 1
    if index < 0:
        return None
    return values[index]
