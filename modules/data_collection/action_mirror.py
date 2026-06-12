import json
import math
import os
import threading
import time

from modules.logger import get_logger
from modules.ros_io.serializers import RosMessageImportError, import_message_class


LOGGER = get_logger()

LIFTING_TOPIC = os.environ.get("ACTION_MIRROR_LIFTING_TOPIC", "/action/lifting")
MESSAGE_TYPE = "std_msgs/msg/String"


def _env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return float(default)


DEFAULT_RATE_HZ = _env_float("ACTION_MIRROR_RATE_HZ", 60.0)
DEFAULT_LIFTING_HEIGHT_M = _env_float("ACTION_MIRROR_DEFAULT_LIFTING_HEIGHT_M", 0.0)


class ActionMirrorValidationError(ValueError):
    pass


def _number(value, field, default=None):
    if value is None and default is not None:
        value = default
    if isinstance(value, bool):
        raise ActionMirrorValidationError(f"{field} must be a number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ActionMirrorValidationError(f"{field} must be a number.") from exc
    if not math.isfinite(parsed):
        raise ActionMirrorValidationError(f"{field} must be a finite number.")
    return parsed


class ActionMirror:
    """Publish non-chassis web actions as dataset labels without controlling hardware."""

    def __init__(
        self,
        runtime=None,
        rate_hz=DEFAULT_RATE_HZ,
        lifting_height_m=DEFAULT_LIFTING_HEIGHT_M,
        lifting_topic=LIFTING_TOPIC,
        message_class=None,
        clock=time.monotonic,
    ):
        self._runtime = runtime
        self._rate_hz = max(1.0, float(rate_hz))
        self._lifting_topic = lifting_topic
        self._message_class = message_class
        self._clock = clock

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread = None
        self._lifting_publisher = None
        self._last_error_log_at = 0.0

        self._lifting_height_m = _number(lifting_height_m, "lifting_height_m", default=0.0)

    @property
    def lifting_topic(self):
        return self._lifting_topic

    def start(self):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, name="action-mirror", daemon=True)
            self._thread.start()

    def stop(self, timeout=1.0):
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

    def set_lifting_action(self, height_m):
        height = _number(height_m, "height")
        with self._lock:
            self._lifting_height_m = height
        return height

    def snapshot(self):
        with self._lock:
            lifting_height = self._lifting_height_m
        return {
            "lifting": {"height": lifting_height},
        }

    def publish_once(self):
        snapshot = self.snapshot()
        self._ensure_publishers()
        self._publish_json(self._lifting_publisher, snapshot["lifting"])

    def _run(self):
        interval = 1.0 / self._rate_hz
        next_publish_at = self._clock()
        while not self._stop_event.is_set():
            try:
                self.publish_once()
            except Exception as exc:
                self._log_publish_error(exc)
            next_publish_at += interval
            delay = max(0.0, next_publish_at - self._clock())
            if delay == 0.0:
                next_publish_at = self._clock()
            self._stop_event.wait(delay)

    def _ensure_runtime(self):
        if self._runtime is None:
            from modules.ros_io import get_ros_runtime

            self._runtime = get_ros_runtime()
        return self._runtime

    def _ensure_publishers(self):
        if self._message_class is None:
            self._message_class = import_message_class(MESSAGE_TYPE)
        runtime = self._ensure_runtime()
        if self._lifting_publisher is None:
            self._lifting_publisher = runtime.get_publisher(
                "action_mirror_lifting",
                MESSAGE_TYPE,
                self._lifting_topic,
                qos_depth=1,
            )

    def _publish_json(self, publisher, payload):
        message = self._message_class()
        message.data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        publisher.publish(message)

    def _log_publish_error(self, exc):
        now = self._clock()
        if now - self._last_error_log_at < 5.0:
            return
        self._last_error_log_at = now
        if isinstance(exc, RosMessageImportError):
            LOGGER.warning("Action mirror cannot import ROS message type: %s", exc)
        else:
            LOGGER.warning("Action mirror publish failed: %s", exc)


_mirror = None
_mirror_lock = threading.Lock()


def get_action_mirror():
    global _mirror
    with _mirror_lock:
        if _mirror is None:
            _mirror = ActionMirror()
        return _mirror


def start_action_mirror():
    mirror = get_action_mirror()
    mirror.start()
    return mirror


def shutdown_action_mirror():
    with _mirror_lock:
        mirror = _mirror
    if mirror is not None:
        mirror.stop()
