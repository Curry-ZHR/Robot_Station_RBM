import backend.server as server


def _handler(path, payload=None):
    handler = object.__new__(server.RobotStationHandler)
    handler.path = path
    handler.read_json_body = lambda: payload or {}
    return handler


class FakeNavigationManager:
    def __init__(self):
        self.started = []
        self.stopped = 0
        self.interrupted = 0

    def status(self):
        return {"ok": True, "code": "NAV-STATUS", "status": "idle", "phase": "idle"}

    def start(self, payload):
        self.started.append(payload)
        return {"ok": True, "code": "NAV-STARTED", "status": "running", "phase": "lateral_translate"}

    def stop(self):
        self.stopped += 1
        return {"ok": True, "code": "NAV-STOPPED", "status": "stopped", "phase": "stopped"}

    def interrupt_for_manual_control(self):
        self.interrupted += 1
        return {"ok": True, "code": "NAV-STOPPED", "status": "stopped", "phase": "stopped"}


class FakeActionMirror:
    def __init__(self):
        self.chassis_calls = []

    def set_chassis_action(self, command):
        self.chassis_calls.append(command)


def test_navigation_status_endpoint(monkeypatch):
    manager = FakeNavigationManager()
    responses = []
    handler = _handler("/api/navigation/status")
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    monkeypatch.setattr(server, "get_navigation_manager", lambda: manager)

    server.RobotStationHandler.do_GET(handler)

    assert responses == [(manager.status(), 200)]


def test_navigation_start_and_stop_endpoints(monkeypatch):
    manager = FakeNavigationManager()
    responses = []
    monkeypatch.setattr(server, "get_navigation_manager", lambda: manager)
    monkeypatch.setattr(server, "log_action_result", lambda *args, **kwargs: None)

    handler = _handler("/api/navigation/start", {"mode": "lateral", "x": 1, "y": 2, "yawDeg": 90})
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    server.RobotStationHandler.do_POST(handler)

    handler = _handler("/api/navigation/stop")
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    server.RobotStationHandler.do_POST(handler)

    assert manager.started == [{"mode": "lateral", "x": 1, "y": 2, "yawDeg": 90}]
    assert manager.stopped == 1
    assert responses[0] == ({"ok": True, "code": "NAV-STARTED", "status": "running", "phase": "lateral_translate"}, 200)
    assert responses[1] == ({"ok": True, "code": "NAV-STOPPED", "status": "stopped", "phase": "stopped"}, 200)


def test_manual_chassis_velocity_interrupts_navigation(monkeypatch):
    manager = FakeNavigationManager()
    mirror = FakeActionMirror()
    responses = []
    handler = _handler("/api/control/chassis/cmd_vel", {"linearX": 0.1, "linearY": 0.0, "angularZ": 0.0})
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))
    monkeypatch.setattr(server, "get_navigation_manager", lambda: manager)
    monkeypatch.setattr(server, "get_action_mirror", lambda: mirror)
    monkeypatch.setattr(server, "log_action_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        server,
        "publish_chassis_velocity",
        lambda payload: {
            "ok": True,
            "code": "CHASSIS-C-PUBLISHED",
            "command": {
                "linearX": payload["linearX"],
                "linearY": payload["linearY"],
                "angularZ": payload["angularZ"],
            },
        },
    )

    server.RobotStationHandler.do_POST(handler)

    assert manager.interrupted == 1
    assert mirror.chassis_calls == [{"linearX": 0.1, "linearY": 0.0, "angularZ": 0.0}]
    assert responses[0][0]["code"] == "CHASSIS-C-PUBLISHED"
