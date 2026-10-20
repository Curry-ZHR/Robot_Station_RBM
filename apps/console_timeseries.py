"""Read named SONIC Parquet State/Action for synchronized visualization only."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import threading

from console_support import ConsoleError, atomic_json, read_json
from dataset_conversion import ConversionError, child_path, DATA_PATTERN


def episode_layout(source, index):
    try:
        info = json.loads(child_path(source, "meta/info.json").read_text())
        if info.get("demo_only") or (source/"DEMO_ONLY.md").exists():
            raise ConsoleError("演示元数据没有真实关节序列", 404, "no_timeseries")
        if info.get("codebase_version") != "v2.1":
            raise ConsoleError("当前回放支持 SONIC LeRobot v2.1", 412, "unsupported_dataset")
        rows = [json.loads(line) for line in child_path(source, "meta/episodes.jsonl").read_text().splitlines() if line.strip()]
        episodes = [r for r in rows if r.get("episode_index") == index]
        if len(episodes) != 1:
            raise ConsoleError("采集片段不存在或编号重复", 404, "not_found")
        if type(episodes[0].get('length')) is not int or episodes[0]['length']<1:
            raise ConsoleError("片段帧数无效",412,"invalid_frames")
        chunks = info.get("chunks_size", 1000)
        if type(chunks) is not int or chunks < 1:
            raise ConsoleError("chunks_size 无效")
        relative = info.get("data_path", DATA_PATTERN).format(episode_index=index, episode_chunk=index//chunks)
        path = child_path(source, relative)
        if not path.is_file():
            raise ConsoleError("此片段缺少 Parquet 数值数据", 404, "no_timeseries")
        return info, episodes[0], path
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ConversionError) as exc:
        raise ConsoleError("数据集布局无效："+str(exc), 412, "invalid_dataset") from exc


def read_series(source, index, profile, max_points=6000):
    import numpy as np
    import pyarrow.parquet as pq
    info, episode, path = episode_layout(source, index)
    features = info.get("features", {})
    state_key, action_key = "observation.state", "action.wbc"
    names = []
    for key in (state_key, action_key):
        feature = features.get(key, {})
        current = feature.get("names")
        shape = feature.get("shape")
        if not isinstance(current, list) or any(not isinstance(n,str) or not n for n in current) or len(set(current)) != len(current):
            raise ConsoleError(f"{key} 缺少唯一具名关节，不能按索引猜测", 412, "joint_mapping_missing")
        if shape != [len(current)] or not set(profile).issubset(current):
            raise ConsoleError(f"{key} 的形状或 29 身体关节映射不完整", 412, "joint_mapping_missing")
        if feature.get('dtype') not in {'float32','float64'}:
            raise ConsoleError(f"{key} 必须声明浮点关节数据",412,"invalid_frames")
        unit = feature.get("unit")
        if unit is not None and unit != "rad":
            raise ConsoleError("回放仅接受 rad 关节数据", 412, "unsupported_unit")
        sonic_vla='teleop.smpl_joints' in features and 'action.motion_token' in features
        if unit is None and not sonic_vla and not any(v in str(info.get("robot_type", "")).lower() for v in ("g1", "sonic")):
            raise ConsoleError("无法确认此数据集关节单位，请显式声明 rad", 412, "unsupported_unit")
        names.append(current)
    state_names, action_names = names
    if set(state_names) != set(action_names):
        raise ConsoleError("State / Action 关节集合不一致", 412, "joint_mapping_missing")
    order = [action_names.index(n) for n in state_names]
    parquet = pq.ParquetFile(path)
    import pyarrow as pa
    for key in (state_key,action_key):
        field=parquet.schema_arrow.field(key).type
        if not (pa.types.is_list(field) or pa.types.is_fixed_size_list(field)) or not pa.types.is_floating(field.value_type):
            raise ConsoleError("Parquet 关节列必须是浮点数组",412,"invalid_frames")
    if parquet.metadata.num_rows != episode.get("length") or parquet.metadata.num_rows < 1:
        raise ConsoleError("片段帧数与元数据不一致", 412, "invalid_frames")
    count = parquet.metadata.num_rows
    selected = set(np.linspace(0, count-1, min(count, max_points), dtype=np.int64).tolist())
    frames, previous, origin, seen = [], -float("inf"), None, 0
    columns = ["timestamp", state_key, action_key, "frame_index", "episode_index"]
    missing = set(columns)-set(parquet.schema_arrow.names)
    if missing:
        raise ConsoleError("Parquet 缺少字段："+", ".join(sorted(missing)), 412, "invalid_frames")
    for batch in parquet.iter_batches(batch_size=2048, columns=columns):
        data = batch.to_pydict()
        for offset in range(batch.num_rows):
            timestamp = data["timestamp"][offset]
            if isinstance(timestamp, list) and len(timestamp) == 1:
                timestamp = timestamp[0]
            if isinstance(timestamp, bool) or not isinstance(timestamp,(int,float)) or not math.isfinite(timestamp) or timestamp <= previous:
                raise ConsoleError("片段时间戳必须有限且严格递增", 412, "invalid_timestamps")
            if type(data["frame_index"][offset]) is not int or type(data["episode_index"][offset]) is not int or data["frame_index"][offset] != seen or data["episode_index"][offset] != index:
                raise ConsoleError("帧编号或片段编号不连续", 412, "invalid_frames")
            state = np.asarray(data[state_key][offset], dtype=np.float64)
            action = np.asarray(data[action_key][offset], dtype=np.float64)
            if state.shape != (len(state_names),) or action.shape != (len(action_names),) or not (np.isfinite(state).all() and np.isfinite(action).all()):
                raise ConsoleError("关节数据形状错误或包含非有限值", 412, "invalid_frames")
            origin = timestamp if origin is None else origin
            if seen in selected:
                frames.append({"time_s": float(timestamp-origin), "state": state.tolist(), "action": action[order].tolist(), "frame_index": seen})
            seen += 1
            previous = timestamp
    return {"source": "SONIC LeRobot v2.1 / Parquet", "dataset": source.name, "episode": index,
            "unit": "rad", "time_base": "episode_start", "source_time_origin_s": origin,
            "joint_names": state_names, "state_column": state_key, "action_column": action_key,
            "original_frames": count, "returned_frames": len(frames), "sampled": len(frames)<count,
            "duration_seconds": float(previous-origin), "frames": frames}


class TimeseriesService:
    def __init__(self, workspace, runtime_dir, python=None):
        self.workspace = workspace
        self.directory = Path(runtime_dir)/"timeseries"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.python = Path(python or Path(__file__).parent/".venv_conversion/bin/python")
        self.slots = threading.BoundedSemaphore(2)

    def get(self, dataset, episode, max_points=6000):
        if not isinstance(dataset,str):raise ConsoleError("数据集名称无效")
        source = self.workspace._dataset_path(dataset)
        if (self.workspace.output_root/dataset).is_symlink():
            raise ConsoleError("不读取符号链接数据集",400)
        index = self.workspace.episode_index(episode)
        if type(max_points) is not int or not 2 <= max_points <= 10000:
            raise ConsoleError("max_points 必须在 2 到 10000 之间")
        info, row, parquet = episode_layout(source,index)
        paths = [source/"meta/info.json",source/"meta/episodes.jsonl",parquet]
        def signature():
            return [(str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in paths]
        before=signature()
        profile_path = Path(__file__).parent/"static/assets/g1/profile.json"
        if not profile_path.is_file():profile_path=Path(__file__).parent.parent/"static/assets/g1/profile.json"
        digest = hashlib.sha256(json.dumps([before,max_points,profile_path.read_text()],sort_keys=True).encode()).hexdigest()
        cached = self.directory/(digest+".json")
        if cached.is_file():return read_json(cached)
        if not self.python.is_file():raise ConsoleError("回放数据读取环境未安装",503,"reader_unavailable")
        if not self.slots.acquire(blocking=False):raise ConsoleError("已有回放数据正在读取，请稍后重试",429,"reader_busy")
        try:
            result=subprocess.run([str(self.python),str(Path(__file__)),"--source",str(source),"--episode",str(index),
                "--profile",str(profile_path),"--max-points",str(max_points)],capture_output=True,text=True,timeout=60)
            try:data=json.loads(result.stdout)
            except ValueError as exc:raise ConsoleError("关节序列读取失败，请检查数据字段",412,"invalid_timeseries") from exc
            if not data.get("ok"):
                raise ConsoleError(data.get("message","序列读取失败"),data.get("status",412),data.get("code","invalid_timeseries"))
            if signature()!=before:raise ConsoleError("片段在读取期间变化，请保存完成后重试",409,"source_changed")
            atomic_json(cached,data["series"])
            return data["series"]
        except subprocess.TimeoutExpired as exc:
            raise ConsoleError("片段读取超时",504,"reader_timeout") from exc
        finally:self.slots.release()


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--episode",type=int,required=True)
    parser.add_argument("--profile",type=Path,required=True)
    parser.add_argument("--max-points",type=int,default=6000)
    args=parser.parse_args()
    try:
        result=read_series(args.source,args.episode,read_json(args.profile)["body_joints"],args.max_points)
        print(json.dumps({"ok":True,"series":result},ensure_ascii=False,allow_nan=False))
    except Exception as exc:
        print(json.dumps({"ok":False,"message":str(exc),"status":getattr(exc,"status",412),"code":getattr(exc,"code","invalid_timeseries")},ensure_ascii=False))
        sys.exit(1)
