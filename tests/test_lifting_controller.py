from modules.control.lifting import lifting_target_height_m
from modules.control.lifting import commands
from modules.control.lifting import controller


def test_lifting_target_height_m_accepts_supported_field_names():
    assert lifting_target_height_m({"heightM": 0.2}) == 0.2
    assert lifting_target_height_m({"height": 0.3}) == 0.3
    assert lifting_target_height_m({"targetHeightM": 0.4}) == 0.4


def test_immediate_callback_motion_states_are_accepted(monkeypatch):
    monkeypatch.setattr(controller, "_callback_mode", lambda: 1)

    assert controller._state_ok(0, -1)
    assert controller._state_ok(0, 0)
    assert controller._state_ok(-4, -1)
    assert controller._state_ok(-2, -1)


def test_blocking_callback_still_requires_position_success(monkeypatch):
    monkeypatch.setattr(controller, "_callback_mode", lambda: 0)

    assert not controller._state_ok(0, -1)
    assert controller._state_ok(0, 1)


def test_shared_lifting_command_mirrors_before_hardware(monkeypatch):
    events = []

    class FakeMirror:
        def set_lifting_action(self, height_m):
            events.append(("mirror", height_m))

    def fake_move(payload):
        events.append(("service", dict(payload)))
        return {"ok": True, "code": "LIFT-C-OK", "detail": "ok"}

    monkeypatch.setattr(commands, "get_action_mirror", lambda: FakeMirror())
    monkeypatch.setattr(commands, "move_lifting_to_height", fake_move)

    result = commands.command_lifting_to_height({"height": 0.3})

    assert result["ok"] is True
    assert events == [("mirror", 0.3), ("service", {"heightM": 0.3})]


def test_shared_lifting_command_does_not_mirror_invalid_height(monkeypatch):
    events = []

    class FakeMirror:
        def set_lifting_action(self, height_m):
            events.append(("mirror", height_m))

    def fake_move(payload):
        events.append(("service", dict(payload)))
        return {"ok": False, "code": "LIFT-C-PAYLOAD", "detail": "invalid"}

    monkeypatch.setattr(commands, "get_action_mirror", lambda: FakeMirror())
    monkeypatch.setattr(commands, "move_lifting_to_height", fake_move)

    result = commands.command_lifting_to_height({"heightM": True})

    assert result["ok"] is False
    assert events == [("service", {"heightM": True})]
