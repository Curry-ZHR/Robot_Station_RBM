"""Inference session orchestration.

Ties together the remote WebSocket session, observation builder, chunk
validator and a step executor. The HTTP layer only talks to this manager.

Execution model:
  * connect          -> open the persistent backend->remote WebSocket.
  * request_chunk    -> build observation, send it, receive + validate a chunk.
  * execute_chunk    -> run the first N steps of the cached chunk, paced by a
                        frontend supplied frequency (Hz). A stop event can
                        preempt the loop between any two steps.
  * stop             -> preempt execution and bring the robot to a safe hold.

The continuous closed loop (observe -> request -> execute -> observe ...) is
driven by the frontend repeatedly calling request_chunk then execute_chunk, so
the backend keeps a single-chunk execution contract and a stop that always wins.
"""

import os
import threading
import time

from modules.control.chassis import publish_chassis_velocity, stop_chassis
from modules.control.lifting import move_lifting_to_height, stop_lifting
from modules.control.piper import publish_joint_targets
from modules.inference.action_logs import InferenceActionLogger
from modules.inference.observation import (
    ObservationBuildError,
    build_observation,
    read_current_arm_positions,
)
from modules.inference.session import RemoteInferenceSession, RemoteSessionError
from modules.inference.validation import ActionChunkValidationError, validate_action_chunk


MIN_FREQUENCY_HZ = 1.0
MAX_FREQUENCY_HZ = 30.0
DEFAULT_FREQUENCY_HZ = 10.0
MIN_JOINT_SPEED_DEG_S = 0.5
MAX_JOINT_SPEED_DEG_S = 30.0
DEFAULT_JOINT_SPEED_DEG_S = 20.0
LIFT_MIN_DELTA_M = float(os.environ.get("INFERENCE_LIFT_MIN_DELTA_M", "0.005"))


def _result(ok, code, detail, **extra):
    payload = {"ok": ok, "code": code, "detail": detail}
    payload.update(extra)
    return payload


def _clamp(value, low, high, default):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:  # NaN
        return default
    return max(low, min(high, parsed))


def _normalize_mask(raw):
    """Normalize the action-channel mask. Every channel defaults to enabled.

    Shape: {"left": {"enabled": bool, "joints": [6 bools], "gripper": bool},
            "right": {...}, "lift": bool, "speed": bool}.
    enabled=False means the channel ignores the model output and holds in place.
    """

    raw = raw if isinstance(raw, dict) else {}

    def _side(name):
        side = raw.get(name) if isinstance(raw.get(name), dict) else {}
        joints = side.get("joints")
        if not isinstance(joints, list) or len(joints) != 6:
            joints = [True] * 6
        else:
            joints = [bool(value) for value in joints]
        return {
            "enabled": bool(side.get("enabled", True)),
            "joints": joints,
            "gripper": bool(side.get("gripper", True)),
        }

    return {
        "left": _side("left"),
        "right": _side("right"),
        "lift": bool(raw.get("lift", True)),
        "speed": bool(raw.get("speed", True)),
    }


def _side_needs_snapshot(side_mask):
    """A snapshot is needed only when the side follows the model but freezes
    some of its joints (i.e. enabled with at least one masked joint/gripper)."""
    if not side_mask["enabled"]:
        return False
    return not all(side_mask["joints"]) or not side_mask["gripper"]


class InferenceManager:
    def __init__(
        self,
        session=None,
        joint_publisher=publish_joint_targets,
        chassis_publisher=publish_chassis_velocity,
        chassis_stopper=stop_chassis,
        lift_mover=move_lifting_to_height,
        lift_stopper=stop_lifting,
        observation_builder=build_observation,
        arm_snapshot_reader=read_current_arm_positions,
        action_logger=None,
    ):
        self._session = session or RemoteInferenceSession()
        self._joint_publisher = joint_publisher
        self._chassis_publisher = chassis_publisher
        self._chassis_stopper = chassis_stopper
        self._lift_mover = lift_mover
        self._lift_stopper = lift_stopper
        self._observation_builder = observation_builder
        self._arm_snapshot_reader = arm_snapshot_reader
        self._action_logger = action_logger if action_logger is not None else InferenceActionLogger()

        self._state_lock = threading.RLock()
        self._op_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._lift_thread = None
        self._last_lift_sent = None

        self._status = "disconnected"
        self._prompt = ""
        self._last_chunk = None
        self._last_chunk_timing = None
        self._last_execution_timing = None
        self._last_execution_completed_at = None
        self._last_error = None
        self._executed_steps = 0
        self._updated_at = None
        self._chunk_seq = 0

    # ------------------------------------------------------------------ status
    def _set(self, **fields):
        with self._state_lock:
            for key, value in fields.items():
                setattr(self, f"_{key}", value)
            self._updated_at = time.strftime("%H:%M:%S")

    def _next_chunk_id(self):
        with self._state_lock:
            chunk_id = f"chunk_{self._chunk_seq:04d}"
            self._chunk_seq += 1
            return chunk_id

    def _reset_chunk_ids(self):
        with self._state_lock:
            self._chunk_seq = 0

    def status(self):
        with self._state_lock:
            chunk = self._last_chunk
            return _result(
                True,
                "INFER-STATUS",
                "Inference status.",
                status=self._status,
                connected=self._session.is_connected(),
                remoteUrl=self._session.url,
                prompt=self._prompt,
                chunkId=chunk.get("chunk_id") if chunk else None,
                chunkSteps=chunk.get("stepCount") if chunk else 0,
                executedSteps=self._executed_steps,
                chunkTiming=self._last_chunk_timing,
                executionTiming=self._last_execution_timing,
                lastError=self._last_error,
                updatedAt=self._updated_at,
            )

    # ----------------------------------------------------------------- connect
    def connect(self, url):
        try:
            self._session.connect(url)
        except RemoteSessionError as exc:
            self._set(status="error", last_error=exc.detail)
            return _result(False, exc.code, exc.detail)
        self._reset_chunk_ids()
        self._set(
            status="connected",
            last_error=None,
            last_chunk=None,
            last_chunk_timing=None,
            last_execution_timing=None,
            last_execution_completed_at=None,
            executed_steps=0,
        )
        self._last_lift_sent = None
        return _result(True, "INFER-CONNECTED", "Connected to remote inference server.", remoteUrl=self._session.url)

    # ----------------------------------------------------------- request chunk
    def request_chunk(self, payload):
        payload = payload if isinstance(payload, dict) else {}
        prompt = payload.get("prompt", self._prompt)
        chassis_limits_override = payload.get("chassisLimits")
        if not self._op_lock.acquire(blocking=False):
            return _result(False, "INFER-BUSY", "Another inference operation is in progress.")
        try:
            if not self._session.is_connected():
                return _result(False, "INFER-WS-DISCONNECTED", "Connect to a remote inference server first.")
            self._stop_event.clear()
            self._set(status="requesting", prompt=str(prompt or ""))
            request_started = time.perf_counter()
            observation_started = request_started
            try:
                observation = self._observation_builder(prompt)
            except ObservationBuildError as exc:
                self._set(status="error", last_error=exc.detail)
                return _result(False, exc.code, exc.detail)
            observation_ms = (time.perf_counter() - observation_started) * 1000.0

            try:
                message = self._session.request_chunk(observation)
            except RemoteSessionError as exc:
                self._set(status="error", last_error=exc.detail)
                if not self._session.is_connected():
                    self._reset_chunk_ids()
                self._safe_hold()
                return _result(False, exc.code, exc.detail)

            exchange_timing = getattr(self._session, "last_exchange_timing", None) or {}
            chunk_timing = {
                "observationMs": observation_ms,
                "sendMs": exchange_timing.get("sendMs"),
                "receiveMs": exchange_timing.get("receiveMs"),
                "roundTripMs": exchange_timing.get("roundTripMs"),
                "totalMs": (time.perf_counter() - request_started) * 1000.0,
                "ignoredMessages": exchange_timing.get("ignoredMessages", 0),
            }
            remote_chunk_id = message.get("chunk_id") if isinstance(message, dict) else None
            try:
                chunk = validate_action_chunk(message, chassis_limits_override=chassis_limits_override)
            except ActionChunkValidationError as exc:
                self._action_logger.log_received_chunk(
                    remote_url=self._session.url,
                    prompt=str(prompt or ""),
                    local_chunk_id=None,
                    remote_chunk_id=remote_chunk_id,
                    raw_chunk=message,
                    valid=False,
                    timing=chunk_timing,
                    error=str(exc),
                )
                self._set(status="error", last_error=str(exc), last_chunk_timing=chunk_timing)
                self._safe_hold()
                return _result(False, "INFER-CHUNK-INVALID", str(exc), chunkTiming=chunk_timing)

            if chunk.get("isSuccess") is True:
                self._action_logger.log_received_chunk(
                    remote_url=self._session.url,
                    prompt=str(prompt or ""),
                    local_chunk_id=None,
                    remote_chunk_id=remote_chunk_id,
                    raw_chunk=message,
                    valid=True,
                    step_count=0,
                    clipped=0,
                    clipped_fields=[],
                    normalized_chunk=chunk,
                    timing=chunk_timing,
                )
                self._set(
                    status="completed",
                    last_chunk=None,
                    last_chunk_timing=chunk_timing,
                    last_error=None,
                    executed_steps=0,
                )
                return _result(
                    True,
                    "INFER-SUCCESS",
                    "Remote inference reported task success.",
                    isSuccess=True,
                    chunkId=None,
                    chunkSteps=0,
                    clipped=0,
                    clippedFields=[],
                    chunkTiming=chunk_timing,
                )

            local_chunk_id = self._next_chunk_id()
            chunk["chunk_id"] = local_chunk_id
            self._action_logger.log_received_chunk(
                remote_url=self._session.url,
                prompt=str(prompt or ""),
                local_chunk_id=local_chunk_id,
                remote_chunk_id=remote_chunk_id,
                raw_chunk=message,
                valid=True,
                step_count=chunk["stepCount"],
                clipped=chunk.get("clipped", 0),
                clipped_fields=chunk.get("clippedFields", []),
                normalized_chunk=chunk,
                timing=chunk_timing,
            )
            self._set(status="chunk_ready", last_chunk=chunk, last_chunk_timing=chunk_timing, last_error=None, executed_steps=0)
            return _result(
                True,
                "INFER-CHUNK-READY",
                "Received and validated an action chunk.",
                chunkId=chunk["chunk_id"],
                chunkSteps=chunk["stepCount"],
                isSuccess=False,
                clipped=chunk.get("clipped", 0),
                clippedFields=chunk.get("clippedFields", []),
                chunkTiming=chunk_timing,
            )
        finally:
            self._op_lock.release()

    # ----------------------------------------------------------- execute chunk
    def execute_chunk(self, payload):
        payload = payload if isinstance(payload, dict) else {}
        with self._state_lock:
            chunk = self._last_chunk
        if not chunk:
            return _result(False, "INFER-NO-CHUNK", "No action chunk is available to execute.")

        steps = chunk["steps"]
        requested = payload.get("steps", len(steps))
        try:
            requested = int(requested)
        except (TypeError, ValueError):
            requested = len(steps)
        n = max(1, min(requested, len(steps)))
        frequency = _clamp(payload.get("frequencyHz"), MIN_FREQUENCY_HZ, MAX_FREQUENCY_HZ, DEFAULT_FREQUENCY_HZ)
        joint_speed = _clamp(
            payload.get("maxJointSpeedDegS"),
            MIN_JOINT_SPEED_DEG_S,
            MAX_JOINT_SPEED_DEG_S,
            DEFAULT_JOINT_SPEED_DEG_S,
        )
        interval = 1.0 / frequency
        mask = _normalize_mask(payload.get("mask"))
        executed_actions = []

        def _average(values):
            if not values:
                return None
            return sum(values) / len(values)

        def _log_execution(status, executed, actions, timing=None, error_code=None, error=None):
            self._action_logger.log_executed_chunk(
                remote_url=self._session.url,
                prompt=self._prompt,
                local_chunk_id=chunk.get("chunk_id"),
                status=status,
                requested_steps=n,
                executed_steps=executed,
                available_steps=len(steps),
                frequency_hz=frequency,
                max_joint_speed_deg_s=joint_speed,
                mask=mask,
                actions=actions,
                timing=timing,
                error_code=error_code,
                error=error,
            )

        if not self._op_lock.acquire(blocking=False):
            return _result(False, "INFER-BUSY", "Another inference operation is in progress.")
        try:
            execute_started = time.perf_counter()
            with self._state_lock:
                previous_completed_at = self._last_execution_completed_at
            first_publish_started = None
            publish_start_times = []
            publish_durations_ms = []
            desired_period_ms = interval * 1000.0

            def _execution_timing(finished_at):
                periods_ms = [
                    (publish_start_times[index] - publish_start_times[index - 1]) * 1000.0
                    for index in range(1, len(publish_start_times))
                ]
                return {
                    "totalMs": (finished_at - execute_started) * 1000.0,
                    "firstStepLatencyMs": (
                        (first_publish_started - execute_started) * 1000.0
                        if first_publish_started is not None
                        else None
                    ),
                    "boundaryGapMs": (
                        (first_publish_started - previous_completed_at) * 1000.0
                        if first_publish_started is not None and previous_completed_at is not None
                        else None
                    ),
                    "desiredPeriodMs": desired_period_ms,
                    "stepPeriodAvgMs": _average(periods_ms),
                    "stepPeriodMinMs": min(periods_ms) if periods_ms else None,
                    "stepPeriodMaxMs": max(periods_ms) if periods_ms else None,
                    "stepPeriodMaxJitterMs": (
                        max(abs(value - desired_period_ms) for value in periods_ms)
                        if periods_ms
                        else None
                    ),
                    "publishAvgMs": _average(publish_durations_ms),
                    "publishMinMs": min(publish_durations_ms) if publish_durations_ms else None,
                    "publishMaxMs": max(publish_durations_ms) if publish_durations_ms else None,
                    "stepsPublished": len(publish_durations_ms),
                }

            def _finish(status, executed, **fields):
                finished_at = time.perf_counter()
                timing = _execution_timing(finished_at)
                update = {
                    "status": status,
                    "executed_steps": executed,
                    "last_execution_timing": timing,
                    "last_execution_completed_at": finished_at,
                }
                update.update(fields)
                self._set(**update)
                return timing

            self._stop_event.clear()
            self._set(status="executing")

            # Snapshot current arm positions for any side that freezes some (but
            # not all) of its joints. Refuse to execute if feedback is missing,
            # rather than guessing where to hold.
            snapshot = {"left": None, "right": None}
            needed_sides = [side for side in ("left", "right") if _side_needs_snapshot(mask[side])]
            if needed_sides:
                snapshot = self._arm_snapshot_reader() or {}
                for side in needed_sides:
                    if snapshot.get(side) is None:
                        detail = f"Cannot freeze {side} joints: joint feedback unavailable."
                        timing = _finish("error", 0, last_error=f"{side} joint feedback unavailable")
                        _log_execution("failed", 0, executed_actions, timing=timing, error_code="INFER-MASK-NOFEEDBACK", error=detail)
                        return _result(
                            False,
                            "INFER-MASK-NOFEEDBACK",
                            detail,
                            executionTiming=timing,
                        )

            # Fully disabled arms are held in place once (smoother freezes them).
            hold_sides = [side for side in ("left", "right") if not mask[side]["enabled"]]
            if hold_sides:
                hold_payload = {"hold": True}
                for side in hold_sides:
                    hold_payload[side] = True
                self._joint_publisher(hold_payload)

            # Lift is a blocking service call, so send at most one target (the
            # final step's height) asynchronously and never gate the step loop.
            if mask["lift"]:
                self._dispatch_lift(steps[:n])

            executed = 0
            for index in range(n):
                if self._stop_event.is_set():
                    self._safe_hold()
                    timing = _finish("stopped", executed)
                    _log_execution("stopped", executed, executed_actions, timing=timing, error_code="INFER-STOPPED", error="Stopped before publishing next step.")
                    return _result(
                        False,
                        "INFER-STOPPED",
                        "Execution stopped before completing the requested steps.",
                        executedSteps=executed,
                        requestedSteps=n,
                        executionTiming=timing,
                    )
                step = steps[index]
                publish_started = time.perf_counter()
                if first_publish_started is None:
                    first_publish_started = publish_started
                publish_start_times.append(publish_started)
                publish_result = self._publish_step(step, joint_speed, mask, snapshot)
                publish_durations_ms.append((time.perf_counter() - publish_started) * 1000.0)
                step_action = publish_result.get("action")
                if step_action is not None:
                    step_action = dict(step_action)
                    step_action["stepIndex"] = index
                if not publish_result.get("ok"):
                    logged_actions = list(executed_actions)
                    if step_action is not None:
                        step_action["published"] = False
                        step_action["error"] = publish_result.get("detail")
                        logged_actions.append(step_action)
                    self._safe_hold()
                    timing = _finish("error", executed, last_error=publish_result.get("detail"))
                    _log_execution(
                        "failed",
                        executed,
                        logged_actions,
                        timing=timing,
                        error_code=publish_result.get("code", "INFER-EXEC-FAILED"),
                        error=publish_result.get("detail", "Failed to publish an action step."),
                    )
                    return _result(
                        False,
                        "INFER-EXEC-FAILED",
                        publish_result.get("detail", "Failed to publish an action step."),
                        executedSteps=executed,
                        requestedSteps=n,
                        executionTiming=timing,
                    )
                if step_action is not None:
                    step_action["published"] = True
                    executed_actions.append(step_action)
                executed += 1
                with self._state_lock:
                    self._executed_steps = executed
                if index < n - 1:
                    if self._stop_event.wait(interval):
                        self._safe_hold()
                        timing = _finish("stopped", executed)
                        _log_execution("stopped", executed, executed_actions, timing=timing, error_code="INFER-STOPPED", error="Stopped after publishing step.")
                        return _result(
                            False,
                            "INFER-STOPPED",
                            "Execution stopped before completing the requested steps.",
                            executedSteps=executed,
                            requestedSteps=n,
                            executionTiming=timing,
                        )

            timing = _finish("chunk_ready", executed)
            _log_execution("completed", executed, executed_actions, timing=timing)
            return _result(
                True,
                "INFER-EXECUTED",
                f"Executed {executed} of {len(steps)} steps.",
                executedSteps=executed,
                requestedSteps=n,
                frequencyHz=frequency,
                maxJointSpeedDegS=joint_speed,
                executionTiming=timing,
            )
        finally:
            self._op_lock.release()

    def _build_step_payloads(self, step, joint_speed, mask, snapshot):
        joint_payload = {"max_joint_speed_deg_s": joint_speed}
        action = {}
        for side in ("left", "right"):
            side_mask = mask[side]
            if not side_mask["enabled"]:
                action[side] = {"held": True}
                continue  # held separately; do not publish a new target
            positions = list(step[side])
            snap = snapshot.get(side)
            if snap is not None:
                for joint_index in range(6):
                    if not side_mask["joints"][joint_index]:
                        positions[joint_index] = snap[joint_index]
                if not side_mask["gripper"]:
                    positions[6] = snap[6]
            joint_payload[side] = {"positions": positions}
            action[side] = {
                "positions": positions,
                "maskedJoints": [
                    index + 1
                    for index, enabled in enumerate(side_mask["joints"])
                    if not enabled
                ],
                "maskedGripper": not side_mask["gripper"],
            }

        if mask["speed"]:
            vx, vy, wz = step["speed"]
        else:
            vx, vy, wz = 0.0, 0.0, 0.0
        chassis_payload = {"linearX": vx, "linearY": vy, "angularZ": wz}
        action["speed"] = {"vx": vx, "vy": vy, "wz": wz, "masked": not mask["speed"]}
        if mask["lift"] and step.get("lift_height") is not None:
            action["lift"] = {"height": step["lift_height"]}
        elif not mask["lift"]:
            action["lift"] = {"masked": True}
        else:
            action["lift"] = None
        return joint_payload, chassis_payload, action

    def _publish_step(self, step, joint_speed, mask, snapshot):
        joint_payload, chassis_payload, action = self._build_step_payloads(step, joint_speed, mask, snapshot)

        if "left" in joint_payload or "right" in joint_payload:
            joint_result = self._joint_publisher(joint_payload)
            if not joint_result.get("ok"):
                return _result(
                    False,
                    joint_result.get("code", "INFER-EXEC-FAILED"),
                    joint_result.get("detail", "Joint publish failed."),
                    action=action,
                )

        chassis_result = self._chassis_publisher(chassis_payload)
        if not chassis_result.get("ok"):
            return _result(
                False,
                chassis_result.get("code", "INFER-EXEC-FAILED"),
                chassis_result.get("detail", "Chassis publish failed."),
                action=action,
            )
        return _result(True, "INFER-STEP", "Step published.", action=action)

    def _dispatch_lift(self, steps):
        target = None
        for step in steps:
            if step.get("lift_height") is not None:
                target = step["lift_height"]
        if target is None:
            return
        if self._last_lift_sent is not None and abs(target - self._last_lift_sent) < LIFT_MIN_DELTA_M:
            return
        self._last_lift_sent = target

        def _move():
            try:
                self._lift_mover({"height": target})
            except Exception:
                pass

        thread = threading.Thread(target=_move, name="inference-lift", daemon=True)
        self._lift_thread = thread
        thread.start()

    # --------------------------------------------------------------------- stop
    def stop(self, reason="stop"):
        self._stop_event.set()
        hold = self._safe_hold()
        self._set(status="stopped", last_error=None)
        return _result(True, "INFER-STOPPED", f"Inference stopped ({reason}).", actions=hold)

    def _safe_hold(self):
        """Bring the robot to a safe state: hold arms, zero chassis, stop lift."""
        actions = {}
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
        self._last_lift_sent = None
        return actions

    def disconnect(self):
        self.stop(reason="disconnect")
        try:
            self._session.close()
        except RemoteSessionError:
            pass
        self._reset_chunk_ids()
        self._set(
            status="disconnected",
            last_chunk=None,
            last_chunk_timing=None,
            last_execution_timing=None,
            last_execution_completed_at=None,
            executed_steps=0,
        )
        return _result(True, "INFER-DISCONNECTED", "Disconnected from remote inference server.")


_manager = None
_manager_lock = threading.Lock()


def get_inference_manager():
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = InferenceManager()
        return _manager
