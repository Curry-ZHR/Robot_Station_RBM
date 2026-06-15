import time

from modules.ros_io.commands import CommandValidationError, build_command
from modules.ros_io.registry import write_action_specs
from modules.ros_io.runtime import RosRuntimeError
from modules.ros_io.serializers import RosMessageImportError, import_message_class


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
            publisher.publish(message)
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
            publishedAt=time.strftime("%H:%M:%S"),
        )

    def publish_bool_topic(self, topic, value=True):
        topic_name = str(topic or "").strip()
        key = f"state_machine_bool:{topic_name}"
        message_type = "std_msgs/msg/Bool"
        try:
            message_class = import_message_class(message_type)
            message = message_class()
            message.data = bool(value)
            publisher = self._runtime.get_publisher(key, message_type, topic_name, qos_depth=10)
            publisher.publish(message)
        except (RosRuntimeError, RosMessageImportError) as exc:
            return _result(
                False,
                "ROS-W-UNAVAILABLE",
                str(exc),
                key=key,
                name=f"State machine bool signal {topic_name}",
                topic=topic_name,
                messageType=message_type,
            )

        return _result(
            True,
            "ROS-W-PUBLISHED",
            f"Published bool signal to {topic_name}.",
            key=key,
            name=f"State machine bool signal {topic_name}",
            topic=topic_name,
            messageType=message_type,
            data=bool(value),
            publishedAt=time.strftime("%H:%M:%S"),
        )
