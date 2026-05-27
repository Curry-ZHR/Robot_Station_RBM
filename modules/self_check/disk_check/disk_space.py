import shutil
import tempfile
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
GB = 1024 ** 3

CHECK_TARGETS = (
    {
        "name": "data",
        "path": ROOT_DIR / "data",
        "recommendedFreeGb": 50.0,
        "criticalFreeGb": 10.0,
    },
    {
        "name": "logs",
        "path": ROOT_DIR / "logs",
        "recommendedFreeGb": 1.0,
        "criticalFreeGb": 0.2,
    },
)


def _format_gb(value):
    return f"{value / GB:.1f} GB"


def _existing_parent(path):
    current = path
    while not current.exists() and current.parent != current:
        current = current.parent
    return current if current.exists() else Path("/")


def _metric(status, used_percent, free_gb):
    level = "ok"
    if status == "警告":
        level = "warn"
    if status == "错误":
        level = "danger"
    return {
        "label": "占用",
        "value": f"{used_percent:.0f}%",
        "percent": round(used_percent),
        "level": level,
        "freeGb": round(free_gb, 1),
    }


def _result(status, code, detail, advice, metric, targets):
    return {
        "name": "磁盘空间",
        "status": status,
        "source": "系统",
        "code": code,
        "advice": advice,
        "detail": detail,
        "checkedAt": time.strftime("%H:%M:%S"),
        "metric": metric,
        "targets": targets,
    }


def _ensure_dir(path):
    if path.exists() and not path.is_dir():
        return False, f"{path} 已存在但不是目录"
    if path.exists():
        return False, ""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return False, str(exc)
    return True, ""


def _is_writable_dir(path):
    if not path.exists() or not path.is_dir():
        return False
    try:
        with tempfile.NamedTemporaryFile(prefix=".robot_station_write_", dir=path):
            return True
    except OSError:
        return False


def _check_target(spec):
    path = spec["path"]
    created, create_error = _ensure_dir(path)
    usage_path = path if path.exists() else _existing_parent(path)
    usage = shutil.disk_usage(usage_path)
    used = usage.total - usage.free
    used_percent = (used / usage.total) * 100 if usage.total else 100.0
    free_gb = usage.free / GB
    writable = _is_writable_dir(path)

    if create_error:
        status = "错误"
        code = "DSK-S-CREATE"
        message = f"{spec['name']} 目录创建失败：{create_error}"
    elif not writable:
        status = "错误"
        code = "DSK-S-PERM"
        message = f"{spec['name']} 目录不可写"
    elif free_gb < spec["criticalFreeGb"] or used_percent >= 95:
        status = "错误"
        code = "DSK-S-CRITICAL"
        message = f"{spec['name']} 所在磁盘空间严重不足"
    elif free_gb < spec["recommendedFreeGb"] or used_percent >= 85:
        status = "警告"
        code = "DSK-S-WARN"
        message = f"{spec['name']} 所在磁盘空间低于建议值"
    else:
        status = "正常"
        code = "DSK-S-OK"
        message = f"{spec['name']} 目录可用"

    return {
        "name": spec["name"],
        "path": str(path.relative_to(ROOT_DIR)),
        "absolutePath": str(path),
        "status": status,
        "code": code,
        "message": message,
        "created": created,
        "writable": writable,
        "usagePath": str(usage_path),
        "totalGb": round(usage.total / GB, 1),
        "freeGb": round(free_gb, 1),
        "usedPercent": round(used_percent, 1),
        "recommendedFreeGb": spec["recommendedFreeGb"],
        "criticalFreeGb": spec["criticalFreeGb"],
    }


def _aggregate_status(targets):
    if any(target["status"] == "错误" for target in targets):
        return "错误", "DSK-S-ERROR"
    if any(target["status"] == "警告" for target in targets):
        return "警告", "DSK-S-WARN"
    return "正常", "DSK-S-OK"


def check_disk_space():
    targets = [_check_target(spec) for spec in CHECK_TARGETS]
    status, code = _aggregate_status(targets)
    worst_used_percent = max(target["usedPercent"] for target in targets)
    min_free_gb = min(target["freeGb"] for target in targets)
    metric = _metric(status, worst_used_percent, min_free_gb)
    created_names = [target["path"] for target in targets if target["created"]]
    failed = [target for target in targets if target["status"] == "错误"]
    warned = [target for target in targets if target["status"] == "警告"]

    summary = "，".join(
        f"{target['path']} 剩余 {target['freeGb']:.1f} GB，占用 {target['usedPercent']:.1f}%"
        for target in targets
    )
    created_text = f"；已自动创建 {', '.join(created_names)}" if created_names else ""

    if failed:
        detail = f"{summary}{created_text}。失败项：{'; '.join(target['message'] for target in failed)}。"
        advice = "请确认项目目录权限和磁盘挂载状态，修复后重新执行自检。"
    elif warned:
        detail = f"{summary}{created_text}。警告项：{'; '.join(target['message'] for target in warned)}。"
        advice = "短任务可以继续，长时间数采前建议清理磁盘或更换数据目录。"
    else:
        detail = f"{summary}{created_text}。logs 和 data 目录均可写，磁盘空间满足建议。"
        advice = "可以继续执行数采、日志记录和推理任务。"

    return _result(status, code, detail, advice, metric, targets)

