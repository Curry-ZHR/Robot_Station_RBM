"""Collection records and human reviews backed by LeRobot metadata on disk."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
import json
import math

from sonic_adapter import AdapterError, DATASET_NAME_RE, SonicAdapter


class CollectionWorkspace:
    def __init__(self, adapter: SonicAdapter):
        self.adapter = adapter
        self.output_root = (adapter.repo_root / "outputs").resolve()
        self.reviews_path = adapter.runtime_dir / "episode-reviews.json"

    @staticmethod
    def _number(value: Any, default: float = 0) -> float:
        try:
            number = float(value)
            return number if math.isfinite(number) and number >= 0 else default
        except (TypeError, ValueError, OverflowError):
            return default

    def _dataset_path(self, name: str) -> Path:
        if not DATASET_NAME_RE.fullmatch(name):
            raise AdapterError("数据集名称格式不正确")
        path = (self.output_root / name).resolve()
        if not path.is_relative_to(self.output_root) or not path.is_dir():
            raise AdapterError("找不到数据集", 404)
        return path

    def _metadata(self, path: Path) -> tuple[dict, list[dict]]:
        info = self.adapter._read_json(path / "meta/info.json")
        rows = self.adapter._read_jsonl(path / "meta/episodes.jsonl")
        return info, rows

    def _rows(self, path: Path, info: dict, raw: list[dict], reviews: dict) -> list[dict]:
        fps = self._number(info.get("fps"))
        discarded = set()
        for key in ("discarded_episodes", "discarded_episode_indices"):
            values = info.get(key, [])
            if isinstance(values, list):
                discarded.update(str(i) for i in values)
        dataset_reviews = reviews.get(path.name, {})
        if not isinstance(dataset_reviews, dict):
            dataset_reviews = {}
        result, seen = [], set()
        for row in raw:
            index = row.get("episode_index")
            if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index in seen:
                continue
            seen.add(index)
            frames = int(self._number(row.get("length")))
            review = dataset_reviews.get(str(index), {})
            if not isinstance(review, dict):
                review = {}
            grade = review.get("grade") if review.get("grade") in {"A", "B", "F"} else None
            tasks = row.get("tasks", [])
            tasks = [str(task) for task in tasks] if isinstance(tasks, list) else []
            is_discarded = bool(row.get("discarded")) or str(index) in discarded
            result.append({
                "episode_index": index,
                "name": f"episode_{index:06d}",
                "dataset": path.name,
                "frames": frames,
                "fps": fps,
                "duration_seconds": round(frames / fps, 3) if fps else None,
                "tasks": tasks,
                "grade": grade,
                "reviewed_at": review.get("reviewed_at"),
                "state": "discarded" if is_discarded else "saved",
                "demo_only": bool(info.get("demo_only", False)),
            })
        return sorted(result, key=lambda row: row["episode_index"], reverse=True)

    def groups(self) -> list[dict]:
        if not self.output_root.is_dir():
            return []
        reviews = self.adapter._read_json(self.reviews_path)
        groups = []
        for candidate in self.output_root.iterdir():
            if not candidate.is_dir() or not DATASET_NAME_RE.fullmatch(candidate.name):
                continue
            path = candidate.resolve()
            if not path.is_relative_to(self.output_root):
                continue
            info, raw = self._metadata(path)
            if not info:
                continue
            rows = self._rows(path, info, raw, reviews)
            counts = {grade: 0 for grade in ("A", "B", "F", "unreviewed", "discarded")}
            for row in rows:
                counts["discarded" if row["state"] == "discarded" else row["grade"] or "unreviewed"] += 1
            groups.append({
                "name": candidate.name,
                "path": str(path),
                "episodes": len(rows),
                "retained": len(rows) - counts["discarded"],
                "frames": sum(row["frames"] for row in rows),
                "fps": self._number(info.get("fps")),
                "demo_only": bool(info.get("demo_only", False)),
                "counts": counts,
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                "version": str(info.get("codebase_version", "LeRobot")),
            })
        return sorted(groups, key=lambda group: group["modified_at"], reverse=True)

    def snapshot(self, mode: str | None = None) -> dict:
        groups = self.groups()
        real = [group for group in groups if not group["demo_only"]]
        return {
            "ok": True,
            "generated_at": self.adapter._now(),
            "status": self.adapter.status(mode),
            "groups": groups,
            "totals": {
                "datasets": len(real),
                "episodes": sum(group["retained"] for group in real),
                "frames": sum(group["frames"] for group in real),
                "demo_episodes": sum(group["retained"] for group in groups if group["demo_only"]),
            },
        }

    def episodes(self, name: str, offset: int = 0, limit: int = 30) -> dict:
        if offset < 0 or not 1 <= limit <= 100:
            raise AdapterError("offset 必须非负，limit 必须在 1 到 100 之间")
        path = self._dataset_path(name)
        info, raw = self._metadata(path)
        rows = self._rows(path, info, raw, self.adapter._read_json(self.reviews_path))
        return {
            "ok": True, "dataset": name, "path": str(path), "total": len(rows),
            "offset": offset, "limit": limit, "episodes": rows[offset:offset + limit],
        }

    def _episode(self, name: str, index: int) -> tuple[Path, dict, dict]:
        path = self._dataset_path(name)
        info, raw = self._metadata(path)
        rows = self._rows(path, info, raw, self.adapter._read_json(self.reviews_path))
        row = next((row for row in rows if row["episode_index"] == index), None)
        if row is None:
            raise AdapterError("找不到采集片段", 404)
        return path, info, row

    @staticmethod
    def episode_index(value: Any) -> int:
        if isinstance(value, bool) or not str(value).isascii() or not str(value).isdigit():
            raise AdapterError("片段编号必须是非负整数")
        return int(value)

    def rate(self, payload: dict) -> dict:
        name = str(payload.get("dataset", ""))
        index = self.episode_index(payload.get("episode"))
        grade = payload.get("grade")
        if grade not in ("A", "B", "F", None):
            raise AdapterError("评级只能是 A、B、F 或 null")
        with self.adapter.lock:
            _, _, episode = self._episode(name, index)
            if episode["state"] == "discarded":
                raise AdapterError("已丢弃的片段不能评级", 409)
            reviews = self.adapter._read_json(self.reviews_path)
            review = {"grade": grade, "reviewed_at": self.adapter._now()}
            if not isinstance(reviews.get(name), dict):
                reviews[name] = {}
            reviews[name][str(index)] = review
            temp = self.reviews_path.with_suffix(".tmp")
            temp.write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(self.reviews_path)
        return {"ok": True, "message": "评级已保存", "dataset": name, "episode": index, **review}

    def _video_paths(self, path: Path, info: dict, index: int) -> dict[str, Path]:
        features = info.get("features", {})
        features = features if isinstance(features, dict) else {}
        keys = [key for key, feature in features.items() if isinstance(feature, dict) and feature.get("dtype") == "video"]
        chunks = max(1, int(self._number(info.get("chunks_size"), 1000)))
        template = info.get("video_path", "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4")
        candidates = {}
        for key in keys:
            try:
                relative = str(template).format(episode_chunk=index // chunks, video_key=key, episode_index=index)
            except (KeyError, IndexError, ValueError):
                continue
            candidates[str(key)] = path / relative
        # Some existing datasets omit the video feature declarations.
        for video in path.glob(f"videos/chunk-*/*/episode_{index:06d}.mp4"):
            candidates.setdefault(video.parent.name, video)
        return {
            key: video.resolve() for key, video in candidates.items()
            if video.resolve().is_relative_to(path) and video.suffix.lower() == ".mp4" and video.is_file()
        }

    def review(self, name: str, index: int) -> dict:
        path, info, row = self._episode(name, index)
        videos = []
        for key in self._video_paths(path, info, index):
            label = "左腕" if "left" in key.lower() else "右腕" if "right" in key.lower() else "主视角"
            videos.append({"camera": key, "label": label, "url": "/api/episodes/video?" + urlencode({"dataset": name, "episode": index, "camera": key})})
        return {"ok": True, "episode": row, "dataset_path": str(path), "videos": videos}

    def video(self, name: str, index: int, camera: str) -> Path:
        path, info, _ = self._episode(name, index)
        video = self._video_paths(path, info, index).get(camera)
        if video is None:
            raise AdapterError("找不到此相机的视频文件", 404)
        return video
