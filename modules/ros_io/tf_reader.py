import threading

from modules.ros_io.runtime import RosRuntimeError


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def _stamp_text(stamp):
    if stamp is None:
        return ""
    sec = int(getattr(stamp, "sec", 0) or 0)
    nanosec = int(getattr(stamp, "nanosec", 0) or 0)
    return f"{sec}.{nanosec:09d}"


def _transform_to_plain(transform_stamped):
    transform = transform_stamped.transform
    translation = transform.translation
    rotation = transform.rotation
    return {
        "targetFrame": str(getattr(transform_stamped.header, "frame_id", "") or ""),
        "sourceFrame": str(getattr(transform_stamped, "child_frame_id", "") or ""),
        "translation": {
            "x": float(getattr(translation, "x", 0.0) or 0.0),
            "y": float(getattr(translation, "y", 0.0) or 0.0),
            "z": float(getattr(translation, "z", 0.0) or 0.0),
        },
        "rotation": {
            "x": float(getattr(rotation, "x", 0.0) or 0.0),
            "y": float(getattr(rotation, "y", 0.0) or 0.0),
            "z": float(getattr(rotation, "z", 0.0) or 0.0),
            "w": float(getattr(rotation, "w", 1.0) or 1.0),
        },
        "stamp": _stamp_text(getattr(getattr(transform_stamped, "header", None), "stamp", None)),
    }


class TfTransformReader:
    def __init__(self, runtime):
        self._runtime = runtime
        self._lock = threading.RLock()
        self._buffer = None
        self._listener = None
        self._time_class = None
        self._duration_class = None

    def lookup_transform(self, target_frame, source_frame, timeout_sec=0.5):
        target = str(target_frame or "").strip()
        source = str(source_frame or "").strip()
        if not target or not source:
            return _result(
                False,
                "TF-R-FRAME",
                "Both target_frame and source_frame are required.",
                targetFrame=target,
                sourceFrame=source,
            )

        ready = self._ensure_listener()
        if not ready.get("ok"):
            return {
                **ready,
                "targetFrame": target,
                "sourceFrame": source,
            }

        try:
            transform = self._buffer.lookup_transform(
                target,
                source,
                self._time_class(),
                timeout=self._duration_class(seconds=max(0.0, float(timeout_sec or 0.0))),
            )
        except Exception as exc:
            return _result(
                False,
                "TF-R-LOOKUP",
                str(exc),
                targetFrame=target,
                sourceFrame=source,
            )

        return _result(
            True,
            "TF-R-OK",
            f"Transform {source} -> {target} is available.",
            transform=_transform_to_plain(transform),
            targetFrame=target,
            sourceFrame=source,
        )

    def _ensure_listener(self):
        with self._lock:
            if self._listener is not None:
                return _result(True, "TF-R-READY", "TF listener is ready.")
            try:
                from rclpy.duration import Duration
                from rclpy.time import Time
                import tf2_ros

                node = self._runtime.get_node()
                self._buffer = tf2_ros.Buffer()
                self._listener = tf2_ros.TransformListener(self._buffer, node)
                self._time_class = Time
                self._duration_class = Duration
            except (ImportError, RosRuntimeError) as exc:
                return _result(False, "TF-R-UNAVAILABLE", str(exc))
            except Exception as exc:
                return _result(False, "TF-R-UNAVAILABLE", str(exc))
        return _result(True, "TF-R-READY", "TF listener is ready.")
