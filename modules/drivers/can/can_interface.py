import json
import os
import re
import shutil
import subprocess
from pathlib import Path


DEFAULT_CAN_NAME = os.environ.get("ROBOT_STATION_CAN_NAME", "can0")
DEFAULT_BITRATE = int(os.environ.get("ROBOT_STATION_CAN_BITRATE", "1000000"))
DEFAULT_PIPER_CAN_TARGETS = tuple(
    item.strip()
    for item in os.environ.get("ROBOT_STATION_PIPER_CAN_TARGETS", "can_left,can_right").split(",")
    if item.strip()
)
DEFAULT_CAN_CONFIG_PATH = Path(
    os.environ.get(
        "ROBOT_STATION_CAN_CONFIG",
        Path(__file__).resolve().parents[3] / "config" / "can_ports.json",
    )
)


def _run(command, timeout_sec=2.0):
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": f"{' '.join(command)} timed out after {timeout_sec:.1f}s",
        }
    except OSError as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _command_exists(name):
    return shutil.which(name) is not None


def _ip_path():
    return shutil.which("ip")


def _ethtool_path():
    return shutil.which("ethtool")


def _list_can_interfaces():
    ip = _ip_path()
    if not ip:
        return [], "ip command not found"
    result = _run([ip, "-br", "link", "show", "type", "can"])
    if not result["ok"]:
        return [], (result["stderr"] or result["stdout"]).strip()
    interfaces = []
    for line in result["stdout"].splitlines():
        parts = line.split()
        if parts:
            interfaces.append(parts[0].split("@")[0])
    return interfaces, ""


def list_can_interfaces():
    return _list_can_interfaces()


def _read_operstate(interface):
    path = Path("/sys/class/net") / interface / "operstate"
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _read_statistics(interface):
    stats_dir = Path("/sys/class/net") / interface / "statistics"
    keys = ("rx_packets", "tx_packets", "rx_errors", "tx_errors", "rx_dropped", "tx_dropped")
    stats = {}
    for key in keys:
        try:
            stats[key] = int((stats_dir / key).read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            stats[key] = None
    return stats


def _bus_info(interface):
    ethtool = _ethtool_path()
    if not ethtool:
        return ""
    result = _run([ethtool, "-i", interface])
    if not result["ok"]:
        return ""
    for line in result["stdout"].splitlines():
        if line.strip().startswith("bus-info:"):
            return line.split(":", 1)[1].strip()
    return ""


def get_bus_info(interface):
    return _bus_info(interface)


def _parse_flags(details):
    first_line = details.splitlines()[0] if details else ""
    match = re.search(r"<([^>]*)>", first_line)
    if not match:
        return []
    return [flag.strip() for flag in match.group(1).split(",") if flag.strip()]


def _parse_bitrate(details):
    match = re.search(r"\bbitrate\s+(\d+)", details)
    return int(match.group(1)) if match else None


def _parse_can_state(details):
    match = re.search(r"\bcan\s+state\s+([A-Z-]+)", details)
    return match.group(1) if match else ""


def _interface_details(interface):
    ip = _ip_path()
    if not ip:
        return None, "ip command not found"
    result = _run([ip, "-details", "link", "show", interface])
    if not result["ok"]:
        return None, (result["stderr"] or result["stdout"]).strip()
    details = result["stdout"]
    flags = _parse_flags(details)
    return {
        "details": details.strip(),
        "flags": flags,
        "isUp": "UP" in flags,
        "operstate": _read_operstate(interface),
        "bitrate": _parse_bitrate(details),
        "canState": _parse_can_state(details),
        "busInfo": _bus_info(interface),
        "statistics": _read_statistics(interface),
    }, ""


def interface_details(interface):
    return _interface_details(interface)


def inspect_all_can(expected_bitrate=DEFAULT_BITRATE):
    tools = {
        "ip": _command_exists("ip"),
        "ethtool": _command_exists("ethtool"),
        "candump": _command_exists("candump"),
    }
    interfaces, list_error = _list_can_interfaces()
    payload = {
        "expectedBitrate": expected_bitrate,
        "interfaces": interfaces,
        "tools": tools,
        "details": {},
    }
    if list_error:
        payload["error"] = list_error
        return payload

    for interface in interfaces:
        details, details_error = _interface_details(interface)
        if details_error:
            payload["details"][interface] = {"error": details_error}
            continue
        details["bitrateMatches"] = details["bitrate"] == expected_bitrate
        payload["details"][interface] = details
    return payload


def load_piper_can_config(config_path=DEFAULT_CAN_CONFIG_PATH):
    config = {
        "bitrate": DEFAULT_BITRATE,
        "ports": {},
    }
    try:
        raw = Path(config_path).read_text(encoding="utf-8")
    except OSError:
        return config

    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return config

    try:
        config["bitrate"] = int(loaded.get("bitrate", DEFAULT_BITRATE))
    except (TypeError, ValueError):
        config["bitrate"] = DEFAULT_BITRATE

    ports = loaded.get("ports", {})
    if isinstance(ports, dict):
        config["ports"] = {
            str(name): str(bus_info)
            for name, bus_info in ports.items()
            if str(name).strip() and str(bus_info).strip()
        }
    return config


def inspect_can(interface=DEFAULT_CAN_NAME, expected_bitrate=DEFAULT_BITRATE):
    tools = {
        "ip": _command_exists("ip"),
        "ethtool": _command_exists("ethtool"),
        "candump": _command_exists("candump"),
    }
    interfaces, list_error = _list_can_interfaces()
    if list_error:
        return {
            "interface": interface,
            "expectedBitrate": expected_bitrate,
            "exists": False,
            "interfaces": interfaces,
            "tools": tools,
            "error": list_error,
        }

    selected = interface if interface in interfaces else (interfaces[0] if len(interfaces) == 1 else interface)
    exists = selected in interfaces
    payload = {
        "interface": selected,
        "requestedInterface": interface,
        "expectedBitrate": expected_bitrate,
        "exists": exists,
        "interfaces": interfaces,
        "tools": tools,
        "requiresSelection": len(interfaces) > 1 and interface not in interfaces,
    }
    if not exists:
        return payload

    details, details_error = _interface_details(selected)
    if details_error:
        payload["error"] = details_error
        return payload

    payload.update(details)
    payload["bitrateMatches"] = details["bitrate"] == expected_bitrate
    return payload
