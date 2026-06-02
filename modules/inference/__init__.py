"""Remote WebSocket inference for Robot Station.

The local backend owns the robot safety boundary: it gathers observations,
sends them to a remote inference machine over a persistent WebSocket, validates
the returned action chunks against joint/lift/chassis limits, and executes only
the operator selected prefix of steps. Remote inference never publishes ROS
commands directly.
"""

from modules.inference.action_logs import InferenceActionLogger
from modules.inference.manager import InferenceManager, get_inference_manager
from modules.inference.observation import ObservationBuildError, build_observation
from modules.inference.session import RemoteInferenceSession, RemoteSessionError
from modules.inference.validation import ActionChunkValidationError, validate_action_chunk


__all__ = [
    "InferenceActionLogger",
    "InferenceManager",
    "get_inference_manager",
    "ObservationBuildError",
    "build_observation",
    "RemoteInferenceSession",
    "RemoteSessionError",
    "ActionChunkValidationError",
    "validate_action_chunk",
]
