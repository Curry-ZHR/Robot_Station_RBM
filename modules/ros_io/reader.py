import threading
import time

from modules.ros_io.registry import TopicReadSpec, read_topic_specs
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
        return self._read_spec(spec, timeout_sec=timeout_sec)

    def read_after(self, key, after_sequence=None, timeout_sec=0.0):
        spec = self._specs.get(key)
        if spec is None:
            return _result(False, "ROS-R-UNKNOWN", f"Unknown ROS read topic: {key}", key=key)
        return self._read_spec_after(spec, after_sequence=after_sequence, timeout_sec=timeout_sec)

    def read_bool_topic(self, topic, timeout_sec=0.0):
        return self._read_spec(self._bool_topic_spec(topic), timeout_sec=timeout_sec)

    def read_bool_topic_after(self, topic, after_sequence=None, timeout_sec=0.0):
        return self._read_spec_after(self._bool_topic_spec(topic), after_sequence=after_sequence, timeout_sec=timeout_sec)

    def read_many(self, keys=None, timeout_sec=0.0):
        selected = keys or list(self._specs)
        return {
            "ok": True,
            "results": [self.read(key, timeout_sec=timeout_sec) for key in selected],
        }

    def _read_spec(self, spec, timeout_sec=0.0):
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

        return self._latest_result(spec, latest)

    def _read_spec_after(self, spec, after_sequence=None, timeout_sec=0.0):
        subscribe_result = self._ensure_subscription(spec)
        if not subscribe_result["ok"]:
            return subscribe_result

        deadline = time.monotonic() + timeout_sec if timeout_sec and timeout_sec > 0 else None
        with self._lock:
            while True:
                latest = self._latest.get(spec.key)
                sequence = latest.get("sequence") if latest else None
                if latest is not None and sequence != after_sequence:
                    break
                if deadline is None:
                    latest = None
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    latest = None
                    break
                self._condition.wait(remaining)

        if latest is None:
            return _result(
                False,
                "ROS-R-NODATA",
                f"No new message received from {spec.topic}.",
                key=spec.key,
                name=spec.name,
                topic=spec.topic,
                messageType=spec.message_type,
                afterSequence=after_sequence,
            )

        return self._latest_result(spec, latest, after_sequence=after_sequence)

    def _latest_result(self, spec, latest, after_sequence=None):
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
            sequence=latest["sequence"],
            afterSequence=after_sequence,
            data=latest["data"],
        )

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

    @staticmethod
    def _bool_topic_spec(topic):
        topic_name = str(topic or "").strip()
        key = f"state_machine_bool:{topic_name}"
        return TopicReadSpec(
            key=key,
            name=f"State machine bool signal {topic_name}",
            topic=topic_name,
            message_type="std_msgs/msg/Bool",
            stale_after_sec=1.0,
            description="State machine bool signal topic.",
        )
