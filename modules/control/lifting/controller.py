import json
import math
import os
import time
from pathlib import Path

from modules.ros_io import get_ros_runtime
from modules.ros_io.runtime import RosRuntimeError
from modules.ros_io.serializers import RosMessageImportError, import_service_class


ROOT_DIR = Path(__file__).resolve().parents[3]
SERVICE_TYPE = "lifting_msg_pkg/srv/LiftMotorSrv"
SERVICE_NAME = os.environ.get("LIFTING_SERVICE_NAME", "/LiftingMotorService")
DEFAULT_TIMEOUT_SEC = os.environ.get("LIFTING_SERVICE_TIMEOUT_SEC")
DEFAULT_WAIT_TIMEOUT_SEC = float(os.environ.get("LIFTING_SERVICE_WAIT_TIMEOUT_SEC", "0.3"))
DEFAULT_SPEED_MPS = 0.04
MIN_SPEED_MPS = 0.005
MAX_SPEED_MPS = 0.16


class LiftingControlValidationError(ValueError):
    pass


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def _as_payload_dict(payload):
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise LiftingControlValidationError("Payload must be a JSON object.")
    return payload


def _number(value, field):
    if isinstance(value, bool):
        raise LiftingControlValidationError(f"{field} must be a number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise LiftingControlValidationError(f"{field} must be a number.") from exc
    if not math.isfinite(parsed):
        raise LiftingControlValidationError(f"{field} must be a finite number.")
    return parsed


def _motor_id():
    return str(os.environ.get("LIFTING_MOTOR_ID", "1")).strip() or "1"


def _config_path():
    config_dir = (
        ROOT_DIR
        / "ros_packages"
        / "control"
        / "lifting"
        / "lifting_ctrl_ros2_pkg"
        / "lifting_ctrl_ros2_pkg"
        / "config"
    )
    motor_config = config_dir / f"{_motor_id()}_lifting_motor_config.json"
    if motor_config.exists():
        return motor_config
    return config_dir / "lifting_motor_config.json"


def _load_config():
    try:
        with _config_path().open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError):
        return {}


def _limits():
    config = _load_config()
    lower_mm = _number(os.environ.get("LIFTING_MIN_HEIGHT_MM", config.get("downLimitVal", 0)), "downLimitVal")
    upper_mm = _number(os.environ.get("LIFTING_MAX_HEIGHT_MM", config.get("upLimitVal", 800)), "upLimitVal")
    lower_m = min(lower_mm, upper_mm) / 1000.0
    upper_m = max(lower_mm, upper_mm) / 1000.0
    return {
        "minHeightM": lower_m,
        "maxHeightM": upper_m,
        "minHeightMm": int(round(lower_m * 1000)),
        "maxHeightMm": int(round(upper_m * 1000)),
        "configPath": str(_config_path()),
        "motorId": _motor_id(),
    }


def _service_timeout_sec():
    if DEFAULT_TIMEOUT_SEC:
        return _number(DEFAULT_TIMEOUT_SEC, "LIFTING_SERVICE_TIMEOUT_SEC")
    config = _load_config()
    configured_timeout = _number(config.get("responseTimeout", 70), "responseTimeout")
    return max(8.0, configured_timeout + 5.0)


def _clamp_height_m(height_m):
    limits = _limits()
    if height_m < limits["minHeightM"] or height_m > limits["maxHeightM"]:
        raise LiftingControlValidationError(
            f"heightM must be between {limits['minHeightM']:.3f} and {limits['maxHeightM']:.3f} m."
        )
    return height_m


def _height_from_payload(payload):
    payload = _as_payload_dict(payload)
    marker = object()
    value = payload.get("heightM", marker)
    if value is marker:
        value = payload.get("height", marker)
    if value is marker:
        value = payload.get("targetHeightM", marker)
    if value is marker:
        raise LiftingControlValidationError("heightM is required.")
    return _clamp_height_m(_number(value, "heightM"))


def _speed_from_payload(payload):
    payload = _as_payload_dict(payload)
    value = payload.get("speedMps", payload.get("speed", DEFAULT_SPEED_MPS))
    speed = abs(_number(value, "speedMps"))
    if speed < MIN_SPEED_MPS or speed > MAX_SPEED_MPS:
        raise LiftingControlValidationError(
            f"speedMps must be between {MIN_SPEED_MPS:.3f} and {MAX_SPEED_MPS:.3f} m/s."
        )
    return speed


def _state_detail(state):
    return {
        1: "指令执行成功。",
        -1: "指令未完成或目标尚未到达。",
        0: "指令已发送，但驱动未返回明确成功状态。",
        2: "下限位触发。",
        -2: "上限位触发。",
        -9: "电机离线或串口通信异常。",
        -12: "执行指令超时，驱动已进入急停模式。",
        -13: "初始化未完成且执行超时。",
        -14: "电机初始化失败。",
        -15: "清零位置时电机未停止。",
    }.get(int(state), f"驱动返回状态 {state}。")


def _state_ok(mode, state):
    if state == 1:
        return True
    if mode == -6 and state in (2, -2):
        return True
    if mode == -3 and state in (0, 1):
        return True
    return False


def _service_request(val, mode):
    service_class = import_service_class(SERVICE_TYPE)
    request = service_class.Request()
    request.val = int(round(val))
    request.mode = int(mode)
    return request


def _call_lifting_service(val, mode, action):
    try:
        request = _service_request(val, mode)
        response = get_ros_runtime().call_service(
            key="lifting_motor_service",
            service_type=SERVICE_TYPE,
            service_name=SERVICE_NAME,
            request=request,
            timeout_sec=_service_timeout_sec(),
            wait_timeout_sec=DEFAULT_WAIT_TIMEOUT_SEC,
        )
    except (RosRuntimeError, RosMessageImportError) as exc:
        return _result(False, "LIFT-C-UNAVAILABLE", str(exc), action=action, request={"val": int(round(val)), "mode": int(mode)})

    state = int(response.state)
    ok = _state_ok(request.mode, state)
    return _result(
        ok,
        "LIFT-C-OK" if ok else "LIFT-C-STATE",
        _state_detail(state),
        action=action,
        state=state,
        request={"val": request.val, "mode": request.mode},
        limits=_limits(),
        service=SERVICE_NAME,
        publishedAt=time.strftime("%H:%M:%S"),
    )


def initialize_lifting(payload=None):
    try:
        _as_payload_dict(payload)
    except LiftingControlValidationError as exc:
        return _result(False, "LIFT-C-PAYLOAD", str(exc))
    init_result = _call_lifting_service(0, 1, "init")
    if not init_result.get("ok"):
        return init_result

    zero_result = _call_lifting_service(0, -6, "zero_after_init")
    steps = [init_result, zero_result]
    return _result(
        zero_result.get("ok", False),
        "LIFT-C-OK" if zero_result.get("ok") else zero_result.get("code", "LIFT-C-STATE"),
        "初始化完成，已自动置零。" if zero_result.get("ok") else f"初始化完成，自动置零失败：{zero_result.get('detail', '')}",
        action="init",
        state=zero_result.get("state"),
        request=zero_result.get("request"),
        steps=steps,
        limits=_limits(),
        service=SERVICE_NAME,
        publishedAt=time.strftime("%H:%M:%S"),
    )


def move_lifting_to_height(payload):
    try:
        height_m = _height_from_payload(payload)
    except LiftingControlValidationError as exc:
        return _result(False, "LIFT-C-PAYLOAD", str(exc), limits=_limits())
    return _call_lifting_service(height_m * 1000.0, 0, "height")


def jog_lifting(payload):
    try:
        payload = _as_payload_dict(payload)
        direction = str(payload.get("direction", payload.get("action", ""))).strip().lower()
        if direction in {"hold", "stop", "0", "idle"}:
            return stop_lifting({})
        if direction not in {"up", "down"}:
            raise LiftingControlValidationError("direction must be up, down, hold, or stop.")
        speed_mps = _speed_from_payload(payload)
    except LiftingControlValidationError as exc:
        return _result(False, "LIFT-C-PAYLOAD", str(exc), limits=_limits())

    signed_speed_mm_s = speed_mps * 1000.0
    if direction == "down":
        signed_speed_mm_s = -signed_speed_mm_s
    return _call_lifting_service(signed_speed_mm_s, -4, "jog")


def stop_lifting(payload=None):
    try:
        _as_payload_dict(payload)
    except LiftingControlValidationError as exc:
        return _result(False, "LIFT-C-PAYLOAD", str(exc))
    return _call_lifting_service(0, -2, "stop")


def clear_lifting_error(payload=None):
    try:
        _as_payload_dict(payload)
    except LiftingControlValidationError as exc:
        return _result(False, "LIFT-C-PAYLOAD", str(exc))
    return _call_lifting_service(0, -3, "clear_error")


def zero_lifting_position(payload=None):
    try:
        _as_payload_dict(payload)
    except LiftingControlValidationError as exc:
        return _result(False, "LIFT-C-PAYLOAD", str(exc))
    return _call_lifting_service(0, -6, "zero")


def lifting_limits():
    return _result(True, "LIFT-C-LIMITS", "Lifting axis limits loaded.", limits=_limits())
