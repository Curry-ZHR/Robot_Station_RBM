import threading
import time

from modules.ros_io.registry import read_topic_specs
from modules.ros_io.runtime import RosRuntimeError
from modules.ros_io.serializers import RosMessageImportError, message_to_plain


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


class RosTopicReader:
    def __init__(self, runtime, specs=None):
        self._runtime = runtime
        self._specs = specs or read_topic_specs()
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._latest = {}
        self._sequence = {}
        self._subscribed = set()

    def list_topics(self):
        return {
            "ok": True,
            "topics": [spec.to_dict() for spec in self._specs.values()],
        }

    def read(self, key, timeout_sec=0.0):
        spec = self._specs.get(key)
        if spec is None:
            return _result(False, "ROS-R-UNKNOWN", f"Unknown ROS read topic: {key}", key=key)

        subscribe_result = self._ensure_subscription(spec)
        if not subscribe_result["ok"]:
            return subscribe_result

        deadline = time.monotonic() + timeout_sec if timeout_sec and timeout_sec > 0 else None
        with self._lock:
            baseline = self._latest.get(spec.key)
            baseline_sequence = baseline.get("sequence") if baseline else None
            while True:
                latest = self._latest.get(spec.key)
                sequence = latest.get("sequence") if latest else None
                if latest is not None and sequence != baseline_sequence:
                    break
                if deadline is None:
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._condition.wait(remaining)
            latest = self._latest.get(spec.key)
        if latest is None:
            return _result(
                False,
                "ROS-R-NODATA",
                f"No message received from {spec.topic}.",
                key=spec.key,
                name=spec.name,
                topic=spec.topic,
                messageType=spec.message_type,
            )

        age_ms = int((time.monotonic() - latest["monotonic"]) * 1000)
        stale = age_ms > int(spec.stale_after_sec * 1000)
        return _result(
            True,
            "ROS-R-STALE" if stale else "ROS-R-OK",
            f"Latest message from {spec.topic} is {age_ms} ms old.",
            key=spec.key,
            name=spec.name,
            topic=spec.topic,
            messageType=spec.message_type,
            receivedAt=latest["received_at"],
            ageMs=age_ms,
            stale=stale,
            data=latest["data"],
        )

    def read_many(self, keys=None, timeout_sec=0.0):
        selected = keys or list(self._specs)
        return {
            "ok": True,
            "results": [self.read(key, timeout_sec=timeout_sec) for key in selected],
        }

    def _ensure_subscription(self, spec):
        with self._lock:
            if spec.key in self._subscribed:
                return _result(True, "ROS-R-SUBSCRIBED", "Subscription already registered.")

        def callback(message, topic_key=spec.key):
            rendered = message_to_plain(message)
            with self._lock:
                sequence = self._sequence.get(topic_key, 0) + 1
                self._sequence[topic_key] = sequence
                self._latest[topic_key] = {
                    "monotonic": time.monotonic(),
                    "received_at": time.strftime("%H:%M:%S"),
                    "data": rendered,
                    "sequence": sequence,
                }
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
                "ROS-R-UNAVAILABLE",
                str(exc),
                key=spec.key,
                name=spec.name,
                topic=spec.topic,
                messageType=spec.message_type,
            )

        with self._lock:
            self._subscribed.add(spec.key)
        return _result(True, "ROS-R-SUBSCRIBED", "Subscription registered.")

