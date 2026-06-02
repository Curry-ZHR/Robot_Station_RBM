from modules.control.lifting import lifting_target_height_m
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
