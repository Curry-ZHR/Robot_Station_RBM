import threading
import time
from dataclasses import asdict, dataclass

from modules.ros_io.runtime import RosRuntimeError
from modules.ros_io.serializers import RosMessageImportError


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8"


@dataclass(frozen=True)
class CameraImageSpec:
    camera: str
    kind: str
    label: str
    topic: str
    message_type: str = "sensor_msgs/msg/CompressedImage"
    qos_depth: int = 2
    stale_after_sec: float = 2.0

    @property
    def key(self):
        return f"{self.camera}_{self.kind}"

    def to_dict(self):
        return asdict(self)


CAMERA_LABELS = {
    "camera_h": "Wide-angle",
    "camera_f": "Front",
    "camera_l": "Left",
    "camera_r": "Right",
}
CAMERA_KINDS = {
    "camera_h": ("color",),
    "camera_f": ("color", "depth", "ir"),
    "camera_l": ("color", "depth", "ir"),
    "camera_r": ("color", "depth", "ir"),
}
KIND_LABELS = {
    "color": "RGB",
    "depth": "Depth",
    "ir": "IR",
}
KIND_TOPICS = {
    "color": "color/image_raw/compressed",
    "depth": "depth/image_raw/compressedDepth",
    "ir": "ir/image_raw/compressed",
}


CAMERA_IMAGE_SPECS = {
    f"{camera}_{kind}": CameraImageSpec(
        camera=camera,
        kind=kind,
        label=f"{CAMERA_LABELS[camera]} {KIND_LABELS[kind]}",
        topic=f"/{camera}/{KIND_TOPICS[kind]}",
    )
    for camera, kinds in CAMERA_KINDS.items()
    for kind in kinds
}


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def _content_type_for_format(format_name, payload=None):
    rendered = str(format_name or "").lower()
    if "png" in rendered:
        return "image/png"
    if "jpeg" in rendered or "jpg" in rendered:
        return "image/jpeg"
    if payload and payload.startswith(PNG_SIGNATURE):
        return "image/png"
    if payload and payload.startswith(JPEG_SIGNATURE):
        return "image/jpeg"
    return "application/octet-stream"


def _extract_png_payload(payload):
    start = payload.find(PNG_SIGNATURE)
    if start < 0:
        return None
    return payload[start:]


def _visualize_compressed_depth(payload):
    png_payload = _extract_png_payload(payload)
    if not png_payload:
        return None

    try:
        import cv2
        import numpy as np
    except ImportError:
        return png_payload

    encoded = np.frombuffer(png_payload, dtype=np.uint8)
    depth_image = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED)
    if depth_image is None:
        return png_payload

    if depth_image.ndim == 3:
        depth_image = cv2.cvtColor(depth_image, cv2.COLOR_BGR2GRAY)

    depth = depth_image.astype(np.float32)
    valid = np.isfinite(depth) & (depth > 0)
    normalized = np.zeros(depth.shape, dtype=np.uint8)
    if valid.any():
        low, high = np.percentile(depth[valid], [2, 98])
        if high <= low:
            low = float(depth[valid].min())
            high = float(depth[valid].max())
        if high > low:
            normalized = np.clip((depth - low) * 255.0 / (high - low), 0, 255).astype(np.uint8)
            normalized[~valid] = 0

    color_map = getattr(cv2, "COLORMAP_TURBO", cv2.COLORMAP_JET)
    visual = cv2.applyColorMap(normalized, color_map)
    visual[~valid] = (0, 0, 0)
    success, encoded_visual = cv2.imencode(".png", visual)
    if not success:
        return png_payload
    return encoded_visual.tobytes()


class CameraImageReader:
    def __init__(self, runtime, specs=None):
        self._runtime = runtime
        self._specs = specs or CAMERA_IMAGE_SPECS
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._latest = {}
        self._events = {}
        self._sequence = {}
        self._subscribed = set()

    def _list_specs(self, kind=None):
        normalized_kind = str(kind or "").strip().lower()
        specs = list(self._specs.values())
        if not normalized_kind:
            return specs
        return [spec for spec in specs if spec.kind == normalized_kind]

    def list_images(self, kind=None):
        specs = self._list_specs(kind)
        if kind and not specs:
            return _result(False, "CAM-R-UNKNOWN", f"Unknown camera image kind: {kind}.", feeds=[], errors=[])

        errors = []
        for spec in specs:
            result = self._ensure_subscription(spec)
            if not result["ok"]:
                errors.append(result)

        with self._lock:
            feeds = [self._feed_status(spec) for spec in specs]

        return _result(
            not errors,
            "CAM-R-OK" if not errors else "CAM-R-UNAVAILABLE",
            "Camera image feeds are subscribed." if not errors else "One or more camera image feeds are unavailable.",
            feeds=feeds,
            errors=errors,
        )

    def read_frame(self, camera, kind, timeout_sec=0.0, after_sequence=None):
        spec = self._specs.get(f"{camera}_{kind}")
        if spec is None:
            return _result(False, "CAM-R-UNKNOWN", f"Unknown camera image feed: {camera}/{kind}.")

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
            return _result(False, "CAM-R-NODATA", f"No image received from {spec.topic}.", feed=spec.to_dict())

        body, content_type, render_mode = self._render_frame(spec, latest)
        age_ms = int((time.monotonic() - latest["monotonic"]) * 1000)
        return _result(
            True,
            "CAM-R-FRAME",
            f"Latest image from {spec.topic} is {age_ms} ms old.",
            feed=spec.to_dict(),
            body=body,
            contentType=content_type,
            renderMode=render_mode,
            ageMs=age_ms,
            stale=age_ms > int(spec.stale_after_sec * 1000),
            receivedAt=latest["received_at"],
            format=latest["format"],
            sequence=latest["sequence"],
        )

    def _feed_status(self, spec):
        latest = self._latest.get(spec.key)
        if latest is None:
            return {
                **spec.to_dict(),
                "hasFrame": False,
                "stale": True,
                "ageMs": None,
                "receivedAt": None,
                "format": "",
            }

        age_ms = int((time.monotonic() - latest["monotonic"]) * 1000)
        return {
            **spec.to_dict(),
            "hasFrame": True,
            "stale": age_ms > int(spec.stale_after_sec * 1000),
            "ageMs": age_ms,
            "receivedAt": latest["received_at"],
            "format": latest["format"],
            "sequence": latest["sequence"],
        }

    def _render_frame(self, spec, latest):
        if spec.kind == "depth":
            visualized = _visualize_compressed_depth(latest["data"])
            if visualized is not None:
                return visualized, "image/png", "depth_visualized"
        return latest["data"], _content_type_for_format(latest["format"], latest["data"]), "compressed"

    def _ensure_subscription(self, spec):
        with self._lock:
            if spec.key not in self._events:
                self._events[spec.key] = threading.Event()
            if spec.key in self._subscribed:
                return _result(True, "CAM-R-SUBSCRIBED", "Subscription already registered.")

        def callback(message, topic_key=spec.key):
            with self._lock:
                sequence = self._sequence.get(topic_key, 0) + 1
                self._sequence[topic_key] = sequence
                self._latest[topic_key] = {
                    "monotonic": time.monotonic(),
                    "received_at": time.strftime("%H:%M:%S"),
                    "format": str(getattr(message, "format", "")),
                    "data": bytes(getattr(message, "data", b"")),
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
                "CAM-R-UNAVAILABLE",
                str(exc),
                feed=spec.to_dict(),
            )

        with self._lock:
            self._subscribed.add(spec.key)
        return _result(True, "CAM-R-SUBSCRIBED", "Subscription registered.")
