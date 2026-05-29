import time

from modules.logger import get_logger
from modules.ros_io.commands import CommandValidationError, build_command
from modules.ros_io.registry import write_action_specs
from modules.ros_io.runtime import RosRuntimeError
from modules.ros_io.serializers import RosMessageImportError, import_message_class

LOGGER = get_logger()


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


class RosTopicWriter:
    def __init__(self, runtime, specs=None):
        self._runtime = runtime
        self._specs = specs or write_action_specs()

    def list_actions(self):
        return {
            "ok": True,
            "actions": [spec.to_dict() for spec in self._specs.values()],
        }

    def publish(self, key, payload):
        spec = self._specs.get(key)
        if spec is None:
            return _result(False, "ROS-W-UNKNOWN", f"Unknown ROS write action: {key}", key=key)

        debug_chassis = key == "chassis_cmd_vel"
        trace_id = payload.get("commandTraceId", payload.get("traceId", ""))
        sequence = payload.get("commandSequence", payload.get("sequence", ""))
        start = time.perf_counter()
        try:
            message_class = import_message_class(spec.message_type)
            message = build_command(spec.builder, payload, message_class)
            stamp = self._runtime.now_msg()
            if hasattr(message, "header"):
                message.header.stamp = stamp
            publisher = self._runtime.get_publisher(
                spec.key,
                spec.message_type,
                spec.topic,
                qos_depth=spec.qos_depth,
            )
            before_publish = time.perf_counter()
            if debug_chassis:
                LOGGER.info(
                    "CHASSIS_DEBUG ros_writer.before_publish trace=%s seq=%s key=%s topic=%s qos=%s build_elapsed_ms=%.3f t=%.6f",
                    trace_id,
                    sequence,
                    spec.key,
                    spec.topic,
                    spec.qos_depth,
                    (before_publish - start) * 1000.0,
                    before_publish,
                )
            publisher.publish(message)
            after_publish = time.perf_counter()
            if debug_chassis:
                LOGGER.info(
                    "CHASSIS_DEBUG ros_writer.after_publish trace=%s seq=%s key=%s topic=%s publish_elapsed_ms=%.3f total_elapsed_ms=%.3f t=%.6f",
                    trace_id,
                    sequence,
                    spec.key,
                    spec.topic,
                    (after_publish - before_publish) * 1000.0,
                    (after_publish - start) * 1000.0,
                    after_publish,
                )
        except CommandValidationError as exc:
            return _result(
                False,
                "ROS-W-PAYLOAD",
                str(exc),
                key=spec.key,
                name=spec.name,
                topic=spec.topic,
                messageType=spec.message_type,
            )
        except (RosRuntimeError, RosMessageImportError) as exc:
            return _result(
                False,
                "ROS-W-UNAVAILABLE",
                str(exc),
                key=spec.key,
                name=spec.name,
                topic=spec.topic,
                messageType=spec.message_type,
            )

        return _result(
            True,
            "ROS-W-PUBLISHED",
            f"Published command to {spec.topic}.",
            key=spec.key,
            name=spec.name,
            topic=spec.topic,
            messageType=spec.message_type,
            debugTiming={
                "writerTotalElapsedMs": round((time.perf_counter() - start) * 1000.0, 3),
            },
            publishedAt=time.strftime("%H:%M:%S"),
        )
