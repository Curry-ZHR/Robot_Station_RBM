import os
import signal
import shutil
import subprocess
import time


REPAIRABLE_ROS_DOMAIN_ID = "99"


def _ros_domain_id():
    return str(os.environ.get("ROS_DOMAIN_ID") or REPAIRABLE_ROS_DOMAIN_ID).strip()


def _metric(status, elapsed_ms=None, started=False):
    if status == "正常":
        if started:
            return {
                "label": "daemon",
                "value": "已启动",
                "percent": 92,
                "level": "ok",
            }
        if elapsed_ms is not None:
            percent = max(12, min(100, 100 - int(elapsed_ms / 12)))
            return {
                "label": "响应",
                "value": f"{elapsed_ms} ms",
                "percent": percent,
                "level": "ok",
            }
    if status == "警告":
        return {
            "label": "daemon",
            "value": "需确认",
            "percent": 42,
            "level": "warn",
        }
    return {
        "label": "daemon",
        "value": "失败",
        "percent": 8,
        "level": "danger",
    }


def _ros_context():
    return {
        "rosDistro": os.environ.get("ROS_DISTRO", ""),
        "rosDomainId": _ros_domain_id(),
        "rmwImplementation": os.environ.get("RMW_IMPLEMENTATION", ""),
    }


def _result(status, code, detail, advice, elapsed_ms=None, raw="", started=False):
    payload = {
        "name": "ROS2 daemon",
        "status": status,
        "source": "ROS",
        "code": code,
        "advice": advice,
        "detail": detail,
        "checkedAt": time.strftime("%H:%M:%S"),
        "metric": _metric(status, elapsed_ms, started=started),
        "raw": raw,
        "startedByRobotStation": started,
    }
    payload.update(_ros_context())
    return payload


def _ros2_path():
    return shutil.which("ros2")


def _ros_command_env():
    env = os.environ.copy()
    env["ROS_DOMAIN_ID"] = _ros_domain_id()
    return env


def _run_ros2(args, timeout_sec):
    ros2 = _ros2_path()
    if not ros2:
        return None, _result(
            "错误",
            "ROS2-D-CMD",
            "系统 PATH 中找不到 ros2 命令，无法检查 ROS2 daemon。",
            "请在启动控制台前 source ROS2 setup 文件，例如 source /opt/ros/<distro>/setup.bash。",
        )

    started = time.monotonic()
    try:
        completed = subprocess.run(
            [ros2, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=_ros_command_env(),
        )
    except subprocess.TimeoutExpired:
        return None, _result(
            "错误",
            "ROS2-D-TIMEOUT",
            f"ros2 {' '.join(args)} 在 {timeout_sec:.1f}s 内没有响应。",
            "请检查 ROS2 环境、DDS/RMW 配置和本机负载，然后重新自检。",
        )
    except OSError as exc:
        return None, _result(
            "错误",
            "ROS2-D-EXEC",
            f"执行 ros2 {' '.join(args)} 失败：{exc}",
            "请检查 ros2 命令权限和本机 ROS2 环境。",
        )

    elapsed_ms = int((time.monotonic() - started) * 1000)
    return completed, elapsed_ms


def _combined_output(completed):
    if completed is None:
        return ""
    return (completed.stdout or completed.stderr or "").strip()


def _daemon_running_from_output(output):
    lowered = output.lower()
    return "running" in lowered and "not running" not in lowered


def _daemon_not_running_from_output(output):
    lowered = output.lower()
    return "not running" in lowered or "not started" in lowered


def _daemon_pids_for_domain(domain_id):
    pids = []
    try:
        with os.scandir("/proc") as entries:
            proc_entries = list(entries)
    except OSError:
        return pids

    for entry in proc_entries:
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == os.getpid():
            continue
        try:
            with open(os.path.join(entry.path, "cmdline"), "rb") as proc_file:
                raw = proc_file.read()
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue
        parts = [
            part.decode("utf-8", errors="replace")
            for part in raw.split(b"\0")
            if part
        ]
        if not parts:
            continue
        text = " ".join(parts)
        if "ros2cli.daemon.daemonize" not in text:
            continue
        if "--name" not in parts or "ros2-daemon" not in parts:
            continue
        try:
            domain_index = parts.index("--ros-domain-id")
            if parts[domain_index + 1] != str(domain_id):
                continue
        except (ValueError, IndexError):
            continue
        pids.append(pid)
    return sorted(set(pids))


def _pid_exists(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _wait_for_pids_to_exit(pids, timeout_sec):
    deadline = time.monotonic() + timeout_sec
    remaining = set(pids)
    while remaining and time.monotonic() < deadline:
        remaining = {pid for pid in remaining if _pid_exists(pid)}
        if remaining:
            time.sleep(0.05)
    return sorted(remaining)


def _terminate_daemon_pids(pids, grace_sec=1.0):
    terminated = []
    forced = []
    errors = []

    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            terminated.append(pid)
        except ProcessLookupError:
            continue
        except OSError as exc:
            errors.append(f"pid {pid}: SIGTERM failed: {exc}")

    remaining = _wait_for_pids_to_exit(terminated, grace_sec)
    for pid in remaining:
        try:
            os.kill(pid, signal.SIGKILL)
            forced.append(pid)
        except ProcessLookupError:
            continue
        except OSError as exc:
            errors.append(f"pid {pid}: SIGKILL failed: {exc}")

    still_running = _wait_for_pids_to_exit(forced, 0.5)
    if still_running:
        errors.append(f"pid still running: {', '.join(str(pid) for pid in still_running)}")

    return {
        "terminated": terminated,
        "forced": forced,
        "errors": errors,
    }


def _should_repair_daemon(result):
    if _ros_domain_id() != REPAIRABLE_ROS_DOMAIN_ID:
        return False
    return result.get("code") in {
        "ROS2-D-TIMEOUT",
        "ROS2-D-STATUS",
        "ROS2-D-START",
        "ROS2-D-START-TIMEOUT",
    }


def check_ros_daemon(timeout_sec=2.5):
    completed, meta = _run_ros2(["daemon", "status"], timeout_sec)
    if completed is None:
        return meta

    output = _combined_output(completed)
    elapsed_ms = meta
    if completed.returncode == 0 and _daemon_running_from_output(output):
        return _result(
            "正常",
            "ROS2-D-OK",
            "ROS2 daemon 已运行，后端可以继续执行 ROS2 graph 查询。",
            "可以继续执行话题和设备检查。",
            elapsed_ms=elapsed_ms,
            raw=output,
        )

    if completed.returncode == 0 and _daemon_not_running_from_output(output):
        return _result(
            "警告",
            "ROS2-D-STOPPED",
            "ROS2 daemon 当前未运行。",
            "执行自检时可以自动启动 ROS2 daemon；如果仍失败，请检查 ROS2 环境。",
            elapsed_ms=elapsed_ms,
            raw=output,
        )

    return _result(
        "错误",
        "ROS2-D-STATUS",
        output or f"ros2 daemon status 返回非零状态：{completed.returncode}",
        "请确认 ROS2 环境已 source，ros2 daemon 子命令可用，并检查终端中的详细报错。",
        elapsed_ms=elapsed_ms,
        raw=output,
    )


def _start_daemon(timeout_sec=4.0):
    completed, meta = _run_ros2(["daemon", "start"], timeout_sec)
    if completed is None:
        return meta

    output = _combined_output(completed)
    elapsed_ms = meta
    if completed.returncode == 0:
        return _result(
            "正常",
            "ROS2-D-STARTED",
            "自检已启动 ROS2 daemon。",
            "后续后端 ROS2 graph 查询可以复用该 daemon；机器人节点通信本身不依赖 daemon。",
            elapsed_ms=elapsed_ms,
            raw=output,
            started=True,
        )

    return _result(
        "错误",
        "ROS2-D-START",
        output or f"ros2 daemon start 返回非零状态：{completed.returncode}",
        "请确认 ROS2 环境已 source，且当前用户有权限启动 ROS2 daemon。",
        elapsed_ms=elapsed_ms,
        raw=output,
    )


def _wait_until_running(timeout_sec=4.0):
    deadline = time.monotonic() + timeout_sec
    last_result = None
    while time.monotonic() < deadline:
        last_result = check_ros_daemon(timeout_sec=1.0)
        if last_result["status"] == "正常":
            last_result["code"] = "ROS2-D-STARTED"
            last_result["detail"] = "自检已确认 ROS2 daemon 正在运行。"
            last_result["advice"] = "可以继续执行话题和设备检查。"
            last_result["metric"] = _metric("正常", started=True)
            last_result["startedByRobotStation"] = True
            return last_result
        time.sleep(0.25)

    return _result(
        "错误",
        "ROS2-D-START-TIMEOUT",
        f"已尝试启动 ROS2 daemon，但 {timeout_sec:.1f}s 内仍未确认运行。",
        "请在终端执行 ros2 daemon status 查看详细状态，并检查 ROS2 环境。",
        raw=(last_result or {}).get("raw", ""),
    )


def _repair_stuck_daemon(timeout_sec=4.0):
    domain_id = _ros_domain_id()
    if domain_id != REPAIRABLE_ROS_DOMAIN_ID:
        return _result(
            "错误",
            "ROS2-D-REPAIR-SKIPPED",
            (
                f"当前 ROS_DOMAIN_ID={domain_id}，自动修复仅允许处理 "
                f"ROS_DOMAIN_ID={REPAIRABLE_ROS_DOMAIN_ID}。"
            ),
            "请确认启动环境的 ROS_DOMAIN_ID 是否为 99。",
        )

    pids = _daemon_pids_for_domain(domain_id)
    kill_result = (
        _terminate_daemon_pids(pids)
        if pids
        else {"terminated": [], "forced": [], "errors": []}
    )
    raw_lines = [
        f"repair domain={domain_id}",
        f"daemon pids={','.join(str(pid) for pid in pids) or 'none'}",
        f"terminated={','.join(str(pid) for pid in kill_result['terminated']) or 'none'}",
        f"forced={','.join(str(pid) for pid in kill_result['forced']) or 'none'}",
    ]
    raw_lines.extend(kill_result["errors"])

    if kill_result["errors"]:
        return _result(
            "错误",
            "ROS2-D-REPAIR",
            "自动修复 ROS2 daemon 失败：" + "；".join(kill_result["errors"]),
            "请检查当前用户是否有权限终止 ROS2 daemon，"
            "或手动确认 ROS2 daemon 进程状态。",
            raw="\n".join(raw_lines),
        )

    start_result = _start_daemon(timeout_sec=timeout_sec)
    raw_lines.append(start_result.get("raw", ""))
    if start_result["status"] != "正常":
        start_result["raw"] = "\n".join(line for line in raw_lines if line)
        return start_result

    wait_result = _wait_until_running(timeout_sec=timeout_sec)
    wait_result["raw"] = "\n".join(
        line for line in [*raw_lines, wait_result.get("raw", "")] if line
    )
    if wait_result["status"] == "正常":
        pid_text = (
            ", ".join(str(pid) for pid in pids)
            if pids
            else "未找到旧 daemon 进程"
        )
        wait_result["code"] = "ROS2-D-REPAIRED"
        wait_result["detail"] = (
            f"已自动修复 ROS2 daemon（ROS_DOMAIN_ID={domain_id}，旧 pid={pid_text}）。"
        )
        wait_result["advice"] = "可以继续执行话题和设备检查。"
        wait_result["startedByRobotStation"] = True
    else:
        wait_result["detail"] = (
            f"已尝试自动修复 ROS2 daemon（ROS_DOMAIN_ID={domain_id}），"
            f"但仍未确认运行：{wait_result.get('detail', '')}"
        )
    return wait_result


def ensure_ros_daemon(timeout_sec=2.5, startup_timeout_sec=4.0):
    result = check_ros_daemon(timeout_sec=timeout_sec)
    if result["status"] == "正常":
        return result
    if _should_repair_daemon(result):
        return _repair_stuck_daemon(timeout_sec=startup_timeout_sec)

    start_result = _start_daemon(timeout_sec=startup_timeout_sec)
    if start_result["status"] != "正常":
        if _should_repair_daemon(start_result):
            return _repair_stuck_daemon(timeout_sec=startup_timeout_sec)
        return start_result

    wait_result = _wait_until_running(timeout_sec=startup_timeout_sec)
    if wait_result["status"] != "正常" and _should_repair_daemon(wait_result):
        return _repair_stuck_daemon(timeout_sec=startup_timeout_sec)
    return wait_result
