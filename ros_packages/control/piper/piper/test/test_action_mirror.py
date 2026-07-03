from piper.action_mirror import LatestActionMirror, normalize_frame


def _frame(value):
    return normalize_frame(
        tuple(f"joint{index}" for index in range(7)),
        [value] * 7,
        [0.0] * 7,
        [0.0] * 7,
    )


def test_feedback_is_used_before_first_action():
    mirror = LatestActionMirror()
    feedback = _frame(0.1)

    mirror.update_feedback(feedback)

    assert mirror.current_frame() == feedback


def test_latest_action_wins_over_feedback():
    mirror = LatestActionMirror()
    feedback = _frame(0.1)
    action = _frame(0.4)

    mirror.update_feedback(feedback)
    mirror.update_action(action)

    assert mirror.current_frame() == action


def test_hold_does_not_replace_last_action():
    mirror = LatestActionMirror()
    action = _frame(0.4)
    hold_output = _frame(0.2)

    mirror.update_action(action)
    mirror.set_hold(True)
    selected = mirror.update_action(hold_output)

    assert selected == action
    assert mirror.current_frame() == action


def test_hold_before_action_keeps_feedback_fallback():
    mirror = LatestActionMirror()
    feedback = _frame(0.1)
    hold_output = _frame(0.2)

    mirror.update_feedback(feedback)
    mirror.set_hold(True)
    selected = mirror.update_action(hold_output)

    assert selected == feedback
    assert mirror.current_frame() == feedback


def test_clear_hold_allows_next_action():
    mirror = LatestActionMirror()
    first = _frame(0.1)
    held = _frame(0.2)
    second = _frame(0.3)

    mirror.update_action(first)
    mirror.set_hold(True)
    mirror.update_action(held)
    mirror.clear_hold()
    mirror.update_action(second)

    assert mirror.current_frame() == second
