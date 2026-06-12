import json

import pytest

from modules.data_collection.action_mirror import ActionMirror, ActionMirrorValidationError


class FakeString:
    def __init__(self):
        self.data = ""


class FakePublisher:
    def __init__(self, topic):
        self.topic = topic
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


class FakeRuntime:
    def __init__(self):
        self.publishers = {}

    def get_publisher(self, key, message_type, topic, qos_depth=10):
        if key not in self.publishers:
            self.publishers[key] = FakePublisher(topic)
        return self.publishers[key]


class FakeClock:
    def __init__(self, value=0.0):
        self.value = value

    def __call__(self):
        return self.value


def _last_payload(runtime, key):
    return json.loads(runtime.publishers[key].messages[-1].data)


def test_action_mirror_publishes_defaults():
    runtime = FakeRuntime()
    mirror = ActionMirror(runtime=runtime, message_class=FakeString)

    mirror.publish_once()

    assert "action_mirror_chassis" not in runtime.publishers
    assert runtime.publishers["action_mirror_lifting"].topic == "/action/lifting"
    assert _last_payload(runtime, "action_mirror_lifting") == {"height": 0.0}


def test_lifting_action_holds_last_height():
    clock = FakeClock(3.0)
    runtime = FakeRuntime()
    mirror = ActionMirror(runtime=runtime, message_class=FakeString, clock=clock)

    mirror.set_lifting_action(0.42)
    clock.value += 100.0
    mirror.publish_once()

    assert _last_payload(runtime, "action_mirror_lifting") == {"height": 0.42}


def test_rejects_invalid_action_values():
    mirror = ActionMirror(runtime=FakeRuntime(), message_class=FakeString)

    with pytest.raises(ActionMirrorValidationError):
        mirror.set_lifting_action(float("nan"))
