"""Run one offline job in the isolated conversion environment; no robot imports."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import time
import traceback

import h5py
import numpy as np
import pyarrow.parquet as pq

from dataset_conversion import atomic_json, child_path, dataset_layout, inspect_source, load_json


class Cancelled(Exception):
    pass


class Worker:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.request = load_json(self.folder / "request.json")
        self.state = load_json(self.folder / "state.json")
        self.source = Path(self.request["source"])
        self.output = Path(self.request["output"])
        self.last_update = 0
        self.numeric_frames = 0

    def check(self):
        if (self.folder / "cancel").exists():
            raise Cancelled()

    def update(self, message, progress=None, **values):
        self.state.update(message=message, updated_at=time.time(), **values)
        if progress is not None:
            self.state["progress"] = max(0, min(100, progress))
        atomic_json(self.folder / "state.json", self.state)

    def heartbeat(self, message):
        self.check()
        if time.time() - self.last_update > 1:
            self.last_update = time.time()
            self.update(message)

    def copy(self, source, destination):
        self.check()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as src, destination.open("xb") as dst:
            while True:
                self.check()
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
                self.heartbeat("正在复制文件 · " + source.name)

    def probe(self, path, expected, feature=None):
        command = ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                   "-show_entries", "stream=width,height,nb_read_frames,avg_frame_rate", "-of", "json", str(path)]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            while True:
                self.check()
                try:
                    stdout, stderr = process.communicate(timeout=.5)
                    break
                except subprocess.TimeoutExpired:
                    self.heartbeat("校验视频帧数 · " + path.name)
            if process.returncode:
                raise ValueError("视频无法解码：" + path.name)
            streams = json.loads(stdout).get("streams", [])
            if not streams or int(streams[0].get("nb_read_frames", -1)) != expected:
                raise ValueError("视频帧数与 Parquet 不一致：" + path.name)
            width, height = int(streams[0]["width"]), int(streams[0]["height"])
            rate = streams[0].get("avg_frame_rate", "0/1").split("/")
            actual_fps = float(rate[0]) / float(rate[1]) if len(rate) == 2 and float(rate[1]) else 0
            if not math.isclose(actual_fps, self.info["fps"], rel_tol=.005):
                raise ValueError("视频帧率与采样时间轴不一致：" + path.name)
            if feature and feature.get("shape") != [height, width, 3]:
                raise ValueError("视频分辨率与字段声明不一致：" + path.name)
            return width, height
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)

    def numeric_batches(self, record, info):
        parquet = pq.ParquetFile(record["parquet"])
        expected = record["episode"]["length"]
        if parquet.metadata.num_rows != expected:
            raise ValueError("Parquet 帧数与片段元数据不一致")
        required = {"timestamp", "episode_index", "frame_index", "index", "task_index"}
        if not required.issubset(parquet.schema_arrow.names):
            raise ValueError("Parquet 缺少 LeRobot 时间、片段或任务索引")
        declared = {key for key, value in info["features"].items() if value["dtype"] != "video"}
        if not declared.issubset(set(parquet.schema_arrow.names)):
            raise ValueError("Parquet 缺少已声明的数值字段")
        offset = 0
        last_time = None
        for batch in parquet.iter_batches(batch_size=512):
            self.check()
            values = {}
            for name, column in zip(batch.schema.names, batch.columns):
                spec = info["features"].get(name, {})
                if spec.get("dtype") == "video":
                    continue
                rows = column.to_pylist()
                if any(value is None for value in rows):
                    raise ValueError("字段含空值，需要先修复：" + name)
                dtype = spec.get("dtype")
                if dtype == "string":
                    if not all(isinstance(value, str) for value in rows):
                        raise ValueError("不支持的字符串数组：" + name)
                    array = np.asarray(rows, dtype=object)
                else:
                    if dtype not in {"float32", "float64", "int8", "int16", "int32", "int64",
                                     "uint8", "uint16", "uint32", "uint64", "bool"}:
                        raise ValueError("未声明或不支持的字段类型：" + name)
                    try:
                        array = np.asarray(rows, dtype=np.dtype(dtype))
                    except (ValueError, TypeError) as error:
                        raise ValueError("字段形状不一致：" + name) from error
                    shape = tuple(spec.get("shape", []))
                    if array.shape[1:] != shape and not (array.ndim == 1 and shape in {(), (1,)}):
                        raise ValueError("字段维度与声明不一致：" + name)
                values[name] = array
            stamps = np.asarray(values["timestamp"]).reshape(-1)
            if not np.isfinite(stamps).all() or np.any(np.diff(stamps) <= 0) or (last_time is not None and stamps[0] <= last_time):
                raise ValueError("时间戳缺失、无效或未严格递增")
            last_time = float(stamps[-1])
            if not np.all(np.asarray(values["episode_index"]) == record["episode"]["episode_index"]):
                raise ValueError("Parquet 片段编号不一致")
            if not np.array_equal(np.asarray(values["frame_index"]).reshape(-1), np.arange(offset, offset + len(stamps))):
                raise ValueError("帧索引不连续")
            yield offset, values
            offset += len(stamps)
            self.heartbeat("校验并写入数值帧")

    def embedded_video(self, group, path):
        size = path.stat().st_size
        data = group.create_dataset("encoded_mp4", shape=(size,), dtype="uint8",
                                    chunks=(min(1024 * 1024, max(1, size)),))
        group.attrs["encoding"] = "mp4"
        with path.open("rb") as source:
            offset = 0
            while True:
                self.check()
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                data[offset:offset + len(chunk)] = np.frombuffer(chunk, dtype=np.uint8)
                offset += len(chunk)
                self.heartbeat("内嵌原始 MP4 · " + path.parent.name)

    def rgb_video(self, group, path, count, width, height):
        pixels = width * height * 3
        dataset = group.create_dataset("rgb", shape=(count, height, width, 3), dtype="uint8",
                                       chunks=(1, height, width, 3), compression="gzip", compression_opts=1)
        group.attrs["encoding"] = "rgb24"
        process = subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "1", "-i", str(path),
                                    "-map", "0:v:0", "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            for index in range(count):
                self.check()
                frame = process.stdout.read(pixels)
                if len(frame) != pixels:
                    raise ValueError("RGB 视频帧解码提前结束")
                dataset[index] = np.frombuffer(frame, dtype=np.uint8).reshape(height, width, 3)
                self.heartbeat(f"解码 RGB · {path.parent.name} · {index + 1}/{count} 帧")
            if process.stdout.read(1):
                raise ValueError("RGB 视频含多余帧")
            if process.wait(timeout=30) != 0:
                raise ValueError("RGB 视频解码失败")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
            process.stdout.close()

    def hdf5_episode(self, record, info):
        index = record["episode"]["episode_index"]
        target = self.output / "episodes" / f"episode_{index:06d}.hdf5"
        target.parent.mkdir(exist_ok=True)
        with h5py.File(target, "x") as output:
            output.attrs.update(schema="sonic-hdf5-v1", source_format="LeRobot v2.1",
                                episode_index=index, fps=info["fps"], num_frames=record["episode"]["length"])
            text_type = h5py.string_dtype("utf-8")
            meta = output.create_group("meta")
            for key, value in {"info_json": info, "episode_json": record["episode"]}.items():
                meta.create_dataset(key, data=json.dumps(value, ensure_ascii=False), dtype=text_type)
            for name in ["tasks.jsonl", "modality.json"]:
                path = child_path(self.source, "meta/" + name)
                if path.is_file():
                    meta.create_dataset(name.replace(".", "_"), data=path.read_text(encoding="utf-8"), dtype=text_type)
            frames = output.create_group("frames")
            for offset, values in self.numeric_batches(record, info):
                for name, array in values.items():
                    if "/" in name:
                        raise ValueError("字段名包含 HDF5 路径分隔符")
                    if name not in frames:
                        dtype = text_type if array.dtype.kind == "O" else array.dtype
                        options = {"compression": "gzip", "compression_opts": 4}
                        if array.dtype.kind != "O":
                            options["shuffle"] = True
                        frames.create_dataset(name, shape=(record["episode"]["length"], *array.shape[1:]),
                                              dtype=dtype, chunks=(min(512, record["episode"]["length"]), *array.shape[1:]), **options)
                        frames[name].attrs["feature_json"] = json.dumps(info["features"].get(name, {}), ensure_ascii=False)
                    frames[name][offset:offset + len(array)] = array
            cameras = output.create_group("videos")
            for key, path in record["videos"].items():
                if "/" in key:
                    raise ValueError("视频字段名包含 HDF5 路径分隔符")
                width, height = self.probe(path, record["episode"]["length"], info["features"][key])
                group = cameras.create_group(key)
                group.attrs.update(width=width, height=height, fps=info["fps"], num_frames=record["episode"]["length"],
                                   original_feature=key)
                if self.request["video_mode"] == "rgb":
                    self.rgb_video(group, path, record["episode"]["length"], width, height)
                else:
                    self.embedded_video(group, path)

    def run(self):
        try:
            self.update("重新校验来源文件", 1, state="running")
            self.check()
            inspection = inspect_source(self.source, self.request["dataset"])
            if not inspection["can_convert"] or inspection["fingerprint"] != self.request["fingerprint"]:
                raise ValueError("来源数据已变化或不完整，请重新校验")
            info, records = dataset_layout(self.source)
            self.info = info
            self.output.mkdir()  # Exclusive: never overwrite an existing export.
            (self.output / ".incomplete").write_text(self.request["id"])
            for path in sorted((self.source / "meta").rglob("*")):
                self.check()
                if path.is_file() and path.suffix in {".json", ".jsonl"}:
                    path = child_path(self.source, str(path.relative_to(self.source)))
                    self.copy(path, self.output / path.relative_to(self.source))
            for position, record in enumerate(records):
                self.check()
                self.update(f"转换片段 {position + 1}/{len(records)}", 5 + 90 * position / len(records), episodes_done=position)
                if self.request["format"] == "hdf5":
                    self.hdf5_episode(record, info)
                else:
                    for _offset, _values in self.numeric_batches(record, info):
                        pass
                    self.copy(record["parquet"], self.output / record["parquet"].relative_to(self.source))
                    for _key, path in record["videos"].items():
                        self.probe(path, record["episode"]["length"], info["features"][_key])
                        self.copy(path, self.output / path.relative_to(self.source))
                self.update(f"已完成 {position + 1}/{len(records)} 段", 5 + 90 * (position + 1) / len(records),
                            episodes_done=position + 1)
            final = inspect_source(self.source, self.request["dataset"])
            if final["fingerprint"] != self.request["fingerprint"]:
                raise ValueError("转换期间来源文件发生变化，结果未标记完成；请重新导出")
            manifest = {"schema": "robot-station-conversion-v1", "format": self.request["format"],
                        "hdf5_schema": "sonic-hdf5-v1" if self.request["format"] == "hdf5" else None,
                        "video_mode": self.request["video_mode"], "source_dataset": self.request["dataset"],
                        "source_fingerprint": self.request["fingerprint"], "episodes": len(records),
                        "frames": info["total_frames"], "fps": info["fps"], "source_metadata_preserved": True,
                        "preserve_all_episodes": True, "resampled": False,
                        "completed_at": time.time()}
            atomic_json(self.output / "conversion.json", manifest)
            self.check()
            (self.output / ".incomplete").unlink()
            files = [{"path": str(path.relative_to(self.output)), "bytes": path.stat().st_size}
                     for path in sorted(self.output.rglob("*")) if path.is_file()][:100]
            self.update("转换完成 · 原始字段、维度和时间戳已保留", 100, state="succeeded", files=files,
                        result={"episodes": len(records), "frames": info["total_frames"], "format": self.request["format"]})
        except Cancelled:
            self.update("已取消；部分输出保留，源数据未修改", state="cancelled")
        except Exception as error:
            self.update(str(error) + "；部分输出保留，源数据未修改", state="failed")
            traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-dir", required=True)
    Worker(parser.parse_args().job_dir).run()
