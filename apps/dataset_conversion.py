"""Offline conversion manager. Does not import robot control or mutate source datasets."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid

NAME = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
SOURCE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
JOB_ID = re.compile(r"^[a-f0-9]{32}$")
DATA_PATTERN = "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet"
VIDEO_PATTERN = "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4"
TERMINAL = {"succeeded", "failed", "cancelled"}


class ConversionError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def child_path(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ConversionError("数据声明了不安全的文件路径")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ConversionError("数据文件路径越界或为符号链接")
    # Reject symlinked intermediate directories, including links that point inside.
    cursor = path
    while cursor != root:
        if cursor.is_symlink():
            raise ConversionError("数据文件路径包含符号链接")
        cursor = cursor.parent
    return path


def dataset_layout(source):
    info = load_json(child_path(source, "meta/info.json"))
    if info.get("codebase_version") != "v2.1":
        raise ConversionError("当前支持 SONIC 原生 LeRobot v2.1；其他版本需要专门适配")
    if not isinstance(info,dict):
        raise ConversionError("info.json 必须是 JSON 对象")
    episodes = json_lines(child_path(source, "meta/episodes.jsonl"))
    features = info.get("features", {})
    if not isinstance(features, dict) or not features or any(not isinstance(feature,dict) for feature in features.values()):
        raise ConversionError("缺少 features 字段声明")
    if not episodes:
        raise ConversionError("数据集没有已保存片段")
    if any(not isinstance(row,dict) for row in episodes):
        raise ConversionError("片段元数据格式无效")
    ids = [row.get("episode_index") for row in episodes]
    if any(type(index) is not int or index < 0 for index in ids) or len(set(ids)) != len(ids):
        raise ConversionError("片段编号无效或重复")
    if len(episodes) != info.get("total_episodes"):
        raise ConversionError("片段数量与 info.json 不一致")
    if any(type(row.get("length")) is not int or row["length"] < 1 for row in episodes):
        raise ConversionError("片段帧数无效")
    if sum(row["length"] for row in episodes) != info.get("total_frames"):
        raise ConversionError("总帧数与片段元数据不一致")
    fps = info.get("fps")
    if isinstance(fps, bool) or not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
        raise ConversionError("数据集帧率无效")
    chunks = info.get("chunks_size", 1000)
    if type(chunks) is not int or chunks < 1:
        raise ConversionError("chunks_size 无效")
    videos = [key for key, feature in features.items() if feature.get("dtype") == "video"]
    if any(feature.get("dtype") == "image" for feature in features.values()):
        raise ConversionError("当前转换器支持 SONIC 的 MP4 视频布局，内嵌 image 数据需另行适配")
    records = []
    for episode in episodes:
        index = episode["episode_index"]
        values = {"episode_index": index, "episode_chunk": index // chunks}
        try:
            parquet = child_path(source, info.get("data_path", DATA_PATTERN).format(**values))
            camera_files = {key: child_path(source, info.get("video_path", VIDEO_PATTERN).format(video_key=key, **values)) for key in videos}
        except (KeyError, ValueError, AttributeError) as error:
            raise ConversionError("data_path / video_path 模板无效") from error
        records.append({"episode": episode, "parquet": parquet, "videos": camera_files})
    return info, records


def inspect_source(source, dataset):
    result = {"dataset": dataset, "native_format": "LeRobot v2.1 / SONIC VLA",
              "can_convert": False, "errors": [], "warnings": [], "features": [],
              "episodes": 0, "frames": 0, "fps": None, "video_keys": [], "bytes": 0, "fingerprint": ""}
    if (source/".incomplete").exists():
        result["errors"].append("采集任务尚未正常结束或数据待核验；请先结束任务并检查完整性")
    if (source / "DEMO_ONLY.md").is_file():
        result["demo_only"] = True
        result["errors"].append("此目录仅有演示元数据，没有可转换的实际采集数据")
    try:
        info, records = dataset_layout(source)
        result.update(episodes=len(records), frames=info["total_frames"], fps=info["fps"],
                      video_keys=list(records[0]["videos"]),
                      features=[{"name": key, "dtype": feature.get("dtype"), "shape": feature.get("shape", [])} for key, feature in info["features"].items()])
        result["demo_only"] = bool(info.get("demo_only") or (source / "DEMO_ONLY.md").is_file())
        if result["demo_only"] and not result["errors"]:
            result["errors"].append("此目录是演示元数据，不能作为正式采集数据转换")
        if info.get("discarded_episode_indices"):
            result["warnings"].append("本次完整导出保留全部片段及原有舍弃标记，不清洗、不重采样")
        digest = hashlib.sha256()
        for relative in ["meta/info.json", "meta/episodes.jsonl", "meta/tasks.jsonl", "meta/modality.json"]:
            path = child_path(source, relative)
            if path.is_file():
                digest.update(relative.encode())
                digest.update(path.read_bytes())
        missing = []
        for record in records:
            for path in [record["parquet"], *record["videos"].values()]:
                if not path.is_file():
                    missing.append(str(path.relative_to(source)))
                    continue
                stat = path.stat()
                result["bytes"] += stat.st_size
                digest.update(f"{path.relative_to(source)}:{stat.st_size}:{stat.st_mtime_ns}".encode())
        if missing:
            result["errors"].append(f"缺少 {len(missing)} 个实际文件（例如 {missing[0]}）")
        result["fingerprint"] = digest.hexdigest()
        result["can_convert"] = not result["errors"]
    except (OSError, ValueError, TypeError, ConversionError) as error:
        result["errors"].append(str(error))
    return result


class ConversionManager:
    def __init__(self, source_root, runtime_dir, python=None):
        self.source_root = Path(source_root).resolve()
        self.output_root = self.source_root / "conversions"
        self.runtime = Path(runtime_dir) / "conversions"
        self.runtime.mkdir(parents=True, exist_ok=True)
        self.python = Path(python) if python else Path(__file__).parent / ".venv_conversion/bin/python"
        self.worker = Path(__file__).with_name("conversion_worker.py")
        self.lock = threading.RLock()
        self.children = {}
        self._environment = None

    def environment(self):
        if self._environment is None:
            ready = False
            if self.python.is_file():
                try:
                    probe = subprocess.run([str(self.python), "-c", "import numpy,pyarrow,h5py"], capture_output=True, timeout=15)
                    ready = probe.returncode == 0
                except (OSError, subprocess.TimeoutExpired):
                    pass
            self._environment = {"ready": ready, "ffmpeg": bool(shutil.which("ffmpeg")),
                                 "ffprobe": bool(shutil.which("ffprobe")), "output_root": str(self.output_root),
                                 "formats": ["hdf5", "lerobot_v21"], "hdf5_schema": "sonic-hdf5-v1"}
        return self._environment

    def source(self, name):
        if not isinstance(name, str) or not SOURCE_NAME.fullmatch(name) or name == "conversions":
            raise ConversionError("数据集名称无效")
        path = self.source_root / name
        if not path.is_dir() or path.is_symlink() or not path.resolve().is_relative_to(self.source_root):
            raise ConversionError("数据集不存在", 404)
        return path

    def sources(self):
        datasets = []
        for path in sorted(self.source_root.iterdir()):
            if path.name == "conversions" or path.is_symlink() or not path.is_dir() or not SOURCE_NAME.fullmatch(path.name):
                continue
            try:
                info = load_json(child_path(path, "meta/info.json"))
            except (OSError, ValueError, ConversionError):
                continue
            datasets.append({"name": path.name, "version": info.get("codebase_version", "未知"),
                             "episodes": info.get("total_episodes", 0), "frames": info.get("total_frames", 0),
                             "fps": info.get("fps"), "demo_only": bool(info.get("demo_only") or (path / "DEMO_ONLY.md").is_file())})
        return {"ok": True, "datasets": datasets, "environment": self.environment()}

    def inspect(self, name):
        return {"ok": True, "inspection": inspect_source(self.source(name), name)}

    def _folder(self, job_id):
        if not isinstance(job_id, str) or not JOB_ID.fullmatch(job_id):
            raise ConversionError("转换任务编号无效", 404)
        return self.runtime / job_id

    def _job(self, job_id):
        folder = self._folder(job_id)
        try:
            job = load_json(folder / "state.json")
        except (OSError, ValueError) as error:
            raise ConversionError("转换任务不存在", 404) from error
        if job["state"] not in TERMINAL:
            try:
                pid = int((folder / "pid").read_text())
                command = Path(f"/proc/{pid}/cmdline").read_bytes()
                alive = str(self.worker).encode() in command and str(folder).encode() in command
            except (OSError, ValueError):
                alive = False
            if not alive:
                job.update(state="cancelled" if (folder / "cancel").exists() else "failed",
                           message="转换已中断，部分输出保留；源数据未修改", updated_at=time.time())
                atomic_json(folder / "state.json", job)
        child = self.children.get(job_id)
        if child and child.poll() is not None:
            self.children.pop(job_id, None)
        return job

    def jobs(self):
        with self.lock:
            ids = sorted((p.name for p in self.runtime.iterdir() if JOB_ID.fullmatch(p.name)),
                         key=lambda key: (self.runtime / key).stat().st_mtime, reverse=True)[:50]
            return {"ok": True, "jobs": [self._job(key) for key in ids]}

    def job(self, job_id):
        with self.lock:
            return {"ok": True, "job": self._job(job_id)}

    def create(self, payload):
        dataset = payload.get("dataset")
        format_name = payload.get("format")
        name = payload.get("output_name")
        video_mode = payload.get("video_mode", "embedded_mp4")
        if not isinstance(format_name,str) or format_name not in {"hdf5", "lerobot_v21"}:
            raise ConversionError("请选择 HDF5 或 LeRobot v2.1")
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise ConversionError("输出名称限 1～80 位字母、数字、下划线和短横线")
        if not isinstance(video_mode,str) or video_mode not in {"embedded_mp4", "rgb"}:
            raise ConversionError("视频存储方式无效")
        if format_name == "lerobot_v21":
            video_mode = "embedded_mp4"
        with self.lock:
            if any(job["state"] not in TERMINAL for job in self.jobs()["jobs"]):
                raise ConversionError("当前有转换任务在运行，请完成或取消后再提交", 409)
            if not self.environment()["ready"]:
                raise ConversionError("离线转换环境尚未就绪", 503)
            source = self.source(dataset)
            inspection = inspect_source(source, dataset)
            if not inspection["can_convert"]:
                raise ConversionError("；".join(inspection["errors"]), 412)
            if payload.get("fingerprint") != inspection["fingerprint"]:
                raise ConversionError("来源信息已变化，请重新校验", 409)
            if inspection["video_keys"] and not self.environment()["ffprobe"]:
                raise ConversionError("缺少 ffprobe，无法校验视频帧数", 503)
            if format_name == "hdf5" and video_mode == "rgb" and not self.environment()["ffmpeg"]:
                raise ConversionError("缺少 ffmpeg，无法导出 RGB", 503)
            self.output_root.mkdir(exist_ok=True)
            output = self.output_root / name
            if self.output_root.is_symlink() or output.exists() or output.is_symlink():
                raise ConversionError("输出目录已存在，请换一个名称；不会覆盖原数据", 409)
            numeric_bytes = 0
            rgb_bytes = 0
            for feature in inspection["features"]:
                shape = feature.get("shape") or [1]
                if any(type(dimension) is not int or dimension < 1 or dimension > 100000 for dimension in shape):
                    raise ConversionError("字段形状无效")
                count = 1
                for dimension in shape:
                    count *= dimension
                if feature["dtype"] == "video":
                    rgb_bytes += count * inspection["frames"]
                else:
                    numeric_bytes += count * 8 * inspection["frames"]
            needed = inspection["bytes"] * 2 + numeric_bytes
            if format_name == "hdf5" and video_mode == "rgb":
                needed += rgb_bytes
            if shutil.disk_usage(self.output_root).free < needed + 256 * 1024 ** 2:
                raise ConversionError("可用空间不足，请清理或改用压缩视频内嵌", 412)
            job_id = uuid.uuid4().hex
            folder = self.runtime / job_id
            folder.mkdir()
            request = {"id": job_id, "dataset": dataset, "source": str(source), "output": str(output),
                       "format": format_name, "video_mode": video_mode, "fingerprint": inspection["fingerprint"]}
            job = {**request, "state": "queued", "progress": 0, "message": "等待离线转换进程",
                   "created_at": time.time(), "updated_at": time.time(), "files": [], "episodes_done": 0,
                   "episodes_total": inspection["episodes"]}
            atomic_json(folder / "request.json", request)
            atomic_json(folder / "state.json", job)
            with (folder / "worker.log").open("ab") as log:
                child = subprocess.Popen([str(self.python), str(self.worker), "--job-dir", str(folder)],
                                         stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            (folder / "pid").write_text(str(child.pid))
            self.children[job_id] = child
            threading.Thread(target=child.wait, daemon=True).start()
            return {"ok": True, "job": job}

    def cancel(self, job_id):
        with self.lock:
            job = self._job(job_id)
            if job["state"] not in TERMINAL:
                folder = self._folder(job_id)
                (folder / "cancel").touch()
                # Worker checks the marker between batches and video frames; no process belonging to a robot is signalled.
                job["message"] = "正在取消；等待当前文件操作结束"
            return {"ok": True, "job": job}

    def download(self, job_id, relative):
        with self.lock:
            job = self._job(job_id)
            if job["state"] != "succeeded":
                raise ConversionError("只能下载已成功完成的结果", 409)
            output = Path(job["output"])
            if output.is_symlink() or output.parent != self.output_root:
                raise ConversionError("输出路径无效")
            target = child_path(output, relative)
            if not target.is_file():
                raise ConversionError("结果文件不存在", 404)
            return target
