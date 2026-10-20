"""Shared persistence and process ownership for the Robot Station execution API."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import math
import os
import signal
import subprocess
import threading
import time
import uuid


class ConsoleError(RuntimeError):
    def __init__(self, message, status=400, code="invalid_request", blockers=None):
        super().__init__(message)
        self.status, self.code, self.blockers = status, code, blockers or []


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def age(timestamp):
    try:
        value = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp()
        delta = time.time() - value
        return delta if delta >= -2 else float("inf")
    except (ValueError, TypeError, AttributeError):
        return float("inf")


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {} if default is None else default


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temp.open("w") as handle:
        json.dump(value, handle, ensure_ascii=False, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)


def process_identity(pid):
    try:
        fields = Path(f"/proc/{int(pid)}/stat").read_text().rsplit(")", 1)[1].split()
        return fields[19] if fields[0] != "Z" else None
    except (OSError, ValueError, IndexError, TypeError):
        return None


class ProcessSupervisor:
    """Only signal children whose persisted Linux start-time still matches."""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.children = {}

    def record(self, name):
        return read_json(self.directory / (name + ".json"))

    def running(self, name):
        row = self.record(name)
        proc = self.children.get(name)
        if proc is not None:
            proc.poll()
        return bool(row.get("start_ticks") and process_identity(row.get("pid")) == row["start_ticks"])

    def start(self, name, argv, cwd, env=None):
        with self.lock:
            if self.running(name):
                return {**self.record(name), "reused": True}
            log_path = self.directory / (name + ".log")
            with log_path.open("ab") as log:
                child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                         stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            self.children[name] = child
            row = {"pid": child.pid, "start_ticks": process_identity(child.pid), "started_at": now(), "log": str(log_path)}
            atomic_json(self.directory / (name + ".json"), row)
            return {**row, "reused": False}

    def stop(self, name, timeout=5):
        with self.lock:
            if not self.running(name):
                child=self.children.get(name)
                if child is not None and process_identity(child.pid) is None:
                    try:child.wait(timeout=1)
                    except subprocess.TimeoutExpired:pass
                return False
            row = self.record(name)
            os.killpg(row["pid"], signal.SIGTERM)
            deadline = time.monotonic() + timeout
            while self.running(name) and time.monotonic() < deadline:
                time.sleep(.05)
            if self.running(name):
                raise ConsoleError("子进程未在期限内停止，已保留进程供检查", 409, "stop_timeout")
            child=self.children.get(name)
            if child is not None:child.wait(timeout=1)
            return True

    def logs(self, name, limit=12000):
        path = self.directory / (name + ".log")
        try:
            with path.open("rb") as handle:
                handle.seek(max(0, path.stat().st_size - limit))
                return handle.read(limit).decode("utf-8", errors="replace")
        except OSError:
            return ""
