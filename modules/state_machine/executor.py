"""State machine executor.

The executor walks a saved editor graph and dispatches task nodes to existing
robot modules. Task handlers are still implemented one by one; navigation is
the first real handler.

API contract (served by backend/server.py):

- GET  /api/state-machine/run/status
    -> {ok, code, detail, run: {
         active: bool,
         status: "idle" | "running" | "completed" | "failed" | "stopped",
         graphName: str,
         currentId: str | None,        # node currently executing
         completedIds: [str],          # nodes finished in this run
         edgePath: [{"from": str, "to": str}],  # edges taken, for UI highlight
         path: [str],                  # node ids visited in order
         error: str,                   # failure reason when status == "failed"
         taskStatus: dict | None,      # current task status wrapper
	       }}

- POST /api/state-machine/run/start   body: {name: str, nodes: [node]}
    Node shape matches the editor snapshot (id/type/taskType/title/params/outgoingIds).
	    Returns the same result shape.

- POST /api/state-machine/run/stop
	    Stops the current run.

Execution semantics (agreed, to implement):
- Walk the graph from sm_start; multiple outgoingIds -> random choice.
- Any task failure stops the whole run (status "failed", node reported in
  currentId, reason in error). Manual chassis override interrupting
  navigation also fails the run. No retry, no failure branches in v1.
- Task dispatch (all in-process, reusing existing managers):
    navigation       -> modules.navigation get_navigation_manager().start(params)
                        then poll status() until completed/failed.
                        params: {targetName, x, y, yawDeg, mode}
    reset_odom       -> modules.control.chassis.reset_chassis_odometry({})
                        once, no params.
    wait             -> waits until arm/gripper feedback has moved once and
                        then stayed stable for params: {stableSec}
    grasp(inference) -> modules.inference manager (remote WS inference).
                        params: {graspMethod: "inference", leftTarget,
                                 rightTarget, prompt}
    grasp(auto)      -> end-effector pose grasp (fake interface for now).
                        params: {graspMethod: "auto", leftTarget, rightTarget,
                                 leftPose, rightPose}
                        pose format: "x, y, z, roll, pitch, yaw"
"""

import copy
import math
import random
import threading
import time

from modules.control.chassis import reset_chassis_odometry
from modules.control.piper.feedback import joint_state_key_candidates, read_joint_state_candidate
from modules.navigation import get_navigation_manager
from modules.ros_io import get_ros_reader, get_ros_writer

_EXECUTOR = None
_EXECUTOR_LOCK = threading.Lock()
_TERMINAL_RUN_STATUSES = {"completed", "failed", "stopped"}
_TERMINAL_NAVIGATION_STATUSES = {"completed", "failed", "stopped"}
WAIT_LEFT_JOINT_STATE_KEYS = joint_state_key_candidates(
    "left",
    list_env="STATE_MACHINE_WAIT_LEFT_JOINT_STATE_KEYS",
    single_env="STATE_MACHINE_WAIT_LEFT_JOINT_STATE_KEY",
)
WAIT_RIGHT_JOINT_STATE_KEYS = joint_state_key_candidates(
    "right",
    list_env="STATE_MACHINE_WAIT_RIGHT_JOINT_STATE_KEYS",
    single_env="STATE_MACHINE_WAIT_RIGHT_JOINT_STATE_KEY",
)
WAIT_LEFT_JOINT_STATE_KEY = WAIT_LEFT_JOINT_STATE_KEYS[0]
WAIT_RIGHT_JOINT_STATE_KEY = WAIT_RIGHT_JOINT_STATE_KEYS[0]
WAIT_JOINT_READ_WAIT_SEC = 0.2
WAIT_MIN_STABLE_SEC = 0.1
WAIT_JOINT_MOVE_EPS_RAD = 0.01
WAIT_JOINT_STABLE_EPS_RAD = 0.003
WAIT_GRIPPER_MOVE_EPS_M = 0.002
WAIT_GRIPPER_STABLE_EPS_M = 0.001


def _result(ok, code, detail, **extra):
    payload = {"ok": ok, "code": code, "detail": detail}
    payload.update(extra)
    return payload


def _idle_run():
    return {
        "active": False,
        "status": "idle",
        "graphName": "",
        "currentId": None,
        "completedIds": [],
        "edgePath": [],
        "path": [],
        "error": "",
        "taskStatus": None,
    }


def _now_text():
    return time.strftime("%H:%M:%S")


def _node_title(node):
    return str(node.get("title") or node.get("id") or "")


def _finite_float(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a number.")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number.") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{field} must be finite.")
    return parsed


class StateMachineExecutor:
    """Walks a state machine graph and dispatches each task to robot modules.

    Navigation is implemented first; the other task types intentionally fail at
    runtime until their final semantics are defined.
    """

    def __init__(self, poll_interval_sec=0.2):
        self._lock = threading.Lock()
        self._run = _idle_run()
        self._worker = None
        self._stop_event = threading.Event()
        self._poll_interval_sec = poll_interval_sec

    # ----- public API -----

    def status(self):
        with self._lock:
            return _result(True, "SM-RUN-STATUS", "State machine run status.", run=copy.deepcopy(self._run))

    def start(self, payload):
        """Validate the graph, spawn the worker thread, return immediately."""
        if not isinstance(payload, dict):
            return _result(False, "SM-RUN-PAYLOAD", "Request body must be a JSON object.")
        nodes = payload.get("nodes")
        if not isinstance(nodes, list):
            return _result(False, "SM-RUN-PAYLOAD", "nodes must be a JSON array.")
        name = str(payload.get("name") or "未命名状态机")

        with self._lock:
            if self._run.get("active"):
                return _result(False, "SM-RUN-BUSY", "State machine is already running.", run=copy.deepcopy(self._run))
            self._stop_event.clear()
            self._run = _idle_run()
            self._run.update(
                {
                    "active": True,
                    "status": "running",
                    "graphName": name,
                    "currentId": "sm_start",
                    "path": ["sm_start"],
                    "error": "",
                    "taskStatus": None,
                }
            )
            worker_nodes = copy.deepcopy(nodes)
            thread = threading.Thread(
                target=self._run_loop,
                args=(name, worker_nodes),
                name="robot_station_state_machine",
                daemon=True,
            )
            self._worker = thread
            thread.start()
            return _result(True, "SM-RUN-STARTED", "State machine run started.", run=copy.deepcopy(self._run))

    def stop(self):
        """Signal the worker to stop after the current task aborts."""
        with self._lock:
            if not self._run.get("active"):
                return _result(True, "SM-RUN-NOTRUNNING", "State machine is not running.", run=copy.deepcopy(self._run))
            self._stop_event.set()
            current_node_id = self._run.get("currentId")
            task_status = self._run.get("taskStatus") or {}

        if task_status.get("taskType") == "navigation":
            get_navigation_manager().stop(detail="State machine stopped navigation.")

        self._finish_run(
            "stopped",
            "State machine run stopped.",
            current_id=current_node_id,
            task_status=self._task_status_from_existing(task_status, "stopped", "State machine run stopped."),
        )
        return _result(True, "SM-RUN-STOPPED", "State machine run stopped.", run=self.status()["run"])

    # ----- run loop -----

    def _run_loop(self, name, nodes):
        """Walk the graph from sm_start; random choice on multiple outgoing."""
        nodes_by_id = {str(node.get("id")): node for node in nodes if isinstance(node, dict) and node.get("id")}
        current_id = "sm_start"
        visited = set()

        while True:
            if self._stop_event.is_set():
                self._finish_run("stopped", "State machine run stopped.", current_id=current_id)
                return

            node = nodes_by_id.get(current_id)
            if node is None:
                self._fail_run(f"State not found: {current_id}", current_id=current_id)
                return

            self._set_current_node(current_id)
            if current_id in visited and current_id != "sm_end":
                self._fail_run(f"Cycle detected at state: {_node_title(node) or current_id}", current_id=current_id)
                return
            visited.add(current_id)

            node_type = node.get("type")
            if node_type == "end" or current_id == "sm_end":
                self._mark_node_completed(current_id)
                self._finish_run("completed", "State machine run completed.", current_id=None)
                return

            if node_type != "start":
                outcome, detail = self._execute_task(node)
                if outcome == "stopped":
                    self._finish_run("stopped", detail or "State machine run stopped.", current_id=current_id)
                    return
                if outcome != "completed":
                    self._fail_run(detail or f"State failed: {_node_title(node) or current_id}", current_id=current_id)
                    return

            self._mark_node_completed(current_id)
            outgoing_ids = [str(item) for item in node.get("outgoingIds") or []]
            if not outgoing_ids:
                self._fail_run(f"State has no outgoing edge: {_node_title(node) or current_id}", current_id=current_id)
                return
            next_id = random.choice(outgoing_ids)
            self._mark_edge_taken(current_id, next_id)
            current_id = next_id

    def _execute_task(self, node):
        task_type = str(node.get("taskType") or "")
        if task_type == "navigation":
            return self._execute_navigation(node)
        if task_type == "reset_odom":
            return self._execute_reset_odom(node)
        if task_type == "wait":
            return self._execute_wait(node)
        if task_type == "topic_wait":
            return self._execute_topic_wait(node)
        if task_type == "topic_publish":
            return self._execute_topic_publish(node)
        if task_type == "grasp":
            params = node.get("params") or {}
            if params.get("graspMethod") == "auto":
                return self._execute_grasp_auto(params)
            return self._execute_grasp_inference(params)
        return "failed", f"Unsupported task type: {task_type or 'unknown'}"

    # ----- task handlers, implemented one by one -----

    def _execute_navigation(self, node):
        """Drive the chassis to params x/y/yawDeg via NavigationManager."""
        manager = get_navigation_manager()
        params = node.get("params") or {}
        start_result = manager.start(params)
        self._set_task_status(node, start_result.get("status") or "starting", start_result.get("detail", ""), start_result)
        if not start_result.get("ok"):
            return "failed", start_result.get("detail") or start_result.get("code") or "Navigation failed to start."

        while not self._stop_event.is_set():
            status_result = manager.status()
            nav_status = str(status_result.get("status") or "")
            self._set_task_status(node, nav_status or "running", status_result.get("detail", ""), status_result)
            if nav_status in _TERMINAL_NAVIGATION_STATUSES:
                if nav_status == "completed":
                    return "completed", status_result.get("detail", "Navigation completed.")
                if nav_status == "stopped" and self._stop_event.is_set():
                    return "stopped", status_result.get("detail", "Navigation stopped.")
                detail = (
                    status_result.get("lastError")
                    or status_result.get("detail")
                    or f"Navigation ended with status: {nav_status}."
                )
                return "failed", detail
            time.sleep(self._poll_interval_sec)

        manager.stop(detail="State machine stopped navigation.")
        status_result = manager.status()
        self._set_task_status(node, "stopped", status_result.get("detail", "State machine stopped navigation."), status_result)
        return "stopped", "State machine run stopped."

    def _execute_reset_odom(self, node):
        """Reset chassis odometry once via the existing /reset_odom Trigger service."""
        self._set_task_status(
            node,
            "running",
            "Resetting chassis odometry.",
            {"phase": "calling_service", "action": "reset_odom"},
        )
        result = reset_chassis_odometry({})
        detail = result.get("detail") or result.get("code") or "Chassis odometry reset finished."
        data = copy.deepcopy(result)
        data["phase"] = "completed" if result.get("ok") else "failed"
        if result.get("ok"):
            self._set_task_status(node, "completed", detail, data)
            return "completed", detail
        self._set_task_status(node, "failed", detail, data)
        return "failed", detail

    def _execute_wait(self, node):
        """Wait for arm/gripper motion, then require continuous stillness."""
        params = node.get("params") or {}
        try:
            stable_sec = _finite_float(params.get("stableSec"), "stableSec")
        except ValueError as exc:
            detail = f"Wait stableSec is invalid: {exc}"
            self._set_task_status(node, "failed", detail, {"phase": "failed", "stableSec": params.get("stableSec")})
            return "failed", detail
        if stable_sec < WAIT_MIN_STABLE_SEC:
            detail = f"Wait stableSec must be >= {WAIT_MIN_STABLE_SEC:g}s."
            self._set_task_status(node, "failed", detail, {"phase": "failed", "stableSec": stable_sec})
            return "failed", detail

        reader = get_ros_reader()
        try:
            entry = self._read_wait_joint_positions(reader)
        except ValueError as exc:
            detail = f"Wait joint feedback unavailable: {exc}"
            self._set_task_status(node, "failed", detail, self._wait_status_data("failed", stable_sec))
            return "failed", detail

        previous = entry
        moved = False
        stable_since = None
        stable_elapsed = 0.0
        self._set_task_status(
            node,
            "running",
            "Waiting for arm or gripper movement.",
            self._wait_status_data("waiting_motion", stable_sec),
        )

        while not self._stop_event.is_set():
            try:
                current = self._read_wait_joint_positions(reader)
            except ValueError as exc:
                detail = f"Wait joint feedback unavailable: {exc}"
                self._set_task_status(node, "failed", detail, self._wait_status_data("failed", stable_sec))
                return "failed", detail

            now = time.monotonic()
            entry_delta = self._wait_snapshot_delta(entry, current)
            frame_delta = self._wait_snapshot_delta(previous, current)
            frame_moving = (
                frame_delta["maxDeltaRad"] > WAIT_JOINT_STABLE_EPS_RAD
                or frame_delta["maxGripperDeltaM"] > WAIT_GRIPPER_STABLE_EPS_M
            )

            if not moved:
                moved = (
                    entry_delta["maxDeltaRad"] >= WAIT_JOINT_MOVE_EPS_RAD
                    or entry_delta["maxGripperDeltaM"] >= WAIT_GRIPPER_MOVE_EPS_M
                )

            if not moved:
                phase = "waiting_motion"
                detail = "Waiting for arm or gripper movement."
                stable_since = None
                stable_elapsed = 0.0
            elif frame_moving:
                phase = "moving"
                detail = "Arm or gripper is moving."
                stable_since = None
                stable_elapsed = 0.0
            else:
                phase = "stable_timing"
                if stable_since is None:
                    stable_since = now
                stable_elapsed = now - stable_since
                detail = f"Arm and gripper stable for {stable_elapsed:.1f}/{stable_sec:.1f}s."
                if stable_elapsed >= stable_sec:
                    data = self._wait_status_data(
                        "completed",
                        stable_sec,
                        stable_elapsed=stable_elapsed,
                        max_delta_rad=frame_delta["maxDeltaRad"],
                        max_gripper_delta_m=frame_delta["maxGripperDeltaM"],
                    )
                    self._set_task_status(node, "completed", "Wait stability condition reached.", data)
                    return "completed", "Wait stability condition reached."

            data = self._wait_status_data(
                phase,
                stable_sec,
                stable_elapsed=stable_elapsed,
                max_delta_rad=frame_delta["maxDeltaRad"],
                max_gripper_delta_m=frame_delta["maxGripperDeltaM"],
            )
            self._set_task_status(node, "running", detail, data)
            previous = current
            time.sleep(self._poll_interval_sec)

        self._set_task_status(
            node,
            "stopped",
            "State machine run stopped.",
            self._wait_status_data("stopped", stable_sec, stable_elapsed=stable_elapsed),
        )
        return "stopped", "State machine run stopped."

    def _execute_topic_wait(self, node):
        """Wait until a configured ROS topic receives the next message."""
        params = node.get("params") or {}
        topic_name = self._topic_param(params, ("topicName", "topic"))
        topic_key = self._topic_param(params, ("topicKey", "readKey", "key"))
        signal_target = topic_name or topic_key
        if not signal_target:
            detail = "Topic wait requires topicName."
            self._set_task_status(node, "failed", detail, self._topic_wait_status_data("failed", signal_target))
            return "failed", detail

        try:
            timeout_sec = self._nonnegative_float(params.get("timeoutSec", 0), "timeoutSec")
        except ValueError as exc:
            detail = f"Topic wait timeoutSec is invalid: {exc}"
            self._set_task_status(node, "failed", detail, self._topic_wait_status_data("failed", signal_target))
            return "failed", detail

        reader = get_ros_reader()
        if topic_name:
            baseline = reader.read_bool_topic(topic_name, timeout_sec=0.0)
        else:
            baseline = reader.read(topic_key, timeout_sec=0.0)
        if not baseline.get("ok") and baseline.get("code") != "ROS-R-NODATA":
            detail = baseline.get("detail") or baseline.get("code") or f"Topic wait failed to subscribe: {signal_target}"
            self._set_task_status(node, "failed", detail, self._topic_wait_status_data("failed", signal_target, baseline))
            return "failed", detail

        after_sequence = baseline.get("sequence") if baseline.get("ok") else None
        topic_data = self._topic_wait_status_data("waiting_message", signal_target, baseline, after_sequence=after_sequence)
        self._set_task_status(node, "running", f"Waiting for message on {signal_target}.", topic_data)

        deadline = time.monotonic() + timeout_sec if timeout_sec > 0 else None
        while not self._stop_event.is_set():
            wait_sec = self._poll_interval_sec
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    detail = f"Topic wait timed out: {signal_target}"
                    data = self._topic_wait_status_data("failed", signal_target, baseline, after_sequence=after_sequence)
                    self._set_task_status(node, "failed", detail, data)
                    return "failed", detail
                wait_sec = min(wait_sec, remaining)

            if topic_name:
                result = reader.read_bool_topic_after(topic_name, after_sequence=after_sequence, timeout_sec=wait_sec)
            else:
                result = reader.read_after(topic_key, after_sequence=after_sequence, timeout_sec=wait_sec)
            if result.get("ok"):
                data = self._topic_wait_status_data("completed", signal_target, result, after_sequence=after_sequence)
                self._set_task_status(node, "completed", f"Received message on {result.get('topic') or topic_key}.", data)
                return "completed", f"Received message on {result.get('topic') or topic_key}."
            if result.get("code") != "ROS-R-NODATA":
                detail = result.get("detail") or result.get("code") or f"Topic wait failed: {signal_target}"
                data = self._topic_wait_status_data("failed", signal_target, result, after_sequence=after_sequence)
                self._set_task_status(node, "failed", detail, data)
                return "failed", detail

            data = self._topic_wait_status_data("waiting_message", signal_target, result, after_sequence=after_sequence)
            self._set_task_status(node, "running", f"Waiting for message on {result.get('topic') or signal_target}.", data)

        self._set_task_status(
            node,
            "stopped",
            "State machine run stopped.",
            self._topic_wait_status_data("stopped", signal_target, baseline, after_sequence=after_sequence),
        )
        return "stopped", "State machine run stopped."

    def _execute_topic_publish(self, node):
        """Publish a true Bool signal through the configured ROS topic."""
        params = node.get("params") or {}
        topic_name = self._topic_param(params, ("topicName", "topic"))
        action_key = self._topic_param(params, ("actionKey", "writeKey", "key"))
        signal_target = topic_name or action_key
        if not signal_target:
            detail = "Topic publish requires topicName."
            self._set_task_status(node, "failed", detail, self._topic_publish_status_data("failed", signal_target))
            return "failed", detail

        payload = {"data": True}
        self._set_task_status(
            node,
            "running",
            f"Publishing true to {signal_target}.",
            self._topic_publish_status_data("publishing", signal_target, payload=payload),
        )
        writer = get_ros_writer()
        result = writer.publish_bool_topic(topic_name, True) if topic_name else writer.publish(action_key, payload)
        detail = result.get("detail") or result.get("code") or f"Published true to {signal_target}."
        phase = "completed" if result.get("ok") else "failed"
        data = self._topic_publish_status_data(phase, signal_target, result, payload=payload)
        if result.get("ok"):
            self._set_task_status(node, "completed", detail, data)
            return "completed", detail
        self._set_task_status(node, "failed", detail, data)
        return "failed", detail

    def _read_wait_joint_positions(self, reader):
        snapshot = {"joints": [], "grippers": []}
        for side, keys in (("left", WAIT_LEFT_JOINT_STATE_KEYS), ("right", WAIT_RIGHT_JOINT_STATE_KEYS)):
            try:
                _, _, positions = read_joint_state_candidate(
                    reader,
                    side,
                    keys,
                    timeout_sec=WAIT_JOINT_READ_WAIT_SEC,
                    min_positions=7,
                    accept_stale=False,
                )
            except Exception as exc:
                raise ValueError(str(exc)) from exc
            parsed = [_finite_float(value, f"{side}.position[{index}]") for index, value in enumerate(positions[:7])]
            snapshot["joints"].extend(parsed[:6])
            snapshot["grippers"].append(parsed[6])
        return snapshot

    @staticmethod
    def _wait_snapshot_delta(previous, current):
        joint_deltas = [abs(a - b) for a, b in zip(previous["joints"], current["joints"])]
        gripper_deltas = [abs(a - b) for a, b in zip(previous["grippers"], current["grippers"])]
        return {
            "maxDeltaRad": max(joint_deltas) if joint_deltas else 0.0,
            "maxGripperDeltaM": max(gripper_deltas) if gripper_deltas else 0.0,
        }

    @staticmethod
    def _wait_status_data(phase, stable_sec, stable_elapsed=0.0, max_delta_rad=0.0, max_gripper_delta_m=0.0):
        return {
            "phase": phase,
            "stableSec": stable_sec,
            "stableElapsedSec": stable_elapsed,
            "maxDeltaRad": max_delta_rad,
            "maxGripperDeltaM": max_gripper_delta_m,
        }

    @staticmethod
    def _topic_param(params, keys):
        for key in keys:
            if key in params:
                value = str(params.get(key) or "").strip()
                return value
        return ""

    @staticmethod
    def _nonnegative_float(value, field):
        parsed = _finite_float(value, field)
        if parsed < 0:
            raise ValueError(f"{field} must be >= 0.")
        return parsed

    @staticmethod
    def _topic_wait_status_data(phase, topic_key, result=None, after_sequence=None):
        result = result or {}
        return {
            "phase": phase,
            "key": topic_key,
            "topic": result.get("topic", ""),
            "messageType": result.get("messageType", ""),
            "code": result.get("code", ""),
            "sequence": result.get("sequence"),
            "afterSequence": after_sequence,
            "receivedAt": result.get("receivedAt", ""),
            "ageMs": result.get("ageMs"),
            "stale": result.get("stale"),
            "data": copy.deepcopy(result.get("data")) if "data" in result else None,
        }

    @staticmethod
    def _topic_publish_status_data(phase, action_key, result=None, payload=None):
        result = result or {}
        return {
            "phase": phase,
            "key": action_key,
            "topic": result.get("topic", ""),
            "messageType": result.get("messageType", ""),
            "code": result.get("code", ""),
            "publishedAt": result.get("publishedAt", ""),
            "payload": copy.deepcopy(payload) if payload is not None else None,
        }

    def _execute_grasp_inference(self, params):
        """Remote inference grasp; left/right targets + prompt."""
        return "failed", "Inference grasp task is not implemented yet."

    def _execute_grasp_auto(self, params):
        """End-effector pose grasp (fake interface for now)."""
        return "failed", "Auto grasp task is not implemented yet."

    # ----- run state helpers -----

    def _set_current_node(self, node_id):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return
            self._run["currentId"] = node_id
            if not self._run["path"] or self._run["path"][-1] != node_id:
                self._run["path"].append(node_id)

    def _mark_node_completed(self, node_id):
        with self._lock:
            if node_id not in self._run["completedIds"]:
                self._run["completedIds"].append(node_id)

    def _mark_edge_taken(self, from_id, to_id):
        with self._lock:
            self._run["edgePath"].append({"from": from_id, "to": to_id})
            self._run["currentId"] = to_id
            if not self._run["path"] or self._run["path"][-1] != to_id:
                self._run["path"].append(to_id)

    def _task_status_payload(self, node, status, detail="", data=None):
        return {
            "nodeId": str(node.get("id") or ""),
            "taskType": str(node.get("taskType") or ""),
            "title": _node_title(node),
            "status": str(status or ""),
            "detail": str(detail or ""),
            "updatedAt": _now_text(),
            "data": copy.deepcopy(data) if data is not None else None,
        }

    def _set_task_status(self, node, status, detail="", data=None):
        task_status = self._task_status_payload(node, status, detail, data)
        with self._lock:
            self._run["taskStatus"] = task_status

    def _task_status_from_existing(self, task_status, status, detail):
        if not task_status:
            return None
        updated = copy.deepcopy(task_status)
        updated.update({"status": status, "detail": detail, "updatedAt": _now_text()})
        return updated

    def _finish_run(self, status, detail, current_id=None, task_status=None):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES and self._run.get("status") != "running":
                return
            self._run.update(
                {
                    "active": False,
                    "status": status,
                    "currentId": current_id,
                    "error": detail if status == "failed" else "",
                }
            )
            if task_status is not None:
                self._run["taskStatus"] = task_status

    def _fail_run(self, detail, current_id=None):
        task_status = None
        with self._lock:
            existing = self._run.get("taskStatus") or {}
            if existing.get("nodeId") == current_id:
                task_status = self._task_status_from_existing(existing, "failed", detail)
        self._finish_run("failed", detail, current_id=current_id, task_status=task_status)


def get_state_machine_executor():
    global _EXECUTOR
    with _EXECUTOR_LOCK:
        if _EXECUTOR is None:
            _EXECUTOR = StateMachineExecutor()
        return _EXECUTOR
