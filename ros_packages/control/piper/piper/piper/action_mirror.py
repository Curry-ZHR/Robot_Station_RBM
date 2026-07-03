from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from piper.joint_smoother import normalize_names, normalize_positions, normalize_vector


@dataclass(frozen=True)
class JointMirrorFrame:
    names: Tuple[str, ...]
    positions: Tuple[float, ...]
    velocity: Tuple[float, ...]
    effort: Tuple[float, ...]


def normalize_frame(names: Iterable[str], positions: Sequence[float], velocity=None, effort=None):
    parsed_names = tuple(names) if names is not None else ()
    return JointMirrorFrame(
        names=normalize_names(parsed_names),
        positions=normalize_positions(positions),
        velocity=normalize_vector(velocity),
        effort=normalize_vector(effort),
    )


class LatestActionMirror:
    """Keeps the action-label frame to publish.

    The selected frame is the latest pre-control action when one exists. Before
    the first action arrives, feedback is used as the static fallback so the
    action label means "hold current state" instead of a fake zero target.
    """

    def __init__(self):
        self._last_action: Optional[JointMirrorFrame] = None
        self._feedback: Optional[JointMirrorFrame] = None
        self._hold_active = False

    def update_action(self, frame: JointMirrorFrame):
        if self._hold_active:
            return self.current_frame()
        self._last_action = frame
        return self._last_action

    def update_feedback(self, frame: JointMirrorFrame):
        self._feedback = frame
        return self.current_frame()

    def set_hold(self, active=True):
        self._hold_active = bool(active)
        return self.current_frame()

    def clear_hold(self):
        self._hold_active = False
        return self.current_frame()

    def current_frame(self):
        return self._last_action or self._feedback
