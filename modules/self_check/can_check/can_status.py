import re
import time

from modules.drivers.can.can_activate import ALLOWED_SOURCE_INTERFACES, activate_can
from modules.drivers.can.can_interface import (
    DEFAULT_BITRATE,
    DEFAULT_CHASSIS_CAN_TARGETS,
    DEFAULT_PIPER_CAN_TARGETS,
    inspect_all_can,
    load_chassis_can_config,
    load_piper_can_config,
)


def _configured_targets(config, preferred_targets):
    ports = config.get("ports", {})
    targets = [target for target in preferred_targets if target in ports]
    targets.extend(target for target in ports if target not in targets)
    return targets


def _combined_can_config(expected_bitrate=None):
    piper_config = load_piper_can_config()
    chassis_config = load_chassis_can_config()
    groups = [
        (piper_config, DEFAULT_PIPER_CAN_TARGETS, int(expected_bitrate or piper_config.get("bitrate") or DEFAULT_BITRATE)),
        (chassis_config, DEFAULT_CHASSIS_CAN_TARGETS, int(chassis_config.get("bitrate"))),
    ]
    targets = []
    ports = {}
    target_bitrates = {}
    for config, preferred_targets, bitrate in groups:
        for target in _configured_targets(config, preferred_targets):
            if target not in targets:
                targets.append(target)
            ports[target] = config.get("ports", {}).get(target, "")
            target_bitrates[target] = bitrate
    return {
        "expectedBitrate": int(expected_bitrate or piper_config.get("bitrate") or DEFAULT_BITRATE),
        "targets": targets,
        "ports": ports,
        "targetBitrates": target_bitrates,
    }


def _metric(status, value, percent):
    level = "ok"
    if status == "警告":
        level = "warn"
    if status == "错误":
        level = "danger"
    return {
        "label": "CAN",
        "value": value,
        "percent": percent,
        "level": level,
    }


def _result(status, code, detail, advice, metric, inspection, activation=None):
    supported_actions = ["retry"] if status == "正常" else ["activate", "retry"]
    return {
        "name": "CAN 接口",
        "status": status,
        "source": "系统",
        "code": code,
        "advice": advice,
        "detail": detail,
        "checkedAt": time.strftime("%H:%M:%S"),
        "metric": metric,
        "can": inspection,
        "activation": activation,
        "supportedActions": supported_actions,
        "requiresSudo": status != "正常",
    }


def _target_state(inspection, target):
    return inspection.get("details", {}).get(target, {})


def _all_targets_exist(inspection, targets):
    interfaces = set(inspection.get("interfaces", []))
    return all(target in interfaces for target in targets)


def _ready_targets(inspection, targets, target_bitrates):
    ready = []
    for target in targets:
        state = _target_state(inspection, target)
        if state.get("isUp") and state.get("bitrate") == target_bitrates.get(target):
            ready.append(target)
    return ready


def _bad_can_states(inspection, targets):
    bad = []
    for target in targets:
        can_state = _target_state(inspection, target).get("canState")
        if can_state in {"BUS-OFF", "ERROR-PASSIVE"}:
            bad.append(f"{target}:{can_state}")
    return bad


def _source_sort_key(interface):
    match = re.fullmatch(r"can(\d+)", interface)
    return int(match.group(1)) if match else 9999


def _raw_source_interfaces(inspection):
    return sorted(
        [
            interface
            for interface in inspection.get("interfaces", [])
            if re.fullmatch(r"can\d+", interface) and interface in ALLOWED_SOURCE_INTERFACES
        ],
        key=_source_sort_key,
    )


def _allowed_source_label():
    return "/".join(sorted(ALLOWED_SOURCE_INTERFACES, key=_source_sort_key)) or "未配置"


def _target_detail(inspection, targets, target_bitrates):
    parts = []
    for target in targets:
        state = _target_state(inspection, target)
        if not state:
            parts.append(f"{target}=缺失")
            continue
        up = "UP" if state.get("isUp") else "DOWN"
        current_bitrate = state.get("bitrate") or "未知"
        expected_bitrate = target_bitrates.get(target)
        can_state = state.get("canState") or "UNKNOWN"
        bus_info = state.get("busInfo")
        extra = f", bus-info {bus_info}" if bus_info else ""
        match = "匹配" if current_bitrate == expected_bitrate else f"不匹配, 应为 {expected_bitrate}"
        parts.append(f"{target}={up}, bitrate {current_bitrate}({match}), {can_state}{extra}")
    return "；".join(parts)


def _format_target_rates(targets, target_bitrates):
    return ", ".join(f"{target}:{target_bitrates.get(target)}" for target in targets)


def _raw_can_advice(inspection):
    sources = _raw_source_interfaces(inspection)
    if sources:
        detail = ", ".join(
            f"{source}({inspection.get('details', {}).get(source, {}).get('busInfo') or 'bus-info 未知'})"
            for source in sources
        )
        return f"检测到原始接口 {detail}，自检会按 USB bus-info 激活并重命名为 can_left/can_right/can_chassis。"
    current = ", ".join(inspection.get("interfaces", [])) or "无"
    return f"未发现可激活的原始接口 {_allowed_source_label()}；当前 CAN 接口：{current}。请检查 USB-CAN 连接。"


def check_can_interface(expected_bitrate=None, auto_activate=True):
    config = _combined_can_config(expected_bitrate=expected_bitrate)
    expected_bitrate = config["expectedBitrate"]
    targets = config["targets"]
    target_bitrates = config["targetBitrates"]
    inspection = inspect_all_can(expected_bitrate=expected_bitrate, expected_bitrates=target_bitrates)
    inspection["requestedTargets"] = targets
    inspection["ports"] = config.get("ports", {})
    inspection["expectedBitrates"] = target_bitrates

    if inspection.get("error"):
        return _result(
            "错误",
            "CAN-I-ERROR",
            f"读取 CAN 接口状态失败：{inspection['error']}",
            "请确认系统安装 iproute2，并在终端执行 ip -details link show type can 查看状态。",
            _metric("错误", "读取失败", 8),
            inspection,
        )

    if not inspection.get("tools", {}).get("ip"):
        return _result(
            "错误",
            "CAN-I-IP",
            "系统中找不到 ip 命令，无法检查 CAN 网络接口。",
            "请安装 iproute2 后重新执行自检。",
            _metric("错误", "无 ip", 8),
            inspection,
        )

    if _all_targets_exist(inspection, targets):
        bad_states = _bad_can_states(inspection, targets)
        if bad_states:
            return _result(
                "错误",
                "CAN-I-BUS",
                f"CAN 接口已命名，但 CAN 状态异常：{', '.join(bad_states)}。",
                "请检查 CAN 线缆、终端电阻、设备供电和 bitrate，修复后重新激活 CAN。",
                _metric("错误", "BUS 异常", 25),
                inspection,
            )

        ready = _ready_targets(inspection, targets, target_bitrates)
        if len(ready) == len(targets):
            detail = f"CAN 已就绪：{_target_detail(inspection, targets, target_bitrates)}。"
            return _result(
                "正常",
                "CAN-I-OK",
                detail,
                "can_left/can_right/can_chassis 均可用，可以继续执行机械臂反馈检查或启动底盘。",
                _metric("正常", "三路 UP", 94),
                inspection,
            )

        if auto_activate:
            activation = activate_can(bitrate=expected_bitrate)
            refreshed = inspect_all_can(expected_bitrate=expected_bitrate, expected_bitrates=target_bitrates)
            refreshed["requestedTargets"] = targets
            refreshed["ports"] = config.get("ports", {})
            refreshed["expectedBitrates"] = target_bitrates
            if len(_ready_targets(refreshed, targets, target_bitrates)) == len(targets):
                detail = f"CAN 已自动修复：{_target_detail(refreshed, targets, target_bitrates)}。"
                return _result(
                    "正常",
                    "CAN-I-ACTIVATED",
                    detail,
                    "can_left/can_right/can_chassis 已可用，可以继续执行机械臂反馈检查或启动底盘。",
                    _metric("正常", "已修复", 92),
                    refreshed,
                    activation=activation,
                )
            refreshed["activation"] = activation
            inspection = refreshed

        detail = f"CAN 接口名称存在，但状态/bitrate 未满足预期：{_target_detail(inspection, targets, target_bitrates)}。"
        return _result(
            "错误",
            "CAN-I-BITRATE",
            detail,
            f"请点击激活 CAN，或手动按预期 bitrate 设置并 UP：{_format_target_rates(targets, target_bitrates)}。",
            _metric("错误", "配置异常", 35),
            inspection,
        )

    missing = [target for target in targets if target not in inspection.get("interfaces", [])]
    if auto_activate and _raw_source_interfaces(inspection):
        activation = activate_can(bitrate=expected_bitrate)
        refreshed = inspect_all_can(expected_bitrate=expected_bitrate, expected_bitrates=target_bitrates)
        refreshed["requestedTargets"] = targets
        refreshed["ports"] = config.get("ports", {})
        refreshed["expectedBitrates"] = target_bitrates
        if len(_ready_targets(refreshed, targets, target_bitrates)) == len(targets):
            detail = f"CAN 已自动激活：{_target_detail(refreshed, targets, target_bitrates)}。"
            return _result(
                "正常",
                "CAN-I-ACTIVATED",
                detail,
                "can_left/can_right/can_chassis 已可用，可以继续执行机械臂反馈检查或启动底盘。",
                _metric("正常", "已激活", 92),
                refreshed,
                activation=activation,
            )
        refreshed["activation"] = activation
        inspection = refreshed

    if not inspection.get("interfaces"):
        return _result(
            "错误",
            "CAN-I-MISSING",
            "系统未发现 CAN 接口。",
            "请检查 Piper 和底盘 USB-CAN 是否连接，确认 gs_usb 驱动已加载，再重新执行自检。",
            _metric("错误", "未发现", 8),
            inspection,
        )

    raw_advice = _raw_can_advice(inspection)
    return _result(
        "错误",
        "CAN-I-INCOMPLETE",
        f"CAN 未完整就绪，缺少：{', '.join(missing)}。{_target_detail(inspection, targets, target_bitrates)}。",
        raw_advice,
        _metric("错误", "缺少接口", 20),
        inspection,
    )
