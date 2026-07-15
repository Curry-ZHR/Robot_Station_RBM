import backend.server as server


def _handler(path, payload):
    handler = object.__new__(server.RobotStationHandler)
    handler.path = path
    handler.read_json_body = lambda: payload
    return handler


def test_lifting_height_delegates_to_shared_command(monkeypatch):
    events = []
    responses = []
    handler = _handler("/api/control/lifting/height", {"heightM": 0.3})

    def fake_command_lifting_to_height(payload):
        events.append(("command", dict(payload)))
        return {"ok": True, "code": "LIFT-C-OK", "detail": "ok"}

    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    monkeypatch.setattr(server, "command_lifting_to_height", fake_command_lifting_to_height)
    monkeypatch.setattr(server, "log_action_result", lambda *args, **kwargs: None)

    server.RobotStationHandler.do_POST(handler)

    assert events == [("command", {"heightM": 0.3})]
    assert responses == [({"ok": True, "code": "LIFT-C-OK", "detail": "ok"}, 200)]


def test_lifting_height_invalid_payload_returns_bad_request(monkeypatch):
    events = []
    responses = []
    handler = _handler("/api/control/lifting/height", {"heightM": True})

    def fake_command_lifting_to_height(payload):
        events.append(("command", dict(payload)))
        return {"ok": False, "code": "LIFT-C-PAYLOAD", "detail": "invalid"}

    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    monkeypatch.setattr(server, "command_lifting_to_height", fake_command_lifting_to_height)
    monkeypatch.setattr(server, "log_action_result", lambda *args, **kwargs: None)

    server.RobotStationHandler.do_POST(handler)

    assert events == [("command", {"heightM": True})]
    assert responses[0][1] == 400
    assert responses[0][0]["code"] == "LIFT-C-PAYLOAD"
