import math
import threading
import time

from modules.control.chassis import chassis_limits, publish_chassis_velocity
from modules.ros_io import get_ros_reader


DEFAULT_MAX_LINEAR_MPS = 0.20
DEFAULT_MAX_LATERAL_MPS = 0.15
DEFAULT_MAX_ANGULAR_RAD_S = 0.50
DEFAULT_POSITION_TOLERANCE_M = 0.05
DEFAULT_YAW_TOLERANCE_DEG = 3.0
DEFAULT_LOCALIZATION_STALE_SEC = 0.8
DEFAULT_CONTROL_RATE_HZ = 20.0
DEFAULT_POSITION_GAIN = 0.9
DEFAULT_YAW_GAIN = 1.4
MIN_POSITION_TOLERANCE_M = 0.02
MIN_YAW_TOLERANCE_DEG = 1.0
MIN_LINEAR_COMMAND_MPS = 0.025
MIN_LATERAL_COMMAND_MPS = 0.025
MIN_ANGULAR_COMMAND_RAD_S = 0.06
ROTATION_DRIFT_REPLAN_FACTOR = 2.0

PHASE_IDLE = "idle"
PHASE_LATERAL_TRANSLATE = "lateral_translate"
PHASE_FORWARD_TRANSLATE = "forward_translate"
PHASE_OMNI_TRANSLATE = "omni_translate"
PHASE_ROTATE = "rotate"
PHASE_COMPLETED = "completed"
PHASE_STOPPED = "stopped"
PHASE_FAILED = "failed"


class NavigationValidationError(ValueError):
    pass


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def navigation_result_status(result):
    if result.get("ok"):
        return 200
    mapping = {
        "NAV-PAYLOAD": 400,
        "NAV-ACTION": 400,
        "NAV-BUSY": 409,
        "NAV-NOTRUNNING": 200,
        "NAV-LOCALIZATION": 409,
        "NAV-CHASSIS": 503,
    }
    return mapping.get(result.get("code", ""), 500)


def _as_payload_dict(payload):
    if not isinstance(payload, dict):
        raise NavigationValidationError("Payload must be a JSON object.")
    return payload


def _finite_number(value, field):
    if isinstance(value, bool):
        raise NavigationValidationError(f"{field} must be a number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise NavigationValidationError(f"{field} must be a number.") from exc
    if not math.isfinite(parsed):
        raise NavigationValidationError(f"{field} must be a finite number.")
    return parsed


def _payload_number(payload, keys, field, default=None):
    for key in keys:
        if key in payload:
            return _finite_number(payload[key], field)
    if default is None:
        raise NavigationValidationError(f"{field} is required.")
    return _finite_number(default, field)


def _optional_positive_number(payload, keys, field, default, minimum, maximum=None):
    value = _payload_number(payload, keys, field, default=default)
    if value < minimum:
        raise NavigationValidationError(f"{field} must be >= {minimum:g}.")
    if maximum is not None and value > maximum:
        raise NavigationValidationError(f"{field} must be <= {maximum:g}.")
    return value


def _normalize_angle(angle):
    normalized = (angle + math.pi) % (2.0 * math.pi) - math.pi
    return 0.0 if abs(normalized) < 1e-12 else normalized


def _target_yaw(payload):
    for key in ("yawDeg", "yaw_deg", "yawDegrees", "thetaDeg", "theta_deg"):
        if key in payload:
            return math.radians(_finite_number(payload[key], key))
    for key in ("yawRad", "yaw_rad", "theta", "yaw"):
        if key in payload:
            return _finite_number(payload[key], key)
    raise NavigationValidationError("yawDeg or yawRad is required.")


def _yaw_from_quaternion(orientation):
    if not isinstance(orientation, dict):
        raise NavigationValidationError("Localization pose orientation is unavailable.")
    x = _finite_number(orientation.get("x"), "orientation.x")
    y = _finite_number(orientation.get("y"), "orientation.y")
    z = _finite_number(orientation.get("z"), "orientation.z")
    w = _finite_number(orientation.get("w"), "orientation.w")
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def _pose_source(data):
    if not isinstance(data, dict):
        raise NavigationValidationError("Localization pose data is unavailable.")
    pose = data.get("pose")
    if isinstance(pose, dict) and isinstance(pose.get("pose"), dict):
        pose = pose["pose"]
    if not isinstance(pose, dict):
        raise NavigationValidationError("Localization pose field is unavailable.")
    return pose


def _pose_from_localization_result(result):
    if not result.get("ok"):
        return None, result.get("detail") or "Localization pose is unavailable."
    if result.get("stale") and result.get("ageMs") is None:
        return None, result.get("detail") or "Localization pose is stale."

    try:
        pose = _pose_source(result.get("data"))
        position = pose.get("position")
        if not isinstance(position, dict):
            raise NavigationValidationError("Localization pose position is unavailable.")
        yaw = _yaw_from_quaternion(pose.get("orientation"))
        parsed = {
            "x": _finite_number(position.get("x"), "position.x"),
            "y": _finite_number(position.get("y"), "position.y"),
            "z": _finite_number(position.get("z", 0.0), "position.z"),
            "yawRad": yaw,
            "yawDeg": math.degrees(yaw),
            "frameId": result.get("data", {}).get("header", {}).get("frame_id", ""),
            "ageMs": result.get("ageMs"),
            "receivedAt": result.get("receivedAt"),
        }
    except NavigationValidationError as exc:
        return None, str(exc)
    return parsed, ""


def _pose_to_status(pose):
    if not pose:
        return None
    return {
        "x": pose["x"],
        "y": pose["y"],
        "z": pose.get("z", 0.0),
        "yawRad": pose["yawRad"],
        "yawDeg": pose["yawDeg"],
        "frameId": pose.get("frameId", ""),
        "ageMs": pose.get("ageMs"),
        "receivedAt": pose.get("receivedAt"),
    }


def _project_to_reference_frame(dx, dy, yaw):
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    return {
        "bodyX": cos_yaw * dx + sin_yaw * dy,
        "bodyY": -sin_yaw * dx + cos_yaw * dy,
    }


def _sign_preserving_command(error, gain, minimum, maximum):
    magnitude = min(maximum, max(minimum, abs(error) * gain))
    return math.copysign(magnitude, error)


class NavigationManager:
    def __init__(self, reader=None, publisher=None):
        self._reader = reader
        self._publisher = publisher or publish_chassis_velocity
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread = None
        self._state = self._base_state()

    def _base_state(self):
        return {
            "status": "idle",
            "phase": PHASE_IDLE,
            "running": False,
            "target": None,
            "params": self._default_params(),
            "translationYawRad": None,
            "translationYawDeg": None,
            "currentPose": None,
            "errors": None,
            "command": {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0},
            "startedAt": None,
            "updatedAt": None,
            "completedAt": None,
            "stoppedAt": None,
            "failedAt": None,
            "detail": "Navigation is idle.",
            "lastError": "",
            "lastPublish": None,
        }

    def _default_params(self):
        return {
            "maxLinearMps": DEFAULT_MAX_LINEAR_MPS,
            "maxLateralMps": DEFAULT_MAX_LATERAL_MPS,
            "maxAngularRadS": DEFAULT_MAX_ANGULAR_RAD_S,
            "positionToleranceM": DEFAULT_POSITION_TOLERANCE_M,
            "yawToleranceDeg": DEFAULT_YAW_TOLERANCE_DEG,
            "yawToleranceRad": math.radians(DEFAULT_YAW_TOLERANCE_DEG),
            "localizationStaleSec": DEFAULT_LOCALIZATION_STALE_SEC,
            "controlRateHz": DEFAULT_CONTROL_RATE_HZ,
        }

    def _reader_instance(self):
        return self._reader or get_ros_reader()

    def status(self):
        with self._lock:
            return _result(True, "NAV-STATUS", self._state.get("detail", "Navigation status."), **self._state_payload())

    def start(self, payload):
        try:
            target, params = self._command_from_payload(payload)
        except NavigationValidationError as exc:
            return _result(False, "NAV-PAYLOAD", str(exc), status=self.status().get("status", "idle"))

        with self._lock:
            if self._state.get("running"):
                return _result(False, "NAV-BUSY", "Navigation is already running.", **self._state_payload())

        pose, error = self._read_current_pose(params, wait_sec=0.2)
        if pose is None:
            return _result(False, "NAV-LOCALIZATION", error, status="failed", phase=PHASE_FAILED)

        now_text = time.strftime("%H:%M:%S")
        translation_yaw = pose["yawRad"]
        initial_phase = PHASE_LATERAL_TRANSLATE if target["mode"] == "lateral" else PHASE_OMNI_TRANSLATE
        self._stop_event.clear()
        with self._lock:
            self._state = self._base_state()
            self._state.update(
                {
                    "status": "running",
                    "phase": initial_phase,
                    "running": True,
                    "target": target,
                    "params": params,
                    "translationYawRad": translation_yaw,
                    "translationYawDeg": math.degrees(translation_yaw),
                    "currentPose": _pose_to_status(pose),
                    "startedAt": now_text,
                    "updatedAt": now_text,
                    "detail": "Navigation started.",
                }
            )

        thread = threading.Thread(target=self._run_loop, name="robot_station_navigation", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return _result(True, "NAV-STARTED", "Navigation started.", **self._state_payload())

    def stop(self, detail="Navigation stopped."):
        with self._lock:
            was_running = bool(self._state.get("running"))
        self._stop_event.set()
        publish_result = self._publish_stop()
        with self._lock:
            if was_running:
                now_text = time.strftime("%H:%M:%S")
                self._state.update(
                    {
                        "status": "stopped",
                        "phase": PHASE_STOPPED,
                        "running": False,
                        "command": {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0},
                        "stoppedAt": now_text,
                        "updatedAt": now_text,
                        "detail": detail,
                        "lastPublish": publish_result,
                    }
                )
                return _result(True, "NAV-STOPPED", detail, **self._state_payload())
            self._state["lastPublish"] = publish_result
            return _result(True, "NAV-NOTRUNNING", "Navigation is not running.", **self._state_payload())

    def interrupt_for_manual_control(self, detail="Navigation interrupted by manual chassis control."):
        with self._lock:
            if not self._state.get("running"):
                return None
        return self.stop(detail=detail)

    def is_running(self):
        with self._lock:
            return bool(self._state.get("running"))

    def _state_copy(self):
        state = {}
        for key, value in self._state.items():
            if isinstance(value, dict):
                state[key] = dict(value)
            else:
                state[key] = value
        return state

    def _state_payload(self):
        state = self._state_copy()
        state.pop("detail", None)
        return state

    def _command_from_payload(self, payload):
        payload = _as_payload_dict(payload)
        mode = str(payload.get("mode", "")).strip().lower()
        if mode not in {"lateral", "omni"}:
            raise NavigationValidationError("mode must be 'lateral' or 'omni'.")

        hard_limits = chassis_limits().get("limits", {})
        hard_linear = _finite_number(hard_limits.get("maxLinearMps", DEFAULT_MAX_LINEAR_MPS), "maxLinearMps")
        hard_lateral = _finite_number(hard_limits.get("maxLateralMps", DEFAULT_MAX_LATERAL_MPS), "maxLateralMps")
        hard_angular = _finite_number(hard_limits.get("maxAngularRadS", DEFAULT_MAX_ANGULAR_RAD_S), "maxAngularRadS")

        target = {
            "mode": mode,
            "x": _payload_number(payload, ("x",), "x"),
            "y": _payload_number(payload, ("y",), "y"),
            "z": 0.0,
            "yawRad": _normalize_angle(_target_yaw(payload)),
        }
        target["yawDeg"] = math.degrees(target["yawRad"])

        yaw_tolerance_deg = _optional_positive_number(
            payload,
            ("yawToleranceDeg", "yaw_tolerance_deg"),
            "yawToleranceDeg",
            DEFAULT_YAW_TOLERANCE_DEG,
            MIN_YAW_TOLERANCE_DEG,
            45.0,
        )
        default_max_linear = min(DEFAULT_MAX_LINEAR_MPS, hard_linear)
        default_max_lateral = min(DEFAULT_MAX_LATERAL_MPS, hard_lateral)
        default_max_angular = min(DEFAULT_MAX_ANGULAR_RAD_S, hard_angular)
        params = {
            "maxLinearMps": _optional_positive_number(
                payload,
                ("maxLinearMps", "max_linear_mps"),
                "maxLinearMps",
                default_max_linear,
                0.01,
                hard_linear,
            ),
            "maxLateralMps": _optional_positive_number(
                payload,
                ("maxLateralMps", "max_lateral_mps"),
                "maxLateralMps",
                default_max_lateral,
                0.01,
                hard_lateral,
            ),
            "maxAngularRadS": _optional_positive_number(
                payload,
                ("maxAngularRadS", "max_angular_rad_s"),
                "maxAngularRadS",
                default_max_angular,
                0.02,
                hard_angular,
            ),
            "positionToleranceM": _optional_positive_number(
                payload,
                ("positionToleranceM", "position_tolerance_m"),
                "positionToleranceM",
                DEFAULT_POSITION_TOLERANCE_M,
                MIN_POSITION_TOLERANCE_M,
                1.0,
            ),
            "yawToleranceDeg": yaw_tolerance_deg,
            "yawToleranceRad": math.radians(yaw_tolerance_deg),
            "localizationStaleSec": _optional_positive_number(
                payload,
                ("localizationStaleSec", "localization_stale_sec"),
                "localizationStaleSec",
                DEFAULT_LOCALIZATION_STALE_SEC,
                0.1,
                5.0,
            ),
            "controlRateHz": _optional_positive_number(
                payload,
                ("controlRateHz", "control_rate_hz"),
                "controlRateHz",
                DEFAULT_CONTROL_RATE_HZ,
                5.0,
                50.0,
            ),
            "positionGain": DEFAULT_POSITION_GAIN,
            "yawGain": DEFAULT_YAW_GAIN,
            "hardLimits": {
                "maxLinearMps": hard_linear,
                "maxLateralMps": hard_lateral,
                "maxAngularRadS": hard_angular,
            },
        }
        return target, params

    def _read_current_pose(self, params, wait_sec=0.0):
        result = self._reader_instance().read("localization_pose", timeout_sec=wait_sec)
        pose, error = _pose_from_localization_result(result)
        if pose is None:
            return None, error
        age_ms = pose.get("ageMs")
        if age_ms is not None and age_ms > params["localizationStaleSec"] * 1000:
            return None, f"Localization pose is stale: {age_ms} ms old."
        return pose, ""

    def _run_loop(self):
        try:
            while not self._stop_event.is_set():
                with self._lock:
                    state = self._state_copy()
                target = state.get("target") or {}
                params = state.get("params") or self._default_params()
                pose, error = self._read_current_pose(params)
                if pose is None:
                    self._fail(f"Navigation stopped: {error}")
                    return

                command, next_phase, errors, done = self._next_command(state, target, params, pose)
                if done:
                    self._complete(pose, errors)
                    return

                if self._stop_event.is_set():
                    return

                publish_result = self._publisher(command)
                if not publish_result.get("ok"):
                    self._fail(publish_result.get("detail", "Failed to publish chassis velocity command."))
                    return

                with self._lock:
                    if not self._state.get("running"):
                        return
                    now_text = time.strftime("%H:%M:%S")
                    self._state.update(
                        {
                            "phase": next_phase,
                            "currentPose": _pose_to_status(pose),
                            "errors": errors,
                            "command": command,
                            "updatedAt": now_text,
                            "detail": f"Navigation phase: {next_phase}.",
                            "lastPublish": publish_result,
                        }
                    )
                time.sleep(1.0 / params["controlRateHz"])
        finally:
            self._publish_stop()

    def _next_command(self, state, target, params, pose):
        dx = target["x"] - pose["x"]
        dy = target["y"] - pose["y"]
        projected = _project_to_reference_frame(dx, dy, state["translationYawRad"])
        distance = math.hypot(dx, dy)
        yaw_error = _normalize_angle(target["yawRad"] - pose["yawRad"])
        errors = {
            **projected,
            "distance": distance,
            "yawRad": yaw_error,
            "yawDeg": math.degrees(yaw_error),
        }

        phase = state.get("phase")
        position_tolerance = params["positionToleranceM"]
        yaw_tolerance = params["yawToleranceRad"]
        if target["mode"] == "lateral":
            if phase not in {PHASE_LATERAL_TRANSLATE, PHASE_FORWARD_TRANSLATE, PHASE_ROTATE}:
                phase = PHASE_LATERAL_TRANSLATE
            if phase == PHASE_LATERAL_TRANSLATE and abs(errors["bodyY"]) <= position_tolerance:
                phase = PHASE_FORWARD_TRANSLATE
            if phase == PHASE_FORWARD_TRANSLATE and abs(errors["bodyX"]) <= position_tolerance:
                phase = PHASE_ROTATE
        else:
            if phase not in {PHASE_OMNI_TRANSLATE, PHASE_ROTATE}:
                phase = PHASE_OMNI_TRANSLATE
            if phase == PHASE_OMNI_TRANSLATE and distance <= position_tolerance:
                phase = PHASE_ROTATE

        if phase == PHASE_ROTATE:
            if distance > position_tolerance * ROTATION_DRIFT_REPLAN_FACTOR:
                phase = PHASE_LATERAL_TRANSLATE if target["mode"] == "lateral" and abs(errors["bodyY"]) > position_tolerance else (
                    PHASE_FORWARD_TRANSLATE if target["mode"] == "lateral" else PHASE_OMNI_TRANSLATE
                )
            elif abs(yaw_error) <= yaw_tolerance:
                return {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0}, PHASE_COMPLETED, errors, True

        if phase == PHASE_LATERAL_TRANSLATE:
            lateral = _sign_preserving_command(
                errors["bodyY"],
                params["positionGain"],
                MIN_LATERAL_COMMAND_MPS,
                params["maxLateralMps"],
            )
            return {"linearX": 0.0, "linearY": lateral, "angularZ": 0.0}, phase, errors, False

        if phase == PHASE_FORWARD_TRANSLATE:
            linear = _sign_preserving_command(
                errors["bodyX"],
                params["positionGain"],
                MIN_LINEAR_COMMAND_MPS,
                params["maxLinearMps"],
            )
            return {"linearX": linear, "linearY": 0.0, "angularZ": 0.0}, phase, errors, False

        if phase == PHASE_OMNI_TRANSLATE:
            linear = _sign_preserving_command(
                errors["bodyX"],
                params["positionGain"],
                MIN_LINEAR_COMMAND_MPS,
                params["maxLinearMps"],
            )
            lateral = _sign_preserving_command(
                errors["bodyY"],
                params["positionGain"],
                MIN_LATERAL_COMMAND_MPS,
                params["maxLateralMps"],
            )
            if abs(errors["bodyX"]) <= position_tolerance:
                linear = 0.0
            if abs(errors["bodyY"]) <= position_tolerance:
                lateral = 0.0
            return {"linearX": linear, "linearY": lateral, "angularZ": 0.0}, phase, errors, False

        angular = _sign_preserving_command(
            yaw_error,
            params["yawGain"],
            MIN_ANGULAR_COMMAND_RAD_S,
            params["maxAngularRadS"],
        )
        return {"linearX": 0.0, "linearY": 0.0, "angularZ": angular}, PHASE_ROTATE, errors, False

    def _publish_stop(self):
        return self._publisher({"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0})

    def _complete(self, pose, errors):
        publish_result = self._publish_stop()
        with self._lock:
            now_text = time.strftime("%H:%M:%S")
            self._state.update(
                {
                    "status": "completed",
                    "phase": PHASE_COMPLETED,
                    "running": False,
                    "currentPose": _pose_to_status(pose),
                    "errors": errors,
                    "command": {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0},
                    "completedAt": now_text,
                    "updatedAt": now_text,
                    "detail": "Navigation completed.",
                    "lastPublish": publish_result,
                }
            )

    def _fail(self, detail):
        publish_result = self._publish_stop()
        with self._lock:
            now_text = time.strftime("%H:%M:%S")
            self._state.update(
                {
                    "status": "failed",
                    "phase": PHASE_FAILED,
                    "running": False,
                    "command": {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0},
                    "failedAt": now_text,
                    "updatedAt": now_text,
                    "detail": detail,
                    "lastError": detail,
                    "lastPublish": publish_result,
                }
            )


_navigation_manager = None
_navigation_manager_lock = threading.Lock()


def get_navigation_manager():
    global _navigation_manager
    with _navigation_manager_lock:
        if _navigation_manager is None:
            _navigation_manager = NavigationManager()
        return _navigation_manager
