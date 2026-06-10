import os
import shutil
import subprocess
import time


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
        "rosDomainId": os.environ.get("ROS_DOMAIN_ID", ""),
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
            env=os.environ.copy(),
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


def ensure_ros_daemon(timeout_sec=2.5, startup_timeout_sec=4.0):
    result = check_ros_daemon(timeout_sec=timeout_sec)
    if result["status"] == "正常":
        return result

    start_result = _start_daemon(timeout_sec=startup_timeout_sec)
    if start_result["status"] != "正常":
        return start_result

    return _wait_until_running(timeout_sec=startup_timeout_sec)
