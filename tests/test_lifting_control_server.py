import backend.server as server


class FakeMirror:
    def __init__(self, events):
        self.events = events

    def set_lifting_action(self, height_m):
        self.events.append(("mirror", height_m))


def _handler(path, payload):
    handler = object.__new__(server.RobotStationHandler)
    handler.path = path
    handler.read_json_body = lambda: payload
    handler.require_operator = lambda: True
    return handler


def test_lifting_height_mirror_updates_before_service(monkeypatch):
    events = []
    responses = []
    handler = _handler("/api/control/lifting/height", {"heightM": 0.3})

    def fake_move_lifting_to_height(payload):
        events.append(("service", dict(payload)))
        return {"ok": True, "code": "LIFT-C-OK", "detail": "ok"}

    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    monkeypatch.setattr(server, "get_action_mirror", lambda: FakeMirror(events))
    monkeypatch.setattr(server, "move_lifting_to_height", fake_move_lifting_to_height)
    monkeypatch.setattr(server, "log_action_result", lambda *args, **kwargs: None)

    server.RobotStationHandler.do_POST(handler)

    assert events == [
        ("mirror", 0.3),
        ("service", {"heightM": 0.3}),
    ]
    assert responses == [({"ok": True, "code": "LIFT-C-OK", "detail": "ok"}, 200)]


def test_lifting_height_invalid_payload_is_not_mirrored(monkeypatch):
    events = []
    responses = []
    handler = _handler("/api/control/lifting/height", {"heightM": True})

    def fake_move_lifting_to_height(payload):
        events.append(("service", dict(payload)))
        return {"ok": True, "code": "LIFT-C-OK", "detail": "ok"}

    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    monkeypatch.setattr(server, "get_action_mirror", lambda: FakeMirror(events))
    monkeypatch.setattr(server, "move_lifting_to_height", fake_move_lifting_to_height)
    monkeypatch.setattr(server, "log_action_result", lambda *args, **kwargs: None)

    server.RobotStationHandler.do_POST(handler)

    assert events == []
    assert responses[0][1] == 400
    assert responses[0][0]["code"] == "LIFT-C-PAYLOAD"
