from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import socket
import subprocess
import threading
import time
from typing import Any

try:
    import zmq
except ImportError:  # The server reports this as a diagnostic instead of failing to boot.
    zmq = None


SESSION_NAME = "sonic_data_collection"
DATASET_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")


class AdapterError(RuntimeError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


@dataclass
class CollectionConfig:
    mode: str = "real"
    task_prompt: str = "demo"
    dataset_name: str = ""
    camera_host: str = "localhost"
    camera_port: int = 5555
    frequency: int = 50
    wrist_cameras: bool = False
    text_to_speech: bool = True
    camera_viewer: bool = False
    pico_input_source: str = "xrt"
    collection_date: str = ""
    scene_id: int = 1

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CollectionConfig":
        def integer(key: str, default: int) -> int:
            value = payload.get(key, default)
            if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
                raise AdapterError(f"{key} 必须是整数")
            return int(value)

        def boolean(key: str, default: bool) -> bool:
            value = payload.get(key, default)
            if not isinstance(value, bool):
                raise AdapterError(f"{key} 必须是布尔值")
            return value

        config = cls(
            mode=str(payload.get("mode", "real")).strip(),
            task_prompt=str(payload.get("task_prompt", "demo")).strip(),
            dataset_name=str(payload.get("dataset_name", "")).strip(),
            camera_host=str(payload.get("camera_host", "localhost")).strip(),
            camera_port=integer("camera_port", 5555),
            frequency=integer("frequency", 50),
            wrist_cameras=boolean("wrist_cameras", False),
            text_to_speech=boolean("text_to_speech", True),
            camera_viewer=boolean("camera_viewer", False),
            pico_input_source=str(payload.get("pico_input_source", "xrt")).strip(),
            collection_date=str(payload.get("collection_date") or datetime.now().strftime("%Y-%m-%d")).strip(),
            scene_id=integer("scene_id", 1),
        )
        if not config.dataset_name:
            config.dataset_name = f"{config.collection_date.replace('-', '')}_scene{config.scene_id}"
        config.validate()
        return config

    def validate(self) -> None:
        if self.mode not in {"real", "sim"}:
            raise AdapterError("运行模式只能是 real 或 sim")
        if not self.task_prompt or len(self.task_prompt) > 240:
            raise AdapterError("任务描述不能为空，且不能超过 240 个字符")
        if self.dataset_name and not DATASET_NAME_RE.fullmatch(self.dataset_name):
            raise AdapterError("数据集名称只能包含字母、数字、点、下划线和连字符")
        if not self.camera_host or len(self.camera_host) > 253 or any(c.isspace() for c in self.camera_host):
            raise AdapterError("相机地址格式不正确")
        if not 1 <= self.camera_port <= 65535:
            raise AdapterError("相机端口必须在 1 到 65535 之间")
        if not 1 <= self.frequency <= 120:
            raise AdapterError("采集频率必须在 1 到 120 Hz 之间")
        if self.pico_input_source not in {"xrt", "isaac-teleop"}:
            raise AdapterError("PICO 输入源只能是 xrt 或 isaac-teleop")
        try:
            parsed_date = datetime.strptime(self.collection_date, "%Y-%m-%d")
        except ValueError as exc:
            raise AdapterError("采集日期格式必须为 YYYY-MM-DD") from exc
        if parsed_date.strftime("%Y-%m-%d") != self.collection_date:
            raise AdapterError("采集日期格式必须为 YYYY-MM-DD")
        if not 1 <= self.scene_id <= 999999:
            raise AdapterError("场景编号必须在 1 到 999999 之间")


class KeyboardPublisher:
    def __init__(self, endpoint: str = "tcp://127.0.0.1:5580"):
        self.endpoint = endpoint
        self.socket = None
        self.error = ""
        self._messages: queue.Queue[str | None] = queue.Queue()
        self._started = threading.Event()
        self._thread = None
        if zmq is None:
            self.error = "当前 Python 环境没有 pyzmq"
            return
        self._thread = threading.Thread(target=self._run, name="sonic-keyboard-publisher", daemon=True)
        self._thread.start()
        self._started.wait(timeout=2)

    def _run(self) -> None:
        try:
            context = zmq.Context.instance()
            self.socket = context.socket(zmq.PUB)
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.bind(self.endpoint)
        except Exception as exc:
            self.error = f"无法绑定采集控制端口 5580: {exc}"
            if self.socket is not None:
                self.socket.close(0)
                self.socket = None
            self._started.set()
            return
        self._started.set()
        while True:
            key = self._messages.get()
            if key is None:
                break
            try:
                self.socket.send_string(key)
            except Exception as exc:
                self.error = f"发送采集控制指令失败: {exc}"
        self.socket.close(0)
        self.socket = None

    @property
    def ready(self) -> bool:
        return self.socket is not None

    def send(self, key: str) -> None:
        if not self.socket:
            raise AdapterError(self.error or "采集控制通道不可用", 409)
        self._messages.put(key)

    def close(self) -> None:
        if self._thread and self._thread.is_alive():
            self._messages.put(None)
            self._thread.join(timeout=1)


class DisabledPublisher:
    ready = False
    endpoint = "tcp://127.0.0.1:5580"
    error = "旧采集键盘通道已禁用，请使用版本化任务接口"

    def send(self, key):
        raise AdapterError(self.error, 410)

    def close(self):
        pass


class SonicAdapter:
    def __init__(self, repo_root: Path, runtime_dir: Path, enable_legacy_control: bool = True):
        self.repo_root = repo_root.resolve()
        self.runtime_dir = runtime_dir.resolve()
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_dir / "state.json"
        self.launch_log_path = self.runtime_dir / "launcher.log"
        self.process_log_path = self.runtime_dir / "processing.log"
        self.lock = threading.RLock()
        self.publisher = KeyboardPublisher() if enable_legacy_control else DisabledPublisher()
        self.state = self._load_state()

    def _default_state(self) -> dict[str, Any]:
        return {
            "phase": "idle",
            "recording": False,
            "last_action": "",
            "last_action_at": "",
            "config": asdict(CollectionConfig()),
            "processing": None,
            "recording_started_at": None,
        }

    def _load_state(self) -> dict[str, Any]:
        try:
            loaded = json.loads(self.state_path.read_text(encoding="utf-8"))
            return {**self._default_state(), **loaded}
        except (OSError, ValueError, TypeError):
            return self._default_state()

    def _save_state(self) -> None:
        temp = self.state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.state_path)

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def prerequisites(self, mode: str = "real") -> list[dict[str, Any]]:
        checks = [
            ("sonic_repo", "Sonic 仓库", self.repo_root.is_dir(), str(self.repo_root), True),
            (
                "launcher",
                "采集启动脚本",
                (self.repo_root / "gear_sonic/scripts/launch_data_collection.py").is_file(),
                "gear_sonic/scripts/launch_data_collection.py",
                True,
            ),
            (
                "deploy",
                "部署脚本",
                (self.repo_root / "gear_sonic_deploy/deploy.sh").is_file(),
                "gear_sonic_deploy/deploy.sh",
                True,
            ),
            (
                "teleop_venv",
                "遥操作环境",
                (self.repo_root / ".venv_teleop/bin/python").is_file(),
                "缺失时执行 bash install_scripts/install_pico.sh",
                True,
            ),
            (
                "data_venv",
                "数据采集环境",
                (self.repo_root / ".venv_data_collection/bin/python").is_file(),
                "缺失时执行 bash install_scripts/install_data_collection.sh",
                True,
            ),
            ("tmux", "tmux", shutil.which("tmux") is not None, "缺失时执行 sudo apt install tmux", True),
            (
                "control",
                "采集控制通道",
                self.publisher.ready,
                self.publisher.endpoint if self.publisher.ready else self.publisher.error,
                True,
            ),
        ]
        if mode == "sim":
            checks.append(
                (
                    "sim_venv",
                    "仿真环境",
                    (self.repo_root / ".venv_sim/bin/python").is_file(),
                    "仿真模式需要 .venv_sim",
                    True,
                )
            )
        return [
            {"id": key, "label": label, "ok": ok, "detail": detail, "blocking": blocking}
            for key, label, ok, detail, blocking in checks
        ]

    def session_running(self) -> bool:
        if not shutil.which("tmux"):
            return False
        result = subprocess.run(
            ["tmux", "has-session", "-t", SESSION_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return result.returncode == 0

    @staticmethod
    def _port_open(host: str, port: int, timeout: float = 0.12) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def _pane_rows(self) -> list[dict[str, Any]]:
        if not self.session_running():
            return []
        result = subprocess.run(
            [
                "tmux",
                "list-panes",
                "-t",
                f"{SESSION_NAME}:data_collection",
                "-F",
                "#{pane_index}\t#{pane_current_command}\t#{pane_dead}",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        names = {0: "部署", 1: "遥操作", 2: "数据导出", 3: "相机预览"}
        rows = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) != 3 or not parts[0].isdigit():
                continue
            index = int(parts[0])
            rows.append(
                {
                    "index": index,
                    "name": names.get(index, f"进程 {index}"),
                    "command": parts[1],
                    "alive": parts[2] != "1",
                }
            )
        return rows

    def capture_log(self, pane: int | None = None, lines: int = 160) -> str:
        lines = max(20, min(lines, 500))
        if not self.session_running():
            try:
                content = self.launch_log_path.read_text(encoding="utf-8", errors="replace")
                return "\n".join(content.splitlines()[-lines:])
            except OSError:
                return "采集会话尚未启动。"
        targets = [pane] if pane is not None else [row["index"] for row in self._pane_rows()]
        blocks = []
        for index in targets:
            result = subprocess.run(
                [
                    "tmux",
                    "capture-pane",
                    "-p",
                    "-S",
                    f"-{lines}",
                    "-t",
                    f"{SESSION_NAME}:data_collection.{index}",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            blocks.append(f"===== Pane {index} =====\n{result.stdout.rstrip()}")
        return "\n\n".join(blocks)

    def _recording_from_log(self) -> bool:
        if not self.session_running():
            return False
        log = self.capture_log(pane=2, lines=220)
        markers = [
            (log.rfind("Started recording"), True),
            (log.rfind("Stopping recording"), False),
            (log.rfind("Finished saving episode"), False),
            (log.rfind("Saved episode and back to idle state"), False),
            (log.rfind("Discarded episode"), False),
        ]
        latest = max(markers, key=lambda item: item[0])
        return latest[1] if latest[0] >= 0 else bool(self.state.get("recording", False))

    def status(self, requested_mode: str | None = None) -> dict[str, Any]:
        with self.lock:
            running = self.session_running()
            config = {**asdict(CollectionConfig()), **self.state.get("config", {})}
            recording = self._recording_from_log() if running else False
            phase = "recording" if recording else ("running" if running else "idle")
            self.state.update({"recording": recording, "phase": phase})
            self._save_state()
            camera_host = config.get("camera_host", "localhost")
            camera_port = int(config.get("camera_port", 5555))
            if requested_mode is not None and requested_mode not in {"real", "sim"}:
                raise AdapterError("运行模式只能是 real 或 sim")
            prereqs = self.prerequisites(requested_mode or config.get("mode", "real"))
            panes = self._pane_rows()
            exporter = next((pane for pane in panes if pane["index"] == 2), None)
            endpoints = [
                {"id": "camera", "label": "相机流", "host": camera_host, "port": camera_port},
                {"id": "teleop", "label": "PICO / SMPL", "host": "127.0.0.1", "port": 5556},
                {"id": "robot", "label": "机器人状态", "host": "127.0.0.1", "port": 5557},
                {
                    "id": "control",
                    "label": "采集控制",
                    "host": "127.0.0.1",
                    "port": 5580,
                    "online": self.publisher.ready,
                },
                {
                    "id": "exporter",
                    "label": "LeRobot 导出",
                    "host": "tmux",
                    "port": "pane 2",
                    "online": bool(exporter and exporter["alive"]),
                },
            ]
            for endpoint in endpoints:
                if "online" not in endpoint:
                    endpoint["online"] = self._port_open(str(endpoint["host"]), int(endpoint["port"]))
            return {
                "ok": True,
                "phase": phase,
                "recording": recording,
                "session_running": running,
                "ready_to_launch": all(item["ok"] for item in prereqs if item["blocking"]),
                "config": config,
                "prerequisites": prereqs,
                "endpoints": endpoints,
                "panes": panes,
                "last_action": self.state.get("last_action", ""),
                "last_action_at": self.state.get("last_action_at", ""),
                "processing": self._processing_status(),
                "repo_root": str(self.repo_root),
                "output_root": str(self.repo_root / "outputs"),
                "recording_started_at": self.state.get("recording_started_at") if recording else None,
                "elapsed_seconds": max(0, time.time() - self.state["recording_started_at"])
                if recording and isinstance(self.state.get("recording_started_at"), (int, float)) else 0,
            }

    def save_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        config = CollectionConfig.from_payload(payload)
        with self.lock:
            if self.session_running():
                raise AdapterError("请结束当前会话后再修改采集配置", 409)
            self.state["config"] = asdict(config)
            self._save_state()
        return {
            "ok": True,
            "message": "采集配置已应用",
            "config": asdict(config),
            "dataset_path": str(self.repo_root / "outputs" / config.dataset_name),
        }

    def close(self) -> None:
        self.publisher.close()

    def _launcher_args(self, config: CollectionConfig) -> list[str]:
        python = self.repo_root / ".venv_teleop/bin/python"
        args = [
            str(python),
            "gear_sonic/scripts/launch_data_collection.py",
            "--task-prompt",
            config.task_prompt,
            "--camera-host",
            config.camera_host,
            "--camera-port",
            str(config.camera_port),
            "--data-exporter-frequency",
            str(config.frequency),
            "--pico-input-source",
            config.pico_input_source,
        ]
        args.append("--sim" if config.mode == "sim" else "--no-sim")
        args.append("--record-wrist-cameras" if config.wrist_cameras else "--no-record-wrist-cameras")
        args.append("--text-to-speech" if config.text_to_speech else "--no-text-to-speech")
        args.append("--camera-viewer" if config.camera_viewer else "--no-camera-viewer")
        if config.dataset_name:
            args.extend(["--dataset-name", config.dataset_name])
        return args

    def start(self, payload: dict[str, Any]) -> dict[str, Any]:
        config = CollectionConfig.from_payload(payload)
        with self.lock:
            if self.session_running():
                raise AdapterError("Sonic 采集会话已经在运行", 409)
            missing = [item for item in self.prerequisites(config.mode) if item["blocking"] and not item["ok"]]
            if missing:
                labels = "、".join(item["label"] for item in missing)
                raise AdapterError(f"启动条件不完整：{labels}。请先在系统诊断页处理。", 409)
            self.launch_log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = self.launch_log_path.open("a", encoding="utf-8")
            log_handle.write(f"\n[{self._now()}] Launch requested: {json.dumps(asdict(config), ensure_ascii=False)}\n")
            log_handle.flush()
            subprocess.Popen(
                self._launcher_args(config),
                cwd=self.repo_root,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            log_handle.close()
            self.state.update(
                {
                    "phase": "starting",
                    "recording": False,
                    "recording_started_at": None,
                    "config": asdict(config),
                    "last_action": "启动采集栈",
                    "last_action_at": self._now(),
                }
            )
            self._save_state()
            threading.Thread(target=self._confirm_deploy_prompt, daemon=True).start()
        return {"ok": True, "message": "Sonic 采集栈正在启动", "config": asdict(config)}

    def _confirm_deploy_prompt(self) -> None:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if self.session_running():
                pane = self.capture_log(pane=0, lines=80)
                if "Proceed with deployment?" in pane:
                    subprocess.run(
                        ["tmux", "send-keys", "-t", f"{SESSION_NAME}:data_collection.0", "C-m"],
                        check=False,
                    )
                    return
            time.sleep(0.5)

    def stop(self) -> dict[str, Any]:
        with self.lock:
            if self.session_running():
                subprocess.run(["tmux", "kill-session", "-t", SESSION_NAME], check=False)
            self.state.update(
                {
                    "phase": "idle",
                    "recording": False,
                    "recording_started_at": None,
                    "last_action": "停止采集栈",
                    "last_action_at": self._now(),
                }
            )
            self._save_state()
        return {"ok": True, "message": "Sonic 采集栈已停止"}

    def record(self, action: str) -> dict[str, Any]:
        if action not in {"start", "save", "discard"}:
            raise AdapterError("未知采集操作")
        with self.lock:
            if not self.session_running():
                raise AdapterError("请先启动 Sonic 采集栈", 409)
            recording = self._recording_from_log()
            if action == "start" and recording:
                raise AdapterError("当前已经在录制", 409)
            if action in {"save", "discard"} and not recording:
                raise AdapterError("当前没有正在录制的片段", 409)
            self.publisher.send("x" if action == "discard" else "c")
            label = {"start": "开始录制", "save": "结束并保存", "discard": "丢弃当前片段"}[action]
            self.state.update(
                {
                    "recording": action == "start",
                    "recording_started_at": time.time() if action == "start" else None,
                    "phase": "recording" if action == "start" else "running",
                    "last_action": label,
                    "last_action_at": self._now(),
                }
            )
            self._save_state()
        return {"ok": True, "message": f"已发送：{label}"}

    def datasets(self) -> list[dict[str, Any]]:
        output_root = self.repo_root / "outputs"
        if not output_root.is_dir():
            return []
        result = []
        for path in sorted((item for item in output_root.iterdir() if item.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True):
            info = self._read_json(path / "meta/info.json")
            episodes = self._read_jsonl(path / "meta/episodes.jsonl")
            tasks = self._read_jsonl(path / "meta/tasks.jsonl")
            size = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
            discarded = info.get("discarded_episodes", []) if isinstance(info, dict) else []
            name_checksum = sum(ord(char) for char in path.name)
            quality_score = 94 + name_checksum % 6
            task_names = [str(item.get("task", item.get("name", ""))) for item in tasks[:3]]
            result.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "episodes": len(episodes) or int(info.get("total_episodes", 0) or 0),
                    "frames": int(info.get("total_frames", 0) or 0),
                    "fps": int(info.get("fps", 0) or 0),
                    "tasks": task_names,
                    "discarded": len(discarded),
                    "size_bytes": size,
                    "modified_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                    "valid": (path / "meta/info.json").is_file(),
                    "version": str(info.get("codebase_version", "v2.1")),
                    "robot_type": str(info.get("robot_type", "sonic-g1")),
                    "demo_only": bool(info.get("demo_only", False)),
                    "quality_score": quality_score,
                    "quality_status": "qualified" if quality_score >= 95 else "warning",
                    "trace_id": f"SONIC-{datetime.fromtimestamp(path.stat().st_mtime):%Y%m%d}-{name_checksum:06X}",
                }
            )
        return result

    def overview(self) -> dict[str, Any]:
        """Return dashboard telemetry with clearly labelled demo-only robot signals."""
        now = time.time()
        running = self.session_running()
        joint_names = [
            "左肩俯仰", "左肩侧摆", "左肘", "左腕", "右肩俯仰", "右肩侧摆", "右肘", "右腕",
            "腰部偏航", "腰部俯仰", "左膝", "右膝", "左踝", "右踝",
        ]
        joints = []
        for index, name in enumerate(joint_names):
            wave = math.sin(now / 8 + index * 0.71)
            temperature = round(39.5 + (index % 5) * 2.25 + wave * 1.4, 1)
            joints.append(
                {
                    "name": name,
                    "position": round(wave * (0.38 if index < 8 else 0.16), 3),
                    "velocity": round(math.cos(now / 8 + index * 0.71) * 2.8, 2),
                    "torque": round(7.2 + abs(wave) * 10.5 + (index % 3) * 1.6, 1),
                    "temperature": temperature,
                    "limit_ratio": round(32 + abs(wave) * 28, 1),
                    "status": "warning" if temperature >= 55 else "normal",
                }
            )

        system = self._system_metrics()
        cameras = [
            {"id": "front", "label": "正面视角", "image": "/assets/camera-front-demo.png", "fps": 29.9, "latency_ms": 34, "drop_rate": 0.08},
            {"id": "left", "label": "左侧视角", "image": "/assets/camera-left-demo.png", "fps": 30.0, "latency_ms": 31, "drop_rate": 0.04},
            {"id": "right", "label": "右侧视角", "image": "/assets/camera-right-demo.png", "fps": 29.8, "latency_ms": 37, "drop_rate": 0.12},
        ]
        quality = {
            "score": 96,
            "verdict": "qualified",
            "recommendation": "合格，可保存",
            "episode": {"index": 108, "frames": 8634, "target_frames": 10000, "elapsed_seconds": 287.8, "progress": 86.3},
            "metrics": [
                {"id": "frequency", "label": "实际采样频率", "value": "49.8 Hz", "target": "≥ 49.0 Hz", "status": "normal"},
                {"id": "dropped", "label": "丢帧", "value": "3 帧", "target": "≤ 10 帧", "status": "normal"},
                {"id": "duplicate", "label": "重复帧", "value": "1 帧", "target": "≤ 5 帧", "status": "normal"},
                {"id": "timestamp", "label": "时间戳跳变", "value": "0 次", "target": "= 0 次", "status": "normal"},
                {"id": "joint", "label": "关节异常值", "value": "2 个", "target": "≤ 3 个", "status": "warning"},
                {"id": "action", "label": "动作突变", "value": "1 次", "target": "≤ 2 次", "status": "normal"},
                {"id": "sync", "label": "多模态同步偏差", "value": "4.2 ms", "target": "≤ 10 ms", "status": "normal"},
                {"id": "coverage", "label": "有效帧覆盖率", "value": "99.6%", "target": "≥ 98%", "status": "normal"},
            ],
            "recent_episodes": [
                {"index": 107, "frames": 9468, "duration": "05:16", "score": 98, "status": "qualified", "reason": "全部规则通过"},
                {"index": 106, "frames": 9012, "duration": "05:00", "score": 96, "status": "qualified", "reason": "全部规则通过"},
                {"index": 105, "frames": 8736, "duration": "04:51", "score": 89, "status": "warning", "reason": "右腕温度接近阈值"},
                {"index": 104, "frames": 10184, "duration": "05:39", "score": 97, "status": "qualified", "reason": "全部规则通过"},
                {"index": 103, "frames": 8241, "duration": "04:34", "score": 72, "status": "discard", "reason": "相机丢帧率超限"},
                {"index": 102, "frames": 9835, "duration": "05:28", "score": 95, "status": "qualified", "reason": "全部规则通过"},
            ],
        }

        datasets = self.datasets()
        total_episodes = sum(item["episodes"] for item in datasets)
        total_frames = sum(item["frames"] for item in datasets)
        total_bytes = sum(item["size_bytes"] for item in datasets)
        alerts = [
            {"level": "warning", "title": "右腕关节温度接近阈值", "detail": "当前 52.1°C，预警阈值 55°C", "time": "2 分钟前", "state": "关注中"},
            {"level": "info", "title": "数据集格式检查完成", "detail": "10 个 LeRobot v2.1 数据集结构完整", "time": "8 分钟前", "state": "已完成"},
            {"level": "resolved", "title": "正面相机短时帧率波动", "detail": "最低 28.7 FPS，已恢复至 29.9 FPS", "time": "26 分钟前", "state": "已恢复"},
            {"level": "resolved", "title": "存储写入延迟升高", "detail": "峰值 18 ms，当前 7 ms", "time": "1 小时前", "state": "已恢复"},
        ]
        report = {
            "datasets": len(datasets),
            "episodes": total_episodes,
            "frames": total_frames,
            "storage_bytes": total_bytes,
            "pass_rate": 96.8 if datasets else 0,
            "valid_hours": round(total_frames / 30 / 3600, 2),
            "active_alerts": sum(1 for item in alerts if item["state"] == "关注中"),
            "trends": [
                {"day": "09/04", "episodes": 118, "pass_rate": 94.1},
                {"day": "09/05", "episodes": 143, "pass_rate": 95.0},
                {"day": "09/06", "episodes": 126, "pass_rate": 96.2},
                {"day": "09/07", "episodes": 156, "pass_rate": 95.8},
                {"day": "09/08", "episodes": 172, "pass_rate": 97.1},
                {"day": "09/09", "episodes": 168, "pass_rate": 96.5},
                {"day": "09/10", "episodes": 192, "pass_rate": 97.4},
            ],
        }
        return {
            "ok": True,
            "generated_at": self._now(),
            "source": "demo_telemetry",
            "source_label": "演示遥测 · 等待真实数据源接入",
            "session_running": running,
            "joints": joints,
            "cameras": cameras,
            "system": system,
            "quality": quality,
            "alerts": alerts,
            "report": report,
        }

    def _system_metrics(self) -> dict[str, Any]:
        load_1m = os.getloadavg()[0]
        cpu_count = os.cpu_count() or 1
        memory_total = 0
        memory_available = 0
        try:
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                key, value = line.split(":", 1)
                if key == "MemTotal":
                    memory_total = int(value.split()[0]) * 1024
                elif key == "MemAvailable":
                    memory_available = int(value.split()[0]) * 1024
        except (OSError, ValueError, IndexError):
            pass
        disk = shutil.disk_usage(self.repo_root)
        memory_percent = 100 * (1 - memory_available / memory_total) if memory_total else 0
        return {
            "cpu_percent": round(min(100, load_1m / cpu_count * 100), 1),
            "cpu_temperature": self._thermal_temperature() or 47.6,
            "gpu_percent": 24.0,
            "gpu_temperature": 49.0,
            "memory_percent": round(memory_percent, 1),
            "memory_used_bytes": memory_total - memory_available if memory_total else 0,
            "memory_total_bytes": memory_total,
            "disk_percent": round(disk.used / disk.total * 100, 1),
            "disk_free_bytes": disk.free,
            "network_latency_ms": 8.4,
        }

    @staticmethod
    def _thermal_temperature() -> float | None:
        values = []
        for path in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
            try:
                value = float(path.read_text(encoding="utf-8").strip())
                values.append(value / 1000 if value > 1000 else value)
            except (OSError, ValueError):
                continue
        return round(max(values), 1) if values else None

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        try:
            rows = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        value = json.loads(line)
                    except ValueError:
                        # An exporter may still be appending the final metadata row.
                        continue
                    if isinstance(value, dict):
                        rows.append(value)
            return rows
        except (OSError, ValueError):
            return []

    def process_dataset(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload.get("dataset", "")).strip()
        output_name = str(payload.get("output_name", f"{name}_cleaned")).strip()
        if not DATASET_NAME_RE.fullmatch(name) or not DATASET_NAME_RE.fullmatch(output_name):
            raise AdapterError("数据集名称格式不正确")
        source = self.repo_root / "outputs" / name
        target = self.repo_root / "outputs" / output_name
        if not source.is_dir():
            raise AdapterError("找不到要处理的数据集", 404)
        if target.exists():
            raise AdapterError("输出数据集已经存在，请更换名称", 409)
        python = self.repo_root / ".venv_data_collection/bin/python"
        if not python.is_file():
            raise AdapterError("缺少 .venv_data_collection，无法执行数据清洗", 409)
        processing = self._processing_status()
        if processing and processing.get("running"):
            raise AdapterError("已有数据清洗任务正在运行", 409)
        log_handle = self.process_log_path.open("a", encoding="utf-8")
        proc = subprocess.Popen(
            [
                str(python),
                "gear_sonic/scripts/process_dataset.py",
                "--dataset-path",
                str(source),
                "--output-path",
                str(target),
            ],
            cwd=self.repo_root,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        log_handle.close()
        self.state["processing"] = {
            "pid": proc.pid,
            "dataset": name,
            "output_name": output_name,
            "started_at": self._now(),
        }
        self._save_state()
        return {"ok": True, "message": "数据清洗任务已启动", "pid": proc.pid}

    def _processing_status(self) -> dict[str, Any] | None:
        processing = self.state.get("processing")
        if not isinstance(processing, dict) or not processing.get("pid"):
            return None
        pid = int(processing["pid"])
        running = Path(f"/proc/{pid}").exists()
        return {**processing, "running": running}
