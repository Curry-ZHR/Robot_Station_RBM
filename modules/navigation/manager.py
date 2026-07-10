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
DEFAULT_ARRIVAL_STABLE_SEC = 0.5
DEFAULT_NEAR_TARGET_RADIUS_M = 0.15
DEFAULT_LATERAL_DEADBAND_M = 0.04
DEFAULT_LATERAL_ENTER_THRESHOLD_M = 0.08
DEFAULT_LATERAL_DOMINANT_LINEAR_DEADBAND_MPS = 0.04
MIN_POSITION_TOLERANCE_M = 0.02
MIN_YAW_TOLERANCE_DEG = 1.0
MIN_LINEAR_COMMAND_MPS = 0.025
MIN_LATERAL_COMMAND_MPS = 0.025
MIN_ANGULAR_COMMAND_RAD_S = 0.06
ROTATION_DRIFT_REPLAN_FACTOR = 2.0
ARRIVAL_POSITION_HOLD_FACTOR = 1.5
ARRIVAL_YAW_HOLD_FACTOR = 1.5
NEAR_TARGET_RADIUS_FACTOR = 3.0

PHASE_IDLE = "idle"
PHASE_LATERAL_TRANSLATE = "lateral_translate"
PHASE_FORWARD_TRANSLATE = "forward_translate"
PHASE_OMNI_TRANSLATE = "omni_translate"
PHASE_ROTATE = "rotate"
PHASE_WAITING_LOCALIZATION = "waiting_localization"
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


def _proportional_command(error, gain, maximum):
    if abs(error) < 1e-12:
        return 0.0
    return math.copysign(min(maximum, abs(error) * gain), error)


def _zero_command():
    return {"linearX": 0.0, "linearY": 0.0, "angularZ": 0.0}


class NavigationManager:
    def __init__(self, reader=None, publisher=None):
        self._reader = reader
        self._publisher = publisher or publish_chassis_velocity
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread = None
        self._state = self._base_state()

    def _arrival_state(self):
        return {
            "stableSince": None,
            "stableElapsedSec": 0.0,
            "stableRequiredSec": DEFAULT_ARRIVAL_STABLE_SEC,
            "positionWithinTolerance": False,
            "positionWithinHoldBand": False,
            "yawWithinTolerance": False,
            "yawWithinHoldBand": False,
        }

    def _lateral_control_state(self):
        return {
            "active": False,
            "deadbandM": DEFAULT_LATERAL_DEADBAND_M,
            "enterThresholdM": DEFAULT_LATERAL_ENTER_THRESHOLD_M,
        }

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
            "arrival": self._arrival_state(),
            "lateralControl": self._lateral_control_state(),
            "command": _zero_command(),
            "startedAt": None,
            "updatedAt": None,
            "completedAt": None,
            "stoppedAt": None,
            "failedAt": None,
            "localizationWaitStartedAt": None,
            "lastLocalizationError": "",
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
            "arrivalStableSec": DEFAULT_ARRIVAL_STABLE_SEC,
            "nearTargetRadiusM": max(DEFAULT_NEAR_TARGET_RADIUS_M, DEFAULT_POSITION_TOLERANCE_M * NEAR_TARGET_RADIUS_FACTOR),
            "lateralDeadbandM": DEFAULT_LATERAL_DEADBAND_M,
            "lateralEnterThresholdM": DEFAULT_LATERAL_ENTER_THRESHOLD_M,
            "lateralDominantLinearDeadbandMps": DEFAULT_LATERAL_DOMINANT_LINEAR_DEADBAND_MPS,
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

        now_text = time.strftime("%H:%M:%S")
        pose, error = self._read_current_pose(params, wait_sec=0.2)
        if pose is None:
            translation_yaw = None
            initial_phase = PHASE_WAITING_LOCALIZATION
            current_pose = None
            wait_started = now_text
            localization_error = error or "Localization pose is unavailable."
            detail = f"Waiting for localization pose: {localization_error}"
        else:
            translation_yaw = pose["yawRad"]
            initial_phase = PHASE_LATERAL_TRANSLATE if target["mode"] == "lateral" else PHASE_OMNI_TRANSLATE
            current_pose = _pose_to_status(pose)
            wait_started = None
            localization_error = ""
            detail = "Navigation started."
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
                    "translationYawDeg": None if translation_yaw is None else math.degrees(translation_yaw),
                    "currentPose": current_pose,
                    "startedAt": now_text,
                    "updatedAt": now_text,
                    "localizationWaitStartedAt": wait_started,
                    "lastLocalizationError": localization_error,
                    "detail": detail,
                }
            )

        thread = threading.Thread(target=self._run_loop, name="robot_station_navigation", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return _result(True, "NAV-STARTED", detail, **self._state_payload())

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
                        "command": _zero_command(),
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
        position_tolerance = _optional_positive_number(
            payload,
            ("positionToleranceM", "position_tolerance_m"),
            "positionToleranceM",
            DEFAULT_POSITION_TOLERANCE_M,
            MIN_POSITION_TOLERANCE_M,
            1.0,
        )
        lateral_deadband = _optional_positive_number(
            payload,
            ("lateralDeadbandM", "lateral_deadband_m"),
            "lateralDeadbandM",
            DEFAULT_LATERAL_DEADBAND_M,
            0.0,
            1.0,
        )
        lateral_enter_threshold = _optional_positive_number(
            payload,
            ("lateralEnterThresholdM", "lateral_enter_threshold_m"),
            "lateralEnterThresholdM",
            max(DEFAULT_LATERAL_ENTER_THRESHOLD_M, lateral_deadband),
            lateral_deadband,
            1.0,
        )
        near_target_radius = _optional_positive_number(
            payload,
            ("nearTargetRadiusM", "near_target_radius_m"),
            "nearTargetRadiusM",
            max(DEFAULT_NEAR_TARGET_RADIUS_M, position_tolerance * NEAR_TARGET_RADIUS_FACTOR),
            position_tolerance,
            2.0,
        )
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
            "positionToleranceM": position_tolerance,
            "yawToleranceDeg": yaw_tolerance_deg,
            "yawToleranceRad": math.radians(yaw_tolerance_deg),
            "arrivalStableSec": _optional_positive_number(
                payload,
                ("arrivalStableSec", "arrival_stable_sec"),
                "arrivalStableSec",
                DEFAULT_ARRIVAL_STABLE_SEC,
                0.0,
                5.0,
            ),
            "nearTargetRadiusM": near_target_radius,
            "lateralDeadbandM": lateral_deadband,
            "lateralEnterThresholdM": lateral_enter_threshold,
            "lateralDominantLinearDeadbandMps": _optional_positive_number(
                payload,
                ("lateralDominantLinearDeadbandMps", "lateral_dominant_linear_deadband_mps"),
                "lateralDominantLinearDeadbandMps",
                DEFAULT_LATERAL_DOMINANT_LINEAR_DEADBAND_MPS,
                0.0,
                0.2,
            ),
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
                    if not self._wait_for_localization(error):
                        return
                    time.sleep(1.0 / params["controlRateHz"])
                    continue

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
                            "translationYawRad": state.get("translationYawRad"),
                            "translationYawDeg": state.get("translationYawDeg"),
                            "currentPose": _pose_to_status(pose),
                            "errors": errors,
                            "arrival": dict(state.get("arrival") or self._arrival_state()),
                            "lateralControl": dict(state.get("lateralControl") or self._lateral_control_state()),
                            "command": command,
                            "updatedAt": now_text,
                            "detail": f"Navigation phase: {next_phase}.",
                            "localizationWaitStartedAt": None,
                            "lastLocalizationError": "",
                            "lastPublish": publish_result,
                        }
                    )
                time.sleep(1.0 / params["controlRateHz"])
        finally:
            self._publish_stop()

    def _update_arrival_state(self, state, errors, params, position_enter, position_hold, yaw_enter, yaw_hold):
        stable_required = params.get("arrivalStableSec", DEFAULT_ARRIVAL_STABLE_SEC)
        arrival = dict(state.get("arrival") or self._arrival_state())
        stable_since = arrival.get("stableSince")
        now = time.monotonic()

        if stable_required <= 0.0:
            stable_since = now if position_enter and yaw_enter else None
            stable_elapsed = 0.0
            ready = bool(position_enter and yaw_enter)
        else:
            if stable_since is None:
                stable_since = now if position_hold and yaw_enter else None
            elif not (position_hold and yaw_hold):
                stable_since = None

            stable_elapsed = 0.0 if stable_since is None else max(0.0, now - stable_since)
            ready = stable_since is not None and stable_elapsed >= stable_required

        arrival.update(
            {
                "stableSince": stable_since,
                "stableElapsedSec": stable_elapsed,
                "stableRequiredSec": stable_required,
                "positionWithinTolerance": bool(position_enter),
                "positionWithinHoldBand": bool(position_hold),
                "yawWithinTolerance": bool(yaw_enter),
                "yawWithinHoldBand": bool(yaw_hold),
            }
        )
        state["arrival"] = arrival
        errors.update(
            {
                "arrivalStableSince": stable_since,
                "arrivalStableElapsedSec": stable_elapsed,
                "arrivalStableRequiredSec": stable_required,
                "positionWithinTolerance": bool(position_enter),
                "positionWithinHoldBand": bool(position_hold),
                "yawWithinTolerance": bool(yaw_enter),
                "yawWithinHoldBand": bool(yaw_hold),
            }
        )
        return ready

    def _reset_arrival_state(self, state, errors, params):
        arrival = self._arrival_state()
        arrival["stableRequiredSec"] = params.get("arrivalStableSec", DEFAULT_ARRIVAL_STABLE_SEC)
        state["arrival"] = arrival
        errors.update(
            {
                "arrivalStableSince": None,
                "arrivalStableElapsedSec": 0.0,
                "arrivalStableRequiredSec": arrival["stableRequiredSec"],
                "positionWithinTolerance": False,
                "positionWithinHoldBand": False,
                "yawWithinTolerance": False,
                "yawWithinHoldBand": False,
            }
        )

    def _omni_vector_command(self, errors, params):
        linear = _proportional_command(
            errors["bodyX"],
            params["positionGain"],
            params["maxLinearMps"],
        )
        lateral = _proportional_command(
            errors["bodyY"],
            params["positionGain"],
            params["maxLateralMps"],
        )
        command_norm = math.hypot(linear, lateral)
        minimum_norm = min(MIN_LINEAR_COMMAND_MPS, MIN_LATERAL_COMMAND_MPS)
        if 0.0 < command_norm < minimum_norm:
            scale = minimum_norm / command_norm
            linear = max(-params["maxLinearMps"], min(params["maxLinearMps"], linear * scale))
            lateral = max(-params["maxLateralMps"], min(params["maxLateralMps"], lateral * scale))
        linear_deadband = params.get("lateralDominantLinearDeadbandMps", DEFAULT_LATERAL_DOMINANT_LINEAR_DEADBAND_MPS)
        if abs(lateral) >= linear_deadband and abs(linear) <= linear_deadband:
            linear = 0.0
        return {"linearX": linear, "linearY": lateral, "angularZ": 0.0}

    def _near_target_omni_command(self, state, errors, params):
        abs_x = abs(errors["bodyX"])
        abs_y = abs(errors["bodyY"])
        tolerance = params["positionToleranceM"]
        deadband = params["lateralDeadbandM"]
        enter_threshold = params["lateralEnterThresholdM"]
        lateral_control = dict(state.get("lateralControl") or self._lateral_control_state())
        lateral_active = bool(lateral_control.get("active"))

        if abs_y <= deadband:
            lateral_active = False
        elif abs_y >= enter_threshold:
            lateral_active = True

        can_finish_by_x = abs_y <= tolerance and abs_x > 1e-12
        can_finish_by_y = abs_x <= tolerance and abs_y > tolerance
        if lateral_active and abs_y > deadband:
            axis = "y"
        elif can_finish_by_x:
            axis = "x"
        elif can_finish_by_y:
            axis = "y"
        elif abs_x >= abs_y and abs_x > 1e-12:
            axis = "x"
        elif abs_y > 1e-12:
            axis = "y"
        else:
            axis = None

        lateral_active = axis == "y" and abs_y > deadband
        lateral_control.update(
            {
                "active": lateral_active,
                "deadbandM": deadband,
                "enterThresholdM": enter_threshold,
            }
        )
        state["lateralControl"] = lateral_control
        errors["nearTarget"] = True
        errors["lateralControlActive"] = lateral_active

        if axis == "y":
            lateral = _sign_preserving_command(
                errors["bodyY"],
                params["positionGain"],
                MIN_LATERAL_COMMAND_MPS,
                params["maxLateralMps"],
            )
            return {"linearX": 0.0, "linearY": lateral, "angularZ": 0.0}
        if axis == "x":
            linear = _sign_preserving_command(
                errors["bodyX"],
                params["positionGain"],
                MIN_LINEAR_COMMAND_MPS,
                params["maxLinearMps"],
            )
            return {"linearX": linear, "linearY": 0.0, "angularZ": 0.0}
        return _zero_command()

    def _next_command(self, state, target, params, pose):
        dx = target["x"] - pose["x"]
        dy = target["y"] - pose["y"]
        reference_yaw = pose["yawRad"] if target["mode"] == "omni" else state.get("translationYawRad")
        if reference_yaw is None:
            reference_yaw = pose["yawRad"]
        state["translationYawRad"] = reference_yaw
        state["translationYawDeg"] = math.degrees(reference_yaw)
        projected = _project_to_reference_frame(dx, dy, reference_yaw)
        distance = math.hypot(dx, dy)
        yaw_error = _normalize_angle(target["yawRad"] - pose["yawRad"])
        errors = {
            **projected,
            "distance": distance,
            "yawRad": yaw_error,
            "yawDeg": math.degrees(yaw_error),
            "nearTarget": distance <= params.get("nearTargetRadiusM", DEFAULT_NEAR_TARGET_RADIUS_M),
            "lateralControlActive": bool((state.get("lateralControl") or {}).get("active")),
        }

        phase = state.get("phase")
        position_tolerance = params["positionToleranceM"]
        yaw_tolerance = params["yawToleranceRad"]
        position_hold_tolerance = position_tolerance * ARRIVAL_POSITION_HOLD_FACTOR
        yaw_hold_tolerance = yaw_tolerance * ARRIVAL_YAW_HOLD_FACTOR
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
                self._reset_arrival_state(state, errors, params)
                phase = PHASE_LATERAL_TRANSLATE if target["mode"] == "lateral" and abs(errors["bodyY"]) > position_tolerance else (
                    PHASE_FORWARD_TRANSLATE if target["mode"] == "lateral" else PHASE_OMNI_TRANSLATE
                )
            else:
                ready = self._update_arrival_state(
                    state,
                    errors,
                    params,
                    distance <= position_tolerance,
                    distance <= position_hold_tolerance,
                    abs(yaw_error) <= yaw_tolerance,
                    abs(yaw_error) <= yaw_hold_tolerance,
                )
                if ready:
                    return _zero_command(), PHASE_COMPLETED, errors, True
                if abs(yaw_error) <= yaw_tolerance:
                    if distance > position_hold_tolerance:
                        self._reset_arrival_state(state, errors, params)
                        phase = PHASE_LATERAL_TRANSLATE if target["mode"] == "lateral" and abs(errors["bodyY"]) > position_tolerance else (
                            PHASE_FORWARD_TRANSLATE if target["mode"] == "lateral" else PHASE_OMNI_TRANSLATE
                        )
                    else:
                        return _zero_command(), PHASE_ROTATE, errors, False

        if phase == PHASE_LATERAL_TRANSLATE:
            self._reset_arrival_state(state, errors, params)
            lateral = _sign_preserving_command(
                errors["bodyY"],
                params["positionGain"],
                MIN_LATERAL_COMMAND_MPS,
                params["maxLateralMps"],
            )
            return {"linearX": 0.0, "linearY": lateral, "angularZ": 0.0}, phase, errors, False

        if phase == PHASE_FORWARD_TRANSLATE:
            self._reset_arrival_state(state, errors, params)
            linear = _sign_preserving_command(
                errors["bodyX"],
                params["positionGain"],
                MIN_LINEAR_COMMAND_MPS,
                params["maxLinearMps"],
            )
            return {"linearX": linear, "linearY": 0.0, "angularZ": 0.0}, phase, errors, False

        if phase == PHASE_OMNI_TRANSLATE:
            self._reset_arrival_state(state, errors, params)
            if errors["nearTarget"]:
                return self._near_target_omni_command(state, errors, params), phase, errors, False
            state["lateralControl"] = self._lateral_control_state()
            errors["lateralControlActive"] = False
            return self._omni_vector_command(errors, params), phase, errors, False

        angular = _sign_preserving_command(
            yaw_error,
            params["yawGain"],
            MIN_ANGULAR_COMMAND_RAD_S,
            params["maxAngularRadS"],
        )
        return {"linearX": 0.0, "linearY": 0.0, "angularZ": angular}, PHASE_ROTATE, errors, False

    def _publish_stop(self):
        return self._publisher(_zero_command())

    def _wait_for_localization(self, error):
        detail = error or "Localization pose is unavailable."
        publish_result = self._publish_stop()
        if not publish_result.get("ok"):
            self._fail(publish_result.get("detail", "Failed to publish chassis stop command."))
            return False
        with self._lock:
            if not self._state.get("running"):
                return False
            now_text = time.strftime("%H:%M:%S")
            wait_started = self._state.get("localizationWaitStartedAt") or now_text
            self._state.update(
                {
                    "status": "running",
                    "phase": PHASE_WAITING_LOCALIZATION,
                    "running": True,
                    "command": _zero_command(),
                    "updatedAt": now_text,
                    "localizationWaitStartedAt": wait_started,
                    "lastLocalizationError": detail,
                    "detail": f"Waiting for localization pose: {detail}",
                    "lastPublish": publish_result,
                }
            )
        return True

    def _arrival_from_errors(self, errors):
        arrival = self._arrival_state()
        if not isinstance(errors, dict):
            return arrival
        arrival.update(
            {
                "stableSince": errors.get("arrivalStableSince"),
                "stableElapsedSec": errors.get("arrivalStableElapsedSec", 0.0),
                "stableRequiredSec": errors.get("arrivalStableRequiredSec", DEFAULT_ARRIVAL_STABLE_SEC),
                "positionWithinTolerance": bool(errors.get("positionWithinTolerance")),
                "positionWithinHoldBand": bool(errors.get("positionWithinHoldBand")),
                "yawWithinTolerance": bool(errors.get("yawWithinTolerance")),
                "yawWithinHoldBand": bool(errors.get("yawWithinHoldBand")),
            }
        )
        return arrival

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
                    "arrival": self._arrival_from_errors(errors),
                    "command": _zero_command(),
                    "completedAt": now_text,
                    "updatedAt": now_text,
                    "localizationWaitStartedAt": None,
                    "lastLocalizationError": "",
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
                    "command": _zero_command(),
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
