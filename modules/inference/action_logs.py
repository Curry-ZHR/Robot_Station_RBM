"""Dedicated JSONL logs for remote inference action chunks."""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = ROOT_DIR / "logs" / "inference"
RECEIVED_ACTIONS_FILE = "received_actions.jsonl"
EXECUTED_ACTIONS_FILE = "executed_actions.jsonl"

LOGGER = logging.getLogger("robot_station")


class InferenceActionLogger:
    def __init__(self, log_dir=None, enabled=True):
        self.log_dir = Path(log_dir) if log_dir is not None else DEFAULT_LOG_DIR
        self.enabled = enabled
        self._lock = threading.Lock()

    def _write(self, filename, payload):
        if not self.enabled:
            return
        entry = {
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            **payload,
        }
        try:
            line = json.dumps(entry, ensure_ascii=False, separators=(",", ":"), default=str)
            with self._lock:
                self.log_dir.mkdir(parents=True, exist_ok=True)
                with (self.log_dir / filename).open("a", encoding="utf-8") as handle:
                    handle.write(line)
                    handle.write("\n")
        except Exception as exc:  # pragma: no cover - logging must not break control
            LOGGER.warning("Failed to write inference action log %s: %s", filename, exc)

    def log_received_chunk(
        self,
        *,
        remote_url,
        prompt,
        local_chunk_id,
        remote_chunk_id,
        raw_chunk,
        valid,
        step_count=None,
        clipped=None,
        clipped_fields=None,
        normalized_chunk=None,
        timing=None,
        error=None,
    ):
        self._write(
            RECEIVED_ACTIONS_FILE,
            {
                "event": "received_action_chunk",
                "remoteUrl": remote_url,
                "prompt": prompt,
                "localChunkId": local_chunk_id,
                "remoteChunkId": remote_chunk_id,
                "valid": bool(valid),
                "stepCount": step_count,
                "clipped": clipped,
                "clippedFields": clipped_fields or [],
                "timing": timing,
                "error": error,
                "rawChunk": raw_chunk,
                "normalizedChunk": normalized_chunk,
            },
        )

    def log_executed_chunk(
        self,
        *,
        remote_url,
        prompt,
        local_chunk_id,
        status,
        requested_steps,
        executed_steps,
        available_steps,
        frequency_hz,
        max_joint_speed_deg_s,
        mask,
        actions,
        timing=None,
        error_code=None,
        error=None,
    ):
        self._write(
            EXECUTED_ACTIONS_FILE,
            {
                "event": "executed_action_chunk",
                "remoteUrl": remote_url,
                "prompt": prompt,
                "localChunkId": local_chunk_id,
                "status": status,
                "requestedSteps": requested_steps,
                "executedSteps": executed_steps,
                "availableSteps": available_steps,
                "frequencyHz": frequency_hz,
                "maxJointSpeedDegS": max_joint_speed_deg_s,
                "mask": mask,
                "timing": timing,
                "errorCode": error_code,
                "error": error,
                "actions": actions,
            },
        )
