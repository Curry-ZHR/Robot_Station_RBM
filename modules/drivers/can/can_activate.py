import os
import re
import shutil
import subprocess

from modules.drivers.can.can_interface import (
    DEFAULT_BITRATE,
    DEFAULT_CHASSIS_CAN_TARGETS,
    DEFAULT_PIPER_CAN_TARGETS,
    inspect_all_can,
    load_chassis_can_config,
    load_piper_can_config,
)


ALLOWED_SOURCE_INTERFACES = {
    item.strip()
    for item in os.environ.get("ROBOT_STATION_CAN_ALLOWED_SOURCES", "can0,can1,can2").split(",")
    if item.strip()
}
ALLOWED_TARGET_INTERFACES = {
    item.strip()
    for item in os.environ.get(
        "ROBOT_STATION_CAN_ALLOWED_TARGETS",
        ",".join(DEFAULT_PIPER_CAN_TARGETS + DEFAULT_CHASSIS_CAN_TARGETS),
    ).split(",")
    if item.strip()
}
ALLOWED_BITRATES = {
    int(item)
    for item in os.environ.get("ROBOT_STATION_CAN_ALLOWED_BITRATES", "1000000,500000").split(",")
    if item.strip()
}
SUDOERS_SETUP_COMMAND = "bash scripts/install_can_sudoers.sh"


def _result(ok, code, detail, advice, commands=None, inspection=None, raw="", activated=None):
    return {
        "ok": ok,
        "code": code,
        "detail": detail,
        "advice": advice,
        "commands": commands or [],
        "inspection": inspection,
        "raw": raw,
        "activated": activated,
    }


def _valid_source_name(interface):
    return bool(re.fullmatch(r"can\d+", interface)) and interface in ALLOWED_SOURCE_INTERFACES


def _valid_target_name(interface):
    return bool(re.fullmatch(r"can_[A-Za-z0-9_]+", interface)) and interface in ALLOWED_TARGET_INTERFACES


def _source_sort_key(interface):
    match = re.fullmatch(r"can(\d+)", interface)
    return int(match.group(1)) if match else 9999


def _allowed_source_label():
    return "/".join(sorted(ALLOWED_SOURCE_INTERFACES, key=_source_sort_key)) or "未配置"


def _source_interfaces(inspection):
    return sorted(
        [
            interface
            for interface in inspection.get("interfaces", [])
            if _valid_source_name(interface)
        ],
        key=_source_sort_key,
    )


def _sudo_ip_command(args):
    ip = shutil.which("ip")
    sudo = shutil.which("sudo")
    if not ip:
        return None, "ip command not found"
    if not sudo:
        return None, "sudo command not found"
    return [sudo, "-n", ip, *args], ""


def _sudo_failure_advice():
    return (
        "网页后端使用 sudo -n，不能弹出密码。请在终端进入 robot_station 后执行 "
        f"`{SUDOERS_SETUP_COMMAND}` 配置一次 CAN 激活免密白名单，然后重新点击 CAN。"
    )


def _run(command, timeout_sec=4.0):
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return False, f"{' '.join(command)} timed out after {timeout_sec:.1f}s"
    except OSError as exc:
        return False, str(exc)
    output = (completed.stdout or completed.stderr or "").strip()
    return completed.returncode == 0, output


def _configured_targets(config, preferred_targets):
    ports = config.get("ports", {})
    targets = [target for target in preferred_targets if target in ports]
    targets.extend(target for target in ports if target not in targets)
    return [target for target in targets if target in ALLOWED_TARGET_INTERFACES]


def _missing_targets(inspection, targets):
    interfaces = set(inspection.get("interfaces", []))
    return [target for target in targets if target not in interfaces]


def _ready_targets(inspection, targets, target_bitrates):
    details = inspection.get("details", {})
    ready = []
    for target in targets:
        info = details.get(target, {})
        if info.get("isUp") and info.get("bitrate") == target_bitrates.get(target):
            ready.append(target)
    return ready


def _target_for_source(source, source_info, config, missing_targets, requested_target=None):
    bus_info = source_info.get("busInfo")
    ports = config.get("ports", {})
    if requested_target:
        expected_bus = ports.get(requested_target)
        if not expected_bus or expected_bus == bus_info:
            return requested_target, ""
        if not bus_info:
            return "", f"无法读取 {source} 的 USB bus-info，不能安全重命名为 {requested_target}。"
        return "", f"{source} 的 USB bus-info 为 {bus_info}，不匹配 {requested_target} 配置的 {expected_bus}。"

    for target in missing_targets:
        if ports.get(target) == bus_info:
            return target, ""

    if not bus_info:
        return "", f"无法读取 {source} 的 USB bus-info，不能安全判断它对应哪个 CAN 目标。"

    expected = ", ".join(f"{target}={bus}" for target, bus in ports.items()) or "未配置"
    return "", f"{source} 的 USB bus-info 为 {bus_info}，但未匹配 CAN 配置：{expected}。"


def _source_target_pairs(inspection, config, missing_targets, requested_target=None):
    sources = _source_interfaces(inspection)
    if not sources:
        current = ", ".join(inspection.get("interfaces", [])) or "无"
        return [], (
            f"CAN 未完整就绪，且未发现可重命名的原始接口 {_allowed_source_label()}。"
            f"当前接口：{current}。"
        )

    ports = config.get("ports", {})
    effective_missing = list(missing_targets)
    if requested_target:
        effective_missing = [target for target in missing_targets if target == requested_target]
        if not effective_missing:
            return [], f"{requested_target} 已存在，拒绝重复重命名。"

    pairs = []
    errors = []
    used_targets = set()
    for source in sources:
        source_info = inspection.get("details", {}).get(source, {})
        target, target_error = _target_for_source(
            source,
            source_info,
            config,
            effective_missing,
            requested_target=requested_target,
        )
        if target_error:
            errors.append(target_error)
            continue
        if target not in effective_missing or target in used_targets:
            continue
        if ports.get(target) and source_info.get("busInfo") and ports[target] != source_info["busInfo"]:
            errors.append(f"{source} 的 USB bus-info 为 {source_info['busInfo']}，不匹配 {target} 配置的 {ports[target]}。")
            continue
        pairs.append((source, target))
        used_targets.add(target)

    if pairs:
        return pairs, ""

    expected = ", ".join(f"{target}={ports.get(target, '未配置')}" for target in effective_missing) or "无"
    source_detail = ", ".join(
        f"{source}={inspection.get('details', {}).get(source, {}).get('busInfo') or '未知'}"
        for source in sources
    )
    detail = "；".join(errors) if errors else f"原始接口 {source_detail} 未匹配缺失目标：{expected}。"
    return [], detail


def _activate_source_as_target(source, target, bitrate, inspection):
    command_specs = [
        ["link", "set", source, "down"],
        ["link", "set", source, "type", "can", "bitrate", str(int(bitrate))],
        ["link", "set", source, "name", target],
        ["link", "set", target, "up"],
    ]
    commands = []
    raw_outputs = []
    for spec in command_specs:
        command, error = _sudo_ip_command(spec)
        if error:
            return _result(
                False,
                "CAN-A-CMD",
                error,
                "请确认系统安装了 iproute2 和 sudo。",
                commands=commands,
                inspection=inspection,
            )
        commands.append(" ".join(command))
        ok, output = _run(command)
        raw_outputs.append(output)
        if not ok:
            return _result(
                False,
                "CAN-A-SUDO",
                output or f"执行 {' '.join(command)} 失败。",
                _sudo_failure_advice(),
                commands=commands,
                inspection=inspection,
                raw="\n".join(raw_outputs),
            )

    return _result(
        True,
        "CAN-A-RENAMED",
        f"{source} 已按 bitrate {int(bitrate)} 激活并重命名为 {target}。",
        "请重新执行 CAN 自检确认所有 CAN 目标是否都已就绪。",
        commands=commands,
        inspection=inspection,
        raw="\n".join(raw_outputs),
        activated={"source": source, "target": target, "bitrate": int(bitrate)},
    )


def _activate_existing_target(target, bitrate, inspection):
    command_specs = [
        ["link", "set", target, "down"],
        ["link", "set", target, "type", "can", "bitrate", str(int(bitrate))],
        ["link", "set", target, "up"],
    ]
    commands = []
    raw_outputs = []
    for spec in command_specs:
        command, error = _sudo_ip_command(spec)
        if error:
            return _result(
                False,
                "CAN-A-CMD",
                error,
                "请确认系统安装了 iproute2 和 sudo。",
                commands=commands,
                inspection=inspection,
            )
        commands.append(" ".join(command))
        ok, output = _run(command)
        raw_outputs.append(output)
        if not ok:
            return _result(
                False,
                "CAN-A-SUDO",
                output or f"执行 {' '.join(command)} 失败。",
                _sudo_failure_advice(),
                commands=commands,
                inspection=inspection,
                raw="\n".join(raw_outputs),
            )

    return _result(
        True,
        "CAN-A-RECONFIGURED",
        f"{target} 已按 bitrate {int(bitrate)} 重新配置并 UP。",
        "请重新执行 CAN 自检确认所有 CAN 目标是否都已就绪。",
        commands=commands,
        inspection=inspection,
        raw="\n".join(raw_outputs),
        activated={"source": target, "target": target, "bitrate": int(bitrate)},
    )


def _merge_activation_payload(activations):
    commands = []
    raw_outputs = []
    activated = []
    for activation in activations:
        commands.extend(activation.get("commands", []))
        if activation.get("raw"):
            raw_outputs.append(activation["raw"])
        if activation.get("activated"):
            activated.append(activation["activated"])
    return commands, "\n".join(raw_outputs), activated


def _activation_summary(activated):
    if not activated:
        return "未执行变更"
    return "；".join(
        f"{item['source']} -> {item['target']}"
        for item in activated
        if item.get("source") and item.get("target")
    )


def _activation_config(interface=None, bitrate=None):
    requested_target = interface if interface in ALLOWED_TARGET_INTERFACES else None
    if interface and not requested_target:
        return None, _result(
            False,
            "CAN-A-TARGET",
            f"目标接口 {interface} 不在允许列表中。",
            f"允许的目标接口：{', '.join(sorted(ALLOWED_TARGET_INTERFACES))}。",
        )

    piper_config = load_piper_can_config()
    chassis_config = load_chassis_can_config()
    groups = [
        ("机械臂", piper_config, DEFAULT_PIPER_CAN_TARGETS, int(bitrate or piper_config.get("bitrate") or DEFAULT_BITRATE)),
        ("底盘", chassis_config, DEFAULT_CHASSIS_CAN_TARGETS, int(chassis_config.get("bitrate"))),
    ]

    ports = {}
    target_bitrates = {}
    targets = []
    labels = []
    for label, config, preferred_targets, group_bitrate in groups:
        group_targets = _configured_targets(config, preferred_targets)
        if requested_target and requested_target not in group_targets:
            continue
        selected_targets = [target for target in group_targets if not requested_target or target == requested_target]
        if not selected_targets:
            continue
        labels.append(label)
        for target in selected_targets:
            if target not in targets:
                targets.append(target)
            ports[target] = config.get("ports", {}).get(target, "")
            target_bitrates[target] = int(group_bitrate)

    if requested_target and requested_target not in targets:
        return None, _result(
            False,
            "CAN-A-TARGET",
            f"目标接口 {requested_target} 不在 CAN 配置中。",
            "请检查 robot_station/config/can_ports.json。",
        )

    return {
        "ports": ports,
        "targets": targets,
        "target_bitrates": target_bitrates,
        "labels": labels,
        "requested_target": requested_target,
    }, None


def _format_target_rates(targets, target_bitrates):
    return ", ".join(f"{target}:{target_bitrates.get(target)}" for target in targets)


def activate_can(interface=None, bitrate=None):
    config, config_error = _activation_config(interface=interface, bitrate=bitrate)
    if config_error:
        return config_error

    targets = config["targets"]
    target_bitrates = config["target_bitrates"]
    requested_target = config["requested_target"]
    invalid_bitrates = {
        target: rate
        for target, rate in target_bitrates.items()
        if rate not in ALLOWED_BITRATES
    }
    if invalid_bitrates:
        detail = ", ".join(f"{target}={rate}" for target, rate in invalid_bitrates.items())
        return _result(
            False,
            "CAN-A-BITRATE",
            f"CAN bitrate 不在允许列表中：{detail}。",
            "机械臂应使用 1000000，底盘应使用 500000；请检查 robot_station/config/can_ports.json。",
        )

    if not targets:
        return _result(
            False,
            "CAN-A-CONFIG",
            "未配置 CAN 目标接口。",
            "请在 robot_station/config/can_ports.json 配置 can_left/can_right 和 can_chassis 的 USB bus-info。",
        )

    inspection = inspect_all_can(expected_bitrates=target_bitrates)
    if inspection.get("error"):
        return _result(
            False,
            "CAN-A-INSPECT",
            f"读取 CAN 接口失败：{inspection['error']}",
            "请确认系统安装 iproute2，并检查 USB-CAN 是否被系统识别。",
            inspection=inspection,
        )

    ready = _ready_targets(inspection, targets, target_bitrates)
    if len(ready) == len(targets):
        return _result(
            True,
            "CAN-A-NOOP",
            f"CAN 已就绪：{_format_target_rates(targets, target_bitrates)}。",
            "无需重新激活。",
            inspection=inspection,
        )

    missing = _missing_targets(inspection, targets)
    existing_not_ready = [
        target
        for target in targets
        if target in inspection.get("interfaces", []) and target not in ready
    ]
    source_pairs, source_error = _source_target_pairs(inspection, config, missing, requested_target=requested_target) if missing else ([], "")

    activations = []
    repair_targets = [
        target
        for target in existing_not_ready
        if not requested_target or target == requested_target
    ]
    for target in repair_targets:
        activation = _activate_existing_target(target, target_bitrates[target], inspection)
        if not activation.get("ok"):
            commands, raw, activated = _merge_activation_payload(activations)
            activation["commands"] = commands + activation.get("commands", [])
            activation["raw"] = "\n".join(item for item in [raw, activation.get("raw", "")] if item)
            activation["activated"] = activated
            return activation
        activations.append(activation)

    if repair_targets and not source_pairs:
        refreshed = inspect_all_can(expected_bitrates=target_bitrates)
        refreshed_ready = _ready_targets(refreshed, targets, target_bitrates)
        commands, raw, activated = _merge_activation_payload(activations)
        if len(refreshed_ready) == len(targets):
            activation.update(
                {
                    "code": "CAN-A-OK",
                    "detail": f"CAN 已全部就绪：{_format_target_rates(targets, target_bitrates)}。本次激活：{_activation_summary(activated)}。",
                    "advice": "可以继续执行机械臂反馈检查，或启动 Piper/Chassis 控制节点。",
                    "commands": commands,
                    "inspection": refreshed,
                    "raw": raw,
                    "activated": activated[0] if len(activated) == 1 else activated,
                }
            )
            return activation

        refreshed_missing = _missing_targets(refreshed, targets)
        remaining_not_ready = [
            target
            for target in targets
            if target in refreshed.get("interfaces", []) and target not in _ready_targets(refreshed, targets, target_bitrates)
        ]
        remaining = refreshed_missing + remaining_not_ready
        activation.update(
            {
                "code": "CAN-A-PARTIAL",
                "detail": f"已修复 {_activation_summary(activated)}，但 CAN 仍未完整就绪：{', '.join(remaining)}。",
                "advice": "请确认机械臂和底盘 USB-CAN 已连接，或再次执行自检/激活。",
                "commands": commands,
                "inspection": refreshed,
                "raw": raw,
                "activated": activated[0] if len(activated) == 1 else activated,
            }
        )
        return activation

    if missing and not source_pairs:
        return _result(
            False,
            "CAN-A-MISSING",
            source_error,
            f"请确认 USB-CAN 已插入；原始接口需为 {_allowed_source_label()}，并与 can_ports.json 的 USB bus-info 对应。",
            inspection=inspection,
        )

    for source, target in source_pairs:
        if not _valid_target_name(target):
            return _result(
                False,
                "CAN-A-TARGET",
                f"目标接口 {target} 不在允许列表中。",
                "CAN 自修复只允许重命名为 can_left/can_right/can_chassis。",
                inspection=inspection,
            )
        activation = _activate_source_as_target(source, target, target_bitrates[target], inspection)
        if not activation.get("ok"):
            commands, raw, activated = _merge_activation_payload(activations)
            activation["commands"] = commands + activation.get("commands", [])
            activation["raw"] = "\n".join(item for item in [raw, activation.get("raw", "")] if item)
            activation["activated"] = activated
            return activation
        activations.append(activation)

    refreshed = inspect_all_can(expected_bitrates=target_bitrates)
    refreshed_ready = _ready_targets(refreshed, targets, target_bitrates)
    commands, raw, activated = _merge_activation_payload(activations)
    if len(refreshed_ready) == len(targets):
        return _result(
            True,
            "CAN-A-OK",
            f"CAN 已全部就绪：{_format_target_rates(targets, target_bitrates)}。本次激活：{_activation_summary(activated)}。",
            "可以继续执行机械臂反馈检查，或启动 Piper/Chassis 控制节点。",
            commands=commands,
            inspection=refreshed,
            raw=raw,
            activated=activated[0] if len(activated) == 1 else activated,
        )

    refreshed_missing = _missing_targets(refreshed, targets)
    remaining_not_ready = [
        target
        for target in targets
        if target in refreshed.get("interfaces", []) and target not in refreshed_ready
    ]
    remaining = refreshed_missing + remaining_not_ready
    return _result(
        True,
        "CAN-A-PARTIAL",
        f"已激活 {_activation_summary(activated)}，但 CAN 仍未完整就绪：{', '.join(remaining) or '状态未刷新'}。",
        f"请确认机械臂和底盘 USB-CAN 已连接，系统原始接口应出现在 {_allowed_source_label()} 中，然后再次执行自检/激活。",
        commands=commands,
        inspection=refreshed,
        raw=raw,
        activated=activated[0] if len(activated) == 1 else activated,
    )
