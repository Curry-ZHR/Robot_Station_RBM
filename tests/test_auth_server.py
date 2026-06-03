import backend.server as server


class FakeInference:
    def __init__(self, events):
        self.events = events

    def disconnect(self):
        self.events.append(("inference", "disconnect"))
        return {"ok": True}


class FakePlayback:
    def __init__(self, events):
        self.events = events

    def stop(self, reason="stop"):
        self.events.append(("playback", reason))
        return {"ok": True}


def test_operator_handoff_holds_piper_without_disabling_enable(monkeypatch):
    events = []

    def fake_publish_joint_targets(payload):
        events.append(("piper", dict(payload)))
        return {"ok": True}

    monkeypatch.setattr(server, "get_inference_manager", lambda: FakeInference(events))
    monkeypatch.setattr(server, "get_playback_manager", lambda: FakePlayback(events))
    monkeypatch.setattr(server, "publish_joint_targets", fake_publish_joint_targets)
    monkeypatch.setattr(server, "stop_chassis", lambda payload=None: events.append(("chassis", payload)) or {"ok": True})
    monkeypatch.setattr(server, "stop_lifting", lambda payload=None: events.append(("lifting", payload)) or {"ok": True})

    result = server.release_operator_outputs("forced login by caizj")

    assert result["piperHold"]["ok"]
    assert ("piper", {"hold": True}) in events
    assert all(event != ("piper", {"enable": False}) for event in events)
    assert all(event != ("piper", {"enabled": False}) for event in events)


def test_post_api_requires_authenticated_operator(monkeypatch):
    responses = []
    handler = object.__new__(server.RobotStationHandler)
    handler.path = "/api/control/chassis/stop"
    handler.headers = {}
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))

    class FakeAuth:
        def require_operator(self, token=None):
            return False, {"ok": False, "code": "AUTH-REQUIRED", "detail": "Login required."}

    monkeypatch.setattr(server, "get_auth_manager", lambda: FakeAuth())

    server.RobotStationHandler.do_POST(handler)

    assert responses == [
        ({"ok": False, "code": "AUTH-REQUIRED", "detail": "Login required."}, 401),
    ]
