import shutil
import subprocess
import time


def _metric(status, utilization=None):
    level = "ok"
    if status == "警告":
        level = "warn"
    if status == "错误":
        level = "danger"
    return {
        "label": "负载",
        "value": "--" if utilization is None else f"{utilization:.0f}%",
        "percent": 0 if utilization is None else round(utilization),
        "level": level,
    }


def _result(status, code, detail, advice, metric=None, raw=""):
    return {
        "name": "GPU 可用性",
        "status": status,
        "source": "系统",
        "code": code,
        "advice": advice,
        "detail": detail,
        "checkedAt": time.strftime("%H:%M:%S"),
        "metric": metric or _metric(status),
        "raw": raw,
    }


def _parse_gpu_rows(output):
    rows = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 5:
            continue
        try:
            rows.append(
                {
                    "name": parts[0],
                    "utilization": float(parts[1]),
                    "memoryUsedMb": float(parts[2]),
                    "memoryTotalMb": float(parts[3]),
                    "temperatureC": float(parts[4]),
                }
            )
        except ValueError:
            continue
    return rows


def check_gpu_status(timeout_sec=3.0):
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        return _result(
            "错误",
            "GPU-A-CMD",
            "系统 PATH 中找不到 nvidia-smi，无法确认 NVIDIA GPU 状态。",
            "请确认机器是否需要 GPU；如果需要，请安装/修复 NVIDIA 驱动并重新自检。",
        )

    query = (
        "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu"
    )
    try:
        completed = subprocess.run(
            [nvidia_smi, query, "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        return _result(
            "错误",
            "GPU-A-TIMEOUT",
            f"nvidia-smi 在 {timeout_sec:.1f}s 内没有响应。",
            "请检查 NVIDIA 驱动状态，必要时重启驱动或机器。",
        )
    except OSError as exc:
        return _result(
            "错误",
            "GPU-A-EXEC",
            f"执行 nvidia-smi 失败：{exc}",
            "请检查 nvidia-smi 权限和 NVIDIA 驱动安装。",
        )

    raw = (completed.stdout or completed.stderr or "").strip()
    if completed.returncode != 0:
        return _result(
            "错误",
            "GPU-A-SMI",
            raw or f"nvidia-smi 返回非零状态：{completed.returncode}",
            "请检查 NVIDIA 驱动、GPU 供电和容器/用户权限。",
            raw=raw,
        )

    rows = _parse_gpu_rows(completed.stdout)
    if not rows:
        return _result(
            "错误",
            "GPU-A-NONE",
            "nvidia-smi 没有返回可解析的 GPU 信息。",
            "请确认 GPU 是否存在，以及 nvidia-smi 输出格式是否正常。",
            raw=raw,
        )

    max_util = max(row["utilization"] for row in rows)
    max_temp = max(row["temperatureC"] for row in rows)
    memory_percents = [
        (row["memoryUsedMb"] / row["memoryTotalMb"]) * 100
        for row in rows
        if row["memoryTotalMb"] > 0
    ]
    max_mem_percent = max(memory_percents) if memory_percents else 0.0

    if max_temp >= 90 or max_mem_percent >= 95:
        status = "错误"
        code = "GPU-A-CRITICAL"
        advice = "请停止高负载任务，释放显存或检查散热后再启动推理。"
    elif max_temp >= 80 or max_mem_percent >= 85 or max_util >= 95:
        status = "警告"
        code = "GPU-A-WARN"
        advice = "GPU 当前负载偏高，启动推理前建议确认是否有其他任务占用。"
    else:
        status = "正常"
        code = "GPU-A-OK"
        advice = "GPU 可用，可以继续执行推理前检查。"

    first = rows[0]
    detail = (
        f"检测到 {len(rows)} 张 GPU，{first['name']}；"
        f"最高负载 {max_util:.0f}%，最高温度 {max_temp:.0f} C，"
        f"最高显存占用 {max_mem_percent:.0f}%。"
    )
    return {
        **_result(status, code, detail, advice, metric=_metric(status, max_util), raw=raw),
        "gpus": rows,
        "maxUtilization": round(max_util, 1),
        "maxTemperatureC": round(max_temp, 1),
        "maxMemoryPercent": round(max_mem_percent, 1),
    }
