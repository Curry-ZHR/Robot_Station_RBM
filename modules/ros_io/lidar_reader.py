import math
import struct
import threading
import time
from dataclasses import asdict, dataclass

from modules.ros_io.runtime import RosRuntimeError
from modules.ros_io.serializers import RosMessageImportError


POINT_FIELD_FORMATS = {
    1: "b",
    2: "B",
    3: "h",
    4: "H",
    5: "i",
    6: "I",
    7: "f",
    8: "d",
}


@dataclass(frozen=True)
class LidarPointCloudSpec:
    key: str
    label: str
    topic: str
    message_type: str = "sensor_msgs/msg/PointCloud2"
    qos_depth: int = 2
    stale_after_sec: float = 1.0
    default_max_points: int = 60000

    def to_dict(self):
        return asdict(self)


LIDAR_POINT_CLOUD_SPECS = {
    "rslidar_points": LidarPointCloudSpec(
        key="rslidar_points",
        label="RoboSense LiDAR",
        topic="/rslidar_points",
        stale_after_sec=1.0,
        default_max_points=60000,
    ),
}


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def _message_stamp_text(message):
    header = getattr(message, "header", None)
    stamp = getattr(header, "stamp", None)
    if stamp is None:
        return ""
    sec = int(getattr(stamp, "sec", 0) or 0)
    nanosec = int(getattr(stamp, "nanosec", 0) or 0)
    return f"{sec}.{nanosec:09d}"


def _field_plain(field):
    return {
        "name": str(getattr(field, "name", "")),
        "offset": int(getattr(field, "offset", 0) or 0),
        "datatype": int(getattr(field, "datatype", 0) or 0),
        "count": int(getattr(field, "count", 1) or 1),
    }


def _numeric_reader(field, is_bigendian):
    datatype = int(field.get("datatype", 0))
    fmt = POINT_FIELD_FORMATS.get(datatype)
    if fmt is None:
        raise ValueError(f"Unsupported PointCloud2 field datatype: {datatype}")
    endian = ">" if is_bigendian else "<"
    unpacker = struct.Struct(endian + fmt)
    return int(field.get("offset", 0)), unpacker


def _downsample_binary_frame(body, point_count, max_points):
    if point_count <= max_points:
        return body, point_count
    step = max(1, math.ceil(point_count / max_points))
    stride = 16
    sampled = bytearray(max_points * stride)
    written = 0
    for index in range(0, point_count, step):
        source_offset = index * stride
        sampled[written * stride:(written + 1) * stride] = body[source_offset:source_offset + stride]
        written += 1
        if written >= max_points:
            break
    return bytes(sampled[:written * stride]), written


def pointcloud2_to_binary_frame(message, max_points):
    fields = [_field_plain(field) for field in getattr(message, "fields", [])]
    field_map = {field["name"]: field for field in fields}
    missing = [name for name in ("x", "y", "z") if name not in field_map]
    if missing:
        raise ValueError(f"PointCloud2 missing required field(s): {', '.join(missing)}")

    is_bigendian = bool(getattr(message, "is_bigendian", False))
    point_step = int(getattr(message, "point_step", 0) or 0)
    row_step = int(getattr(message, "row_step", 0) or 0)
    width = int(getattr(message, "width", 0) or 0)
    height = int(getattr(message, "height", 0) or 0)
    if point_step <= 0 or width <= 0 or height <= 0:
        raise ValueError("PointCloud2 has invalid dimensions or point_step.")

    data = bytes(getattr(message, "data", b""))
    if row_step <= 0:
        row_step = point_step * width

    x_offset, x_unpacker = _numeric_reader(field_map["x"], is_bigendian)
    y_offset, y_unpacker = _numeric_reader(field_map["y"], is_bigendian)
    z_offset, z_unpacker = _numeric_reader(field_map["z"], is_bigendian)
    intensity_reader = None
    if "intensity" in field_map:
        intensity_reader = _numeric_reader(field_map["intensity"], is_bigendian)

    source_point_count = width * height
    target_points = max(1, min(int(max_points), source_point_count))
    sample_step = max(1, math.ceil(source_point_count / target_points))
    body = bytearray(target_points * 16)
    output_offset = 0
    point_count = 0

    for point_index in range(0, source_point_count, sample_step):
        row = point_index // width
        column = point_index % width
        base_offset = row * row_step + column * point_step
        if base_offset + point_step > len(data):
            continue

        x = float(x_unpacker.unpack_from(data, base_offset + x_offset)[0])
        y = float(y_unpacker.unpack_from(data, base_offset + y_offset)[0])
        z = float(z_unpacker.unpack_from(data, base_offset + z_offset)[0])
        if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(z)):
            continue

        intensity = 0.0
        if intensity_reader is not None:
            intensity_offset, intensity_unpacker = intensity_reader
            intensity = float(intensity_unpacker.unpack_from(data, base_offset + intensity_offset)[0])
            if not math.isfinite(intensity):
                intensity = 0.0

        struct.pack_into("<ffff", body, output_offset, x, y, z, intensity)
        output_offset += 16
        point_count += 1
        if point_count >= target_points:
            break

    return {
        "body": bytes(body[:output_offset]),
        "contentType": "application/octet-stream",
        "pointCount": point_count,
        "sourcePointCount": source_point_count,
        "strideFloats": 4,
        "fields": [field["name"] for field in fields],
        "frameId": str(getattr(getattr(message, "header", None), "frame_id", "") or ""),
        "stamp": _message_stamp_text(message),
        "width": width,
        "height": height,
        "pointStep": point_step,
        "rowStep": row_step,
        "isDense": bool(getattr(message, "is_dense", False)),
    }


class LidarPointCloudReader:
    def __init__(self, runtime, specs=None):
        self._runtime = runtime
        self._specs = specs or LIDAR_POINT_CLOUD_SPECS
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._latest = {}
        self._events = {}
        self._sequence = {}
        self._subscribed = set()

    def list_clouds(self):
        errors = []
        for spec in self._specs.values():
            result = self._ensure_subscription(spec)
            if not result["ok"]:
                errors.append(result)

        with self._lock:
            clouds = [self._cloud_status(spec) for spec in self._specs.values()]

        return _result(
            not errors,
            "LDR-R-OK" if not errors else "LDR-R-UNAVAILABLE",
            "LiDAR point cloud feeds are subscribed." if not errors else "One or more LiDAR feeds are unavailable.",
            clouds=clouds,
            errors=errors,
        )

    def read_frame(self, key, timeout_sec=0.0, after_sequence=None, max_points=None):
        spec = self._specs.get(key)
        if spec is None:
            return _result(False, "LDR-R-UNKNOWN", f"Unknown LiDAR point cloud feed: {key}.")

        subscribe_result = self._ensure_subscription(spec)
        if not subscribe_result["ok"]:
            return subscribe_result

        deadline = time.monotonic() + timeout_sec if timeout_sec and timeout_sec > 0 else None
        with self._lock:
            while True:
                latest = self._latest.get(spec.key)
                sequence = latest.get("sequence") if latest else None
                if latest is not None and (after_sequence is None or sequence != after_sequence):
                    break
                if deadline is None:
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(remaining)

            latest = self._latest.get(spec.key)

        if latest is None:
            return _result(False, "LDR-R-NODATA", f"No point cloud received from {spec.topic}.", cloud=spec.to_dict())
        if latest.get("parseError"):
            return _result(
                False,
                "LDR-R-PARSE",
                latest["parseError"],
                cloud=spec.to_dict(),
                sequence=latest.get("sequence"),
            )

        age_ms = int((time.monotonic() - latest["monotonic"]) * 1000)
        body = latest["body"]
        point_count = latest["pointCount"]
        requested_max = self._normalize_max_points(max_points, spec.default_max_points)
        if requested_max < point_count:
            body, point_count = _downsample_binary_frame(body, point_count, requested_max)

        return _result(
            True,
            "LDR-R-FRAME",
            f"Latest point cloud from {spec.topic} is {age_ms} ms old.",
            cloud=spec.to_dict(),
            body=body,
            contentType=latest["contentType"],
            ageMs=age_ms,
            stale=age_ms > int(spec.stale_after_sec * 1000),
            receivedAt=latest["receivedAt"],
            sequence=latest["sequence"],
            pointCount=point_count,
            sourcePointCount=latest["sourcePointCount"],
            strideFloats=latest["strideFloats"],
            fields=latest["fields"],
            frameId=latest["frameId"],
            stamp=latest["stamp"],
            width=latest["width"],
            height=latest["height"],
            pointStep=latest["pointStep"],
            rowStep=latest["rowStep"],
            isDense=latest["isDense"],
        )

    def _cloud_status(self, spec):
        latest = self._latest.get(spec.key)
        if latest is None:
            return {
                **spec.to_dict(),
                "hasFrame": False,
                "stale": True,
                "ageMs": None,
                "receivedAt": None,
                "pointCount": 0,
                "sourcePointCount": 0,
                "frameId": "",
                "fields": [],
            }

        age_ms = int((time.monotonic() - latest["monotonic"]) * 1000)
        return {
            **spec.to_dict(),
            "hasFrame": not bool(latest.get("parseError")),
            "stale": age_ms > int(spec.stale_after_sec * 1000),
            "ageMs": age_ms,
            "receivedAt": latest["receivedAt"],
            "sequence": latest["sequence"],
            "pointCount": latest.get("pointCount", 0),
            "sourcePointCount": latest.get("sourcePointCount", 0),
            "frameId": latest.get("frameId", ""),
            "fields": latest.get("fields", []),
            "parseError": latest.get("parseError", ""),
        }

    def _normalize_max_points(self, value, default_max_points):
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = int(default_max_points)
        return max(1000, min(int(default_max_points), parsed))

    def _ensure_subscription(self, spec):
        with self._lock:
            if spec.key not in self._events:
                self._events[spec.key] = threading.Event()
            if spec.key in self._subscribed:
                return _result(True, "LDR-R-SUBSCRIBED", "Subscription already registered.")

        def callback(message, topic_key=spec.key):
            with self._lock:
                sequence = self._sequence.get(topic_key, 0) + 1
                self._sequence[topic_key] = sequence
            try:
                rendered = pointcloud2_to_binary_frame(message, spec.default_max_points)
                rendered["parseError"] = ""
            except Exception as exc:
                rendered = {
                    "body": b"",
                    "contentType": "application/octet-stream",
                    "pointCount": 0,
                    "sourcePointCount": int(getattr(message, "width", 0) or 0) * int(getattr(message, "height", 0) or 0),
                    "strideFloats": 4,
                    "fields": [str(getattr(field, "name", "")) for field in getattr(message, "fields", [])],
                    "frameId": str(getattr(getattr(message, "header", None), "frame_id", "") or ""),
                    "stamp": _message_stamp_text(message),
                    "width": int(getattr(message, "width", 0) or 0),
                    "height": int(getattr(message, "height", 0) or 0),
                    "pointStep": int(getattr(message, "point_step", 0) or 0),
                    "rowStep": int(getattr(message, "row_step", 0) or 0),
                    "isDense": bool(getattr(message, "is_dense", False)),
                    "parseError": str(exc),
                }

            with self._lock:
                current_latest = self._latest.get(topic_key)
                if current_latest and int(current_latest.get("sequence", 0) or 0) > sequence:
                    return
                self._latest[topic_key] = {
                    **rendered,
                    "monotonic": time.monotonic(),
                    "receivedAt": time.strftime("%H:%M:%S"),
                    "sequence": sequence,
                }
                self._events[topic_key].set()
                self._condition.notify_all()

        try:
            self._runtime.create_subscription(
                spec.key,
                spec.message_type,
                spec.topic,
                callback,
                qos_depth=spec.qos_depth,
            )
        except (RosRuntimeError, RosMessageImportError) as exc:
            return _result(
                False,
                "LDR-R-UNAVAILABLE",
                str(exc),
                cloud=spec.to_dict(),
            )

        with self._lock:
            self._subscribed.add(spec.key)
        return _result(True, "LDR-R-SUBSCRIBED", "Subscription registered.")
