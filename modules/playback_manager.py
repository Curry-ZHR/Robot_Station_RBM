"""Backend-managed state/action playback execution.

Playback data loading lives in modules.playback. This manager turns validated
action frames into ROS control calls and keeps timing on the backend clock.
"""

from __future__ import annotations

import math
import os
import threading
import time
from typing import Any

from modules.control.chassis import publish_chassis_velocity, stop_chassis
from modules.control.lifting import move_lifting_to_height, stop_lifting
from modules.control.piper import publish_joint_targets
from modules.inference.validation import ActionChunkValidationError, validate_action_chunk
from modules.playback import load_playback_dataset
from modules.ros_io import get_ros_writer


MIN_JOINT_SPEED_DEG_S = 0.5
MAX_JOINT_SPEED_DEG_S = 30.0
DEFAULT_JOINT_SPEED_DEG_S = 20.0
LIFT_MIN_DELTA_M = float(os.environ.get("PLAYBACK_LIFT_MIN_DELTA_M", "0.005"))
JOINT_NAMES = ("joint1", "joint2", "joint3", "joint4", "joint5", "joint6")


class PlaybackExecutionError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _result(ok: bool, code: str, detail: str, **extra: Any) -> dict[str, Any]:
    payload = {"ok": ok, "code": code, "detail": detail}
    payload.update(extra)
    return payload


def _finite_number(value: Any, field: str) -> float:
    if value is None or isinstance(value, bool):
        raise PlaybackExecutionError("PLAYBACK-PAYLOAD", f"{field} must be a number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise PlaybackExecutionError("PLAYBACK-PAYLOAD", f"{field} must be a number.") from exc
    if not math.isfinite(parsed):
        raise PlaybackExecutionError("PLAYBACK-PAYLOAD", f"{field} must be finite.")
    return parsed


def _optional_number(value: Any, field: str) -> float | None:
    if value is None:
        return None
    return _finite_number(value, field)


def _clamp(value: Any, low: float, high: float, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(parsed):
        return default
    return max(low, min(high, parsed))


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, parsed)


def _positive_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(parsed):
        return default
    return max(0.0, parsed)


def _default_piper_enable_publisher(enabled: bool) -> dict[str, Any]:
    return get_ros_writer().publish("piper_enable_all", {"enabled": bool(enabled)})


class PlaybackManager:
    def __init__(
        self,
        dataset_loader=load_playback_dataset,
        piper_enable_publisher=_default_piper_enable_publisher,
        joint_publisher=publish_joint_targets,
        chassis_publisher=publish_chassis_velocity,
        chassis_stopper=stop_chassis,
        lift_mover=move_lifting_to_height,
        lift_stopper=stop_lifting,
        clock=time.perf_counter,
    ):
        self._dataset_loader = dataset_loader
        self._piper_enable_publisher = piper_enable_publisher
        self._joint_publisher = joint_publisher
        self._chassis_publisher = chassis_publisher
        self._chassis_stopper = chassis_stopper
        self._lift_mover = lift_mover
        self._lift_stopper = lift_stopper
        self._clock = clock

        self._state_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread = None
        self._lift_lock = threading.RLock()
        self._lift_thread = None
        self._pending_lift_height = None
        self._last_lift_sent = None

        self._status = "idle"
        self._robot_enabled = False
        self._path = ""
        self._dataset_name = ""
        self._duration_sec = 0.0
        self._elapsed_sec = 0.0
        self._current_frame_index = None
        self._executed_frames = 0
        self._total_frames = 0
        self._last_error = None
        self._last_timing = None
        self._updated_at = None
        self._started_perf = None

    def _set(self, **fields: Any) -> None:
        with self._state_lock:
            for key, value in fields.items():
                setattr(self, f"_{key}", value)
            self._updated_at = time.strftime("%H:%M:%S")

    def status(self) -> dict[str, Any]:
        with self._state_lock:
            elapsed_sec = self._elapsed_sec
            if self._status == "running" and self._started_perf is not None:
                elapsed_sec = min(self._duration_sec, max(elapsed_sec, self._clock() - self._started_perf))
            return _result(
                True,
                "PLAYBACK-STATUS",
                "Playback status.",
                status=self._status,
                running=self._status == "running",
                robotEnabled=self._robot_enabled,
                path=self._path,
                datasetName=self._dataset_name,
                durationSec=self._duration_sec,
                elapsedSec=elapsed_sec,
                currentFrameIndex=self._current_frame_index,
                executedFrames=self._executed_frames,
                totalFrames=self._total_frames,
                lastError=self._last_error,
                timing=self._last_timing,
                updatedAt=self._updated_at,
            )

    def enable_piper(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        enabled = bool(payload.get("enabled", True))
        repeat = _positive_int(payload.get("repeat", 3), 3)
        interval_ms = _positive_float(payload.get("intervalMs", 80), 80.0)

        if not enabled:
            self.stop(reason="clear_prepare")
            self._set(robot_enabled=False, status="stopped", last_error=None)
            return _result(
                True,
                "PLAYBACK-PIPER-DISABLED",
                "Playback enable gate cleared. Piper hardware enable flag was left unchanged.",
                robotEnabled=False,
                results=[],
            )

        results = []
        try:
            for index in range(repeat):
                result = self._piper_enable_publisher(enabled)
                results.append(result)
                if not result.get("ok"):
                    raise PlaybackExecutionError(
                        "PLAYBACK-PIPER-ENABLE",
                        result.get("detail", "Failed to publish Piper enable flag."),
                    )
                if index < repeat - 1 and interval_ms:
                    time.sleep(interval_ms / 1000.0)
        except Exception as exc:
            detail = exc.detail if isinstance(exc, PlaybackExecutionError) else str(exc)
            self._set(last_error=detail)
            return _result(False, "PLAYBACK-PIPER-ENABLE", detail, robotEnabled=self._robot_enabled, results=results)

        self._set(robot_enabled=enabled, status="idle" if enabled else "stopped", last_error=None)
        return _result(
            True,
            "PLAYBACK-PIPER-ENABLED" if enabled else "PLAYBACK-PIPER-DISABLED",
            "Piper enable flag published." if enabled else "Piper enable flag cleared.",
            robotEnabled=enabled,
            results=results,
        )

    def start(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        path = str(payload.get("path") or "").strip()
        if not path:
            return _result(False, "PLAYBACK-PATH", "Missing playback file path.")
        with self._state_lock:
            if not self._robot_enabled:
                return _result(False, "PLAYBACK-DISABLED", "Enable Piper before starting playback.")
            if self._status == "running":
                return _result(False, "PLAYBACK-BUSY", "Playback is already running.")

        load_result = self._dataset_loader({"path": path})
        if not load_result.get("ok"):
            return load_result
        dataset = load_result.get("dataset")
        try:
            frames, metadata = self._prepare_dataset(dataset)
        except (PlaybackExecutionError, ActionChunkValidationError) as exc:
            code = exc.code if isinstance(exc, PlaybackExecutionError) else "PLAYBACK-ACTION"
            return _result(False, code, str(exc))

        joint_speed = _clamp(
            payload.get("maxJointSpeedDegS"),
            MIN_JOINT_SPEED_DEG_S,
            MAX_JOINT_SPEED_DEG_S,
            DEFAULT_JOINT_SPEED_DEG_S,
        )
        self._stop_event.clear()
        self._last_lift_sent = None
        with self._state_lock:
            if self._status == "running":
                return _result(False, "PLAYBACK-BUSY", "Playback is already running.")
            self._status = "running"
            self._path = path
            self._dataset_name = str((dataset or {}).get("name") or "")
            self._duration_sec = metadata["durationSec"]
            self._elapsed_sec = 0.0
            self._current_frame_index = None
            self._executed_frames = 0
            self._total_frames = len(frames)
            self._last_error = None
            self._last_timing = None
            self._started_perf = self._clock()
            self._updated_at = time.strftime("%H:%M:%S")

        thread = threading.Thread(
            target=self._run,
            args=(frames, joint_speed),
            name="playback-executor",
            daemon=True,
        )
        self._thread = thread
        thread.start()
        return _result(
            True,
            "PLAYBACK-STARTED",
            "Playback started.",
            path=path,
            datasetName=self._dataset_name,
            durationSec=metadata["durationSec"],
            totalFrames=len(frames),
            clipped=metadata.get("clipped", 0),
            clippedFields=metadata.get("clippedFields", []),
            maxJointSpeedDegS=joint_speed,
        )

    def stop(self, reason: str = "stop") -> dict[str, Any]:
        self._stop_event.set()
        hold = self._safe_hold()
        with self._state_lock:
            if self._status == "running":
                self._status = "stopping"
            elif self._status not in {"completed", "error"}:
                self._status = "stopped"
            self._updated_at = time.strftime("%H:%M:%S")
        return _result(True, "PLAYBACK-STOPPED", f"Playback stopped ({reason}).", actions=hold)

    def wait(self, timeout: float = 2.0) -> bool:
        thread = self._thread
        if thread is None:
            return True
        thread.join(timeout=timeout)
        return not thread.is_alive()

    def _prepare_dataset(self, dataset: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if not isinstance(dataset, dict):
            raise PlaybackExecutionError("PLAYBACK-NODATA", "Playback dataset is empty.")
        raw_frames = dataset.get("frames")
        if not isinstance(raw_frames, list) or not raw_frames:
            raise PlaybackExecutionError("PLAYBACK-NODATA", "Playback dataset has no frames.")

        actions = []
        frame_meta = []
        for index, frame in enumerate(raw_frames):
            if not isinstance(frame, dict):
                raise PlaybackExecutionError("PLAYBACK-NODATA", f"Playback frame {index} must be an object.")
            seconds = _frame_seconds(frame, index)
            actions.append(_action_from_frame(frame.get("action"), index))
            frame_meta.append(
                {
                    "seconds": seconds,
                    "timestamp": frame.get("timestamp"),
                    "frameIndex": frame.get("frameIndex", index),
                }
            )

        chunk = validate_action_chunk(
            {"type": "action_chunk", "actions": actions},
            max_steps=max(1, len(actions)),
        )
        frames = []
        for meta, step in zip(frame_meta, chunk["steps"]):
            frames.append({**meta, "step": step})
        frames.sort(key=lambda item: item["seconds"])
        base_seconds = frames[0]["seconds"]
        for frame in frames:
            frame["seconds"] = max(0.0, frame["seconds"] - base_seconds)

        duration_sec = frames[-1]["seconds"] if len(frames) > 1 else 0.0
        return frames, {
            "durationSec": max(0.001, duration_sec),
            "clipped": chunk.get("clipped", 0),
            "clippedFields": chunk.get("clippedFields", []),
        }

    def _run(self, frames: list[dict[str, Any]], joint_speed: float) -> None:
        started = self._clock()
        publish_durations_ms = []
        executed = 0
        try:
            for index, frame in enumerate(frames):
                if self._wait_for_frame(started, frame["seconds"]):
                    self._mark_stopped(executed)
                    return

                publish_started = self._clock()
                result = self._publish_step(frame["step"], joint_speed)
                publish_durations_ms.append((self._clock() - publish_started) * 1000.0)
                if not result.get("ok"):
                    self._safe_hold()
                    self._set(status="error", last_error=result.get("detail", "Playback publish failed."))
                    return

                executed += 1
                with self._state_lock:
                    self._elapsed_sec = frame["seconds"]
                    self._current_frame_index = frame["frameIndex"]
                    self._executed_frames = executed
                    self._updated_at = time.strftime("%H:%M:%S")

            self._safe_hold()
            total_ms = (self._clock() - started) * 1000.0
            self._set(
                status="completed",
                elapsed_sec=self._duration_sec,
                executed_frames=executed,
                last_timing={
                    "totalMs": total_ms,
                    "publishAvgMs": _average(publish_durations_ms),
                    "publishMaxMs": max(publish_durations_ms) if publish_durations_ms else None,
                    "framesPublished": executed,
                },
            )
        except Exception as exc:
            self._safe_hold()
            self._set(status="error", last_error=str(exc))

    def _wait_for_frame(self, started: float, target_seconds: float) -> bool:
        while True:
            delay = target_seconds - (self._clock() - started)
            if delay <= 0:
                return False
            if self._stop_event.wait(min(delay, 0.1)):
                return True

    def _publish_step(self, step: dict[str, Any], joint_speed: float) -> dict[str, Any]:
        joint_payload = {
            "max_joint_speed_deg_s": joint_speed,
            "left": {"positions": list(step["left"])},
            "right": {"positions": list(step["right"])},
        }
        joint_result = self._joint_publisher(joint_payload)
        if not joint_result.get("ok"):
            return _result(False, joint_result.get("code", "PLAYBACK-PIPER"), joint_result.get("detail", "Piper publish failed."))

        vx, vy, wz = step["speed"]
        chassis_result = self._chassis_publisher(
            {
                "linearX": vx,
                "linearY": vy,
                "angularZ": wz,
                "commandSource": "playback",
            }
        )
        if not chassis_result.get("ok"):
            return _result(False, chassis_result.get("code", "PLAYBACK-CHASSIS"), chassis_result.get("detail", "Chassis publish failed."))

        self._dispatch_lift(step.get("lift_height"))
        return _result(True, "PLAYBACK-STEP", "Playback step published.")

    def _dispatch_lift(self, height: float | None) -> None:
        if height is None:
            return
        if self._last_lift_sent is not None and abs(height - self._last_lift_sent) < LIFT_MIN_DELTA_M:
            return
        with self._lift_lock:
            self._pending_lift_height = height
            if self._lift_thread is not None and self._lift_thread.is_alive():
                return
            thread = threading.Thread(target=self._run_lift_worker, name="playback-lift", daemon=True)
            self._lift_thread = thread
            thread.start()

    def _run_lift_worker(self) -> None:
        while not self._stop_event.is_set():
            with self._lift_lock:
                target = self._pending_lift_height
                self._pending_lift_height = None
                if target is None:
                    return
                self._last_lift_sent = target
            try:
                self._lift_mover({"height": target})
            except Exception:
                return

    def _mark_stopped(self, executed: int) -> None:
        self._safe_hold()
        self._set(status="stopped", executed_frames=executed)

    def _safe_hold(self) -> dict[str, Any]:
        actions = {}
        with self._lift_lock:
            self._pending_lift_height = None
        try:
            actions["piper"] = self._joint_publisher({"hold": True}).get("ok", False)
        except Exception as exc:
            actions["piper"] = f"error: {exc}"
        try:
            actions["chassis"] = self._chassis_stopper({}).get("ok", False)
        except Exception as exc:
            actions["chassis"] = f"error: {exc}"
        try:
            actions["lift"] = self._lift_stopper({}).get("ok", False)
        except Exception as exc:
            actions["lift"] = f"error: {exc}"
        return actions


def _frame_seconds(frame: dict[str, Any], index: int) -> float:
    for key in ("seconds", "timeSec", "elapsedSec", "time", "timestamp", "timestampSec", "stamp"):
        if key in frame:
            return _finite_number(frame.get(key), f"frames[{index}].{key}")
    raise PlaybackExecutionError("PLAYBACK-TIMESTAMP", f"Playback frame {index} is missing a timestamp.")


def _action_from_frame(action: Any, frame_index: int) -> dict[str, Any]:
    if action is None:
        raise PlaybackExecutionError("PLAYBACK-ACTION", f"Playback frame {frame_index} has no action.")
    if isinstance(action, dict):
        return action
    if not isinstance(action, (list, tuple)):
        raise PlaybackExecutionError("PLAYBACK-ACTION", f"Playback frame {frame_index} action must be an object or vector.")

    if len(action) < 14:
        raise PlaybackExecutionError("PLAYBACK-ACTION", f"Playback frame {frame_index} action must contain at least 14 values.")
    values = [_finite_number(action[index], f"frames[{frame_index}].action[{index}]") for index in range(14)]

    output = {
        "left": _arm_action(values[0:7]),
        "right": _arm_action(values[7:14]),
    }
    lift_height = _optional_number(action[14] if len(action) > 14 else None, f"frames[{frame_index}].action[14]")
    if lift_height is not None:
        output["lift"] = {"height": lift_height}

    speed = {}
    if len(action) > 15 and action[15] is not None:
        speed["vx"] = _finite_number(action[15], f"frames[{frame_index}].action[15]")
    if len(action) > 16 and action[16] is not None:
        speed["vy"] = _finite_number(action[16], f"frames[{frame_index}].action[16]")
    if len(action) > 17 and action[17] is not None:
        speed["wz"] = _finite_number(action[17], f"frames[{frame_index}].action[17]")
    if speed:
        output["speed"] = speed
    return output


def _arm_action(values: list[float]) -> dict[str, float]:
    if len(values) != 7:
        raise PlaybackExecutionError("PLAYBACK-ACTION", "Arm action must contain 7 values.")
    arm = {name: values[index] for index, name in enumerate(JOINT_NAMES)}
    arm["gripper"] = values[6]
    return arm


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


_manager = None
_manager_lock = threading.Lock()


def get_playback_manager() -> PlaybackManager:
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = PlaybackManager()
        return _manager
