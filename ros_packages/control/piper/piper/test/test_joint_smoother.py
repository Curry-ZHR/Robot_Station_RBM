import math

from piper.joint_smoother import LatestTargetSmoother, interpolate_positions


def test_interpolate_snaps_when_delta_is_smaller_than_step():
    current = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.01)
    target = (0.01, -0.01, 0.02, -0.02, 0.0, 0.0, 0.05)

    positions, reached = interpolate_positions(current, target, max_joint_step_rad=0.03)

    assert positions == target
    assert reached is True


def test_interpolate_limits_positive_and_negative_joint_steps():
    current = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.01)
    target = (1.0, -1.0, 0.2, -0.2, 0.0, 0.0, 0.08)

    positions, reached = interpolate_positions(current, target, max_joint_step_rad=0.1)

    assert positions[:6] == (0.1, -0.1, 0.1, -0.1, 0.0, 0.0)
    assert positions[6] == 0.08
    assert reached is False


def test_latest_target_wins_from_current_interpolation_position():
    smoother = LatestTargetSmoother(default_max_joint_speed_deg_s=10)
    smoother.update_feedback((0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    smoother.set_target((math.radians(10), 0.0, 0.0, 0.0, 0.0, 0.0, 0.02))

    first = smoother.tick(0.5)
    assert math.isclose(first.positions[0], math.radians(5))

    smoother.set_target((math.radians(-10), 0.0, 0.0, 0.0, 0.0, 0.0, 0.04))
    second = smoother.tick(0.5)

    assert math.isclose(second.positions[0], 0.0, abs_tol=1e-12)
    assert second.positions[6] == 0.04


def test_first_target_waits_for_feedback_before_output():
    smoother = LatestTargetSmoother(default_max_joint_speed_deg_s=5)
    initialized = smoother.set_target((0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

    assert initialized is False
    assert smoother.tick(0.1) is None

    smoother.update_feedback((0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    assert smoother.tick(0.1) is not None
