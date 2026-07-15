"""High-level lifting commands shared by every orchestration entry point."""

from modules.data_collection import get_action_mirror
from modules.logger import get_logger

from .controller import lifting_target_height_m, move_lifting_to_height


LOGGER = get_logger()


def command_lifting_to_height(payload):
    """Mirror a valid height intent, then send it to the lifting controller.

    The mirror is deliberately updated before the hardware call.  It represents
    the command intent even when the driver later rejects or fails to execute it,
    matching the original HTTP control behaviour.
    """

    try:
        height_m = lifting_target_height_m(payload)
    except (TypeError, ValueError):
        # Keep validation errors and configured limits owned by the low-level
        # controller, while ensuring invalid commands never reach the mirror.
        return move_lifting_to_height(payload)

    try:
        get_action_mirror().set_lifting_action(height_m)
    except Exception as exc:
        # Dataset action mirroring must not make hardware control unavailable.
        LOGGER.warning("Action mirror lifting update failed: %s", exc)

    return move_lifting_to_height({"heightM": height_m})
