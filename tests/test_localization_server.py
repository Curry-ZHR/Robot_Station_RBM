import backend.server as server


def _handler(path, payload=None):
    handler = object.__new__(server.RobotStationHandler)
    handler.path = path
    handler.read_json_body = lambda: payload or {}
    return handler


class FakeLocalizationManager:
    def __init__(self):
        self.started = []
        self.stopped = 0

    def status(self):
        return {"ok": True, "code": "LOC-STATUS", "state": "stopped"}

    def start(self, payload):
        self.started.append(payload)
        return {"ok": True, "code": "LOC-STARTED", "map": {"name": payload["mapName"]}}

    def stop(self):
        self.stopped += 1
        return {"ok": True, "code": "LOC-STOPPED"}


def test_localization_status_endpoint(monkeypatch):
    manager = FakeLocalizationManager()
    responses = []
    handler = _handler("/api/localization/status")
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    monkeypatch.setattr(server, "get_localization_manager", lambda: manager)

    server.RobotStationHandler.do_GET(handler)

    assert responses == [(manager.status(), 200)]


def test_localization_start_and_stop_endpoints(monkeypatch):
    manager = FakeLocalizationManager()
    responses = []
    handler = _handler("/api/localization/start", {"mapName": "lab_map"})
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    monkeypatch.setattr(server, "get_localization_manager", lambda: manager)
    monkeypatch.setattr(server, "log_action_result", lambda *args, **kwargs: None)

    server.RobotStationHandler.do_POST(handler)

    handler = _handler("/api/localization/stop")
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    server.RobotStationHandler.do_POST(handler)

    assert manager.started == [{"mapName": "lab_map"}]
    assert manager.stopped == 1
    assert responses[0] == ({"ok": True, "code": "LOC-STARTED", "map": {"name": "lab_map"}}, 200)
    assert responses[1] == ({"ok": True, "code": "LOC-STOPPED"}, 200)
