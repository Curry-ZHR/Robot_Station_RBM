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
         loop: bool,                   # true for continuous repeat mode
         iteration: int,               # current 1-based loop iteration
         completedIterations: int,     # full start->end passes completed
         error: str,                   # failure reason when status == "failed"
         taskStatus: dict | None,      # current task status wrapper
       }}

- POST /api/state-machine/run/start   body: {name: str, nodes: [node]}
    Node shape matches the editor snapshot (id/type/taskType/title/params/outgoingIds).
    Optional loop: true keeps restarting from sm_start after sm_end until stopped.
    Returns the same result shape.

- POST /api/state-machine/run/stop
    Stops the current run.

Execution semantics (agreed, to implement):
- Walk the graph from sm_start; multiple outgoingIds -> random choice.
- Any task failure stops the whole run (status "failed", node reported in
  currentId, reason in error). Manual chassis override interrupting
  navigation also fails the run. No retry, no failure branches in v1.
- Task dispatch (all in-process, reusing existing managers):
    navigation       -> resolve optional uniform x/y/yaw target noise once,
                        then modules.navigation get_navigation_manager().start(params)
                        then poll status() until completed/failed.
                        params: {targetName, x, y, yawDeg, mode,
                                 targetNoiseMode, xNoiseMinM, xNoiseMaxM,
                                 yNoiseMinM, yNoiseMaxM,
                                 yawNoiseMinDeg, yawNoiseMaxDeg}
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
from modules.control.piper import publish_joint_targets
from modules.control.piper.feedback import joint_state_key_candidates, read_joint_state_candidate
from modules.inference import get_inference_manager
from modules.navigation import get_navigation_manager
from modules.ros_io import get_ros_reader, get_ros_writer

_EXECUTOR = None
_EXECUTOR_LOCK = threading.Lock()
_TERMINAL_RUN_STATUSES = {"completed", "failed", "stopped"}
_TERMINAL_NAVIGATION_STATUSES = {"completed", "failed", "stopped"}
NAVIGATION_TARGET_NOISE_NONE = "none"
NAVIGATION_TARGET_NOISE_UNIFORM = "uniform"
LOOP_RESTART_PAUSE_SEC = 0.05
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
PIPER_JOINT_DEFAULT_SPEED_DEG_S = 5.0
PIPER_JOINT_MIN_SPEED_DEG_S = 0.5
PIPER_JOINT_MAX_SPEED_DEG_S = 30.0
PIPER_JOINT_DEFAULT_GRIPPER_EFFORT = 1.0
PIPER_JOINT_MIN_GRIPPER_EFFORT = 0.5
PIPER_JOINT_MAX_GRIPPER_EFFORT = 3.0
PIPER_JOINT_DEFAULT_TOLERANCE_DEG = 2.0
PIPER_JOINT_MIN_TOLERANCE_DEG = 0.01
PIPER_JOINT_MAX_TOLERANCE_DEG = 30.0
PIPER_JOINT_DEFAULT_GRIPPER_TOLERANCE_M = 0.005
PIPER_JOINT_MIN_GRIPPER_TOLERANCE_M = 0.0001
PIPER_JOINT_MAX_GRIPPER_TOLERANCE_M = 0.05
PIPER_JOINT_DEFAULT_STABLE_SEC = 2.0
PIPER_JOINT_MAX_STABLE_SEC = 10.0
PIPER_JOINT_DEFAULT_TIMEOUT_SEC = 20.0
PIPER_JOINT_MIN_TIMEOUT_SEC = 0.1
PIPER_JOINT_MAX_TIMEOUT_SEC = 600.0
INFERENCE_DEFAULT_STEPS = 20
INFERENCE_MIN_STEPS = 1
INFERENCE_MAX_STEPS = 200
INFERENCE_DEFAULT_FREQUENCY_HZ = 10.0
INFERENCE_MIN_FREQUENCY_HZ = 1.0
INFERENCE_MAX_FREQUENCY_HZ = 30.0
INFERENCE_DEFAULT_JOINT_SPEED_DEG_S = 20.0
INFERENCE_MIN_JOINT_SPEED_DEG_S = 0.5
INFERENCE_MAX_JOINT_SPEED_DEG_S = 30.0
INFERENCE_DEFAULT_CHASSIS_LIMITS = {
    "maxLinearMps": 0.2,
    "maxLateralMps": 0.15,
    "maxAngularRadS": 0.5,
}
INFERENCE_PIPER_ENABLE_ACTION_KEY = "piper_enable_all"
INFERENCE_PIPER_ENABLE_REPEAT = 3
INFERENCE_PIPER_ENABLE_INTERVAL_SEC = 0.08


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
        "loop": False,
        "iteration": 0,
        "completedIterations": 0,
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


def _blank(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


def _bounded_float(value, field, default, minimum, maximum):
    parsed = float(default) if _blank(value) else _finite_float(value, field)
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field} must be between {minimum:g} and {maximum:g}.")
    return parsed


def _bounded_int(value, field, default, minimum, maximum):
    parsed_float = float(default) if _blank(value) else _finite_float(value, field)
    parsed = int(parsed_float)
    if parsed != parsed_float:
        raise ValueError(f"{field} must be an integer.")
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field} must be between {minimum:g} and {maximum:g}.")
    return parsed


def _bool_param(value, default=False):
    if _blank(value):
        return bool(default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("1", "true", "yes", "on"):
            return True
        if lowered in ("0", "false", "no", "off"):
            return False
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    return bool(default)


def _normalize_degrees(angle_deg):
    normalized = (angle_deg + 180.0) % 360.0 - 180.0
    return 0.0 if abs(normalized) < 1e-12 else normalized


def _navigation_noise_bounds(params):
    fields = (
        ("x", "xNoiseMinM", "xNoiseMaxM"),
        ("y", "yNoiseMinM", "yNoiseMaxM"),
        ("yawDeg", "yawNoiseMinDeg", "yawNoiseMaxDeg"),
    )
    bounds = {}
    for axis, minimum_key, maximum_key in fields:
        minimum = 0.0 if _blank(params.get(minimum_key)) else _finite_float(params.get(minimum_key), minimum_key)
        maximum = 0.0 if _blank(params.get(maximum_key)) else _finite_float(params.get(maximum_key), maximum_key)
        if minimum > maximum:
            raise ValueError(f"{minimum_key} must be <= {maximum_key}.")
        bounds[axis] = {"min": minimum, "max": maximum}
    return bounds


def _resolve_navigation_target(params, rng):
    command = copy.deepcopy(params)
    if not isinstance(command, dict):
        return command, None
    mode = str(command.get("targetNoiseMode") or NAVIGATION_TARGET_NOISE_NONE).strip().lower()
    if mode == NAVIGATION_TARGET_NOISE_NONE:
        return command, None
    if mode != NAVIGATION_TARGET_NOISE_UNIFORM:
        raise ValueError("targetNoiseMode must be 'none' or 'uniform'.")

    nominal = {
        "x": _finite_float(command.get("x"), "x"),
        "y": _finite_float(command.get("y"), "y"),
        "yawDeg": _finite_float(command.get("yawDeg"), "yawDeg"),
    }
    bounds = _navigation_noise_bounds(command)
    sampled = {
        axis: rng.uniform(axis_bounds["min"], axis_bounds["max"])
        for axis, axis_bounds in bounds.items()
    }
    resolved = {
        "x": nominal["x"] + sampled["x"],
        "y": nominal["y"] + sampled["y"],
        "yawDeg": _normalize_degrees(nominal["yawDeg"] + sampled["yawDeg"]),
    }
    command.update(resolved)
    return command, {
        "targetNoiseMode": NAVIGATION_TARGET_NOISE_UNIFORM,
        "nominalTarget": nominal,
        "sampledNoise": sampled,
        "resolvedTarget": resolved,
        "noiseBounds": bounds,
    }


class StateMachineExecutor:
    """Walks a state machine graph and dispatches each task to robot modules.

    Navigation is implemented first; the other task types intentionally fail at
    runtime until their final semantics are defined.
    """

    def __init__(self, poll_interval_sec=0.2, navigation_noise_rng=None):
        self._lock = threading.Lock()
        self._run = _idle_run()
        self._worker = None
        self._stop_event = threading.Event()
        self._poll_interval_sec = poll_interval_sec
        # Keep target sampling independent from the RNG used for random graph
        # branches so adding noise cannot change which outgoing edge is chosen.
        self._navigation_noise_rng = navigation_noise_rng or random.Random()

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
        loop = payload.get("loop") is True

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
                    "loop": loop,
                    "iteration": 1,
                    "completedIterations": 0,
                    "error": "",
                    "taskStatus": None,
                }
            )
            worker_nodes = copy.deepcopy(nodes)
            thread = threading.Thread(
                target=self._run_loop,
                args=(worker_nodes, loop),
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
        if task_status.get("taskType") == "piper_joint":
            publish_joint_targets({"hold": True})
        if task_status.get("taskType") == "inference":
            get_inference_manager().stop(reason="state_machine")

        self._finish_run(
            "stopped",
            "State machine run stopped.",
            current_id=current_node_id,
            task_status=self._task_status_from_existing(task_status, "stopped", "State machine run stopped."),
        )
        return _result(True, "SM-RUN-STOPPED", "State machine run stopped.", run=self.status()["run"])

    # ----- run loop -----

    def _run_loop(self, nodes, loop=False):
        """Walk the graph from sm_start; random choice on multiple outgoing."""
        nodes_by_id = {str(node.get("id")): node for node in nodes if isinstance(node, dict) and node.get("id")}
        iteration = 1

        while True:
            if not self._begin_iteration(iteration):
                return
            outcome, detail, current_id = self._run_iteration(nodes_by_id)
            if outcome == "completed":
                self._mark_iteration_completed()
                if not loop:
                    self._finish_run("completed", "State machine run completed.", current_id=None)
                    return
                if self._stop_event.wait(LOOP_RESTART_PAUSE_SEC):
                    self._finish_run("stopped", "State machine run stopped.", current_id=None)
                    return
                iteration += 1
                continue
            if outcome == "stopped":
                self._finish_run("stopped", detail or "State machine run stopped.", current_id=current_id)
                return
            self._fail_run(detail or "State machine run failed.", current_id=current_id)
            return

    def _run_iteration(self, nodes_by_id):
        """Run one start-to-end pass. Loop mode restarts this whole pass."""
        current_id = "sm_start"
        visited = set()

        while True:
            if self._stop_event.is_set():
                return "stopped", "State machine run stopped.", current_id

            node = nodes_by_id.get(current_id)
            if node is None:
                return "failed", f"State not found: {current_id}", current_id

            self._set_current_node(current_id)
            if current_id in visited and current_id != "sm_end":
                return "failed", f"Cycle detected at state: {_node_title(node) or current_id}", current_id
            visited.add(current_id)

            node_type = node.get("type")
            if node_type == "end" or current_id == "sm_end":
                self._mark_node_completed(current_id)
                return "completed", "State machine run completed.", None

            if node_type != "start":
                outcome, detail = self._execute_task(node)
                if outcome == "stopped":
                    return "stopped", detail or "State machine run stopped.", current_id
                if outcome != "completed":
                    return "failed", detail or f"State failed: {_node_title(node) or current_id}", current_id

            self._mark_node_completed(current_id)
            outgoing_ids = [str(item) for item in node.get("outgoingIds") or []]
            if not outgoing_ids:
                return "failed", f"State has no outgoing edge: {_node_title(node) or current_id}", current_id
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
        if task_type == "inference":
            return self._execute_inference(node)
        if task_type == "piper_joint":
            return self._execute_piper_joint(node)
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
        try:
            command, target_resolution = _resolve_navigation_target(params, self._navigation_noise_rng)
        except ValueError as exc:
            detail = f"Invalid navigation target noise: {exc}"
            self._set_task_status(
                node,
                "failed",
                detail,
                {"phase": "target_noise_validation", "targetNoiseMode": params.get("targetNoiseMode", NAVIGATION_TARGET_NOISE_NONE)},
            )
            return "failed", detail

        def with_target_resolution(result):
            data = copy.deepcopy(result)
            if target_resolution is not None:
                data.update(copy.deepcopy(target_resolution))
            return data

        start_result = manager.start(command)
        start_data = with_target_resolution(start_result)
        self._set_task_status(node, start_result.get("status") or "starting", start_result.get("detail", ""), start_data)
        if not start_result.get("ok"):
            return "failed", start_result.get("detail") or start_result.get("code") or "Navigation failed to start."

        while not self._stop_event.is_set():
            status_result = manager.status()
            nav_status = str(status_result.get("status") or "")
            status_data = with_target_resolution(status_result)
            self._set_task_status(node, nav_status or "running", status_result.get("detail", ""), status_data)
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
        self._set_task_status(
            node,
            "stopped",
            status_result.get("detail", "State machine stopped navigation."),
            with_target_resolution(status_result),
        )
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
        """Wait until a configured ROS topic receives the next true Bool message."""
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
        topic_data = self._topic_wait_status_data("waiting_true", signal_target, baseline, after_sequence=after_sequence)
        self._set_task_status(node, "running", f"Waiting for true message on {signal_target}.", topic_data)

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
                if not self._topic_wait_result_is_true(result):
                    after_sequence = result.get("sequence", after_sequence)
                    baseline = result
                    data = self._topic_wait_status_data("waiting_true", signal_target, result, after_sequence=after_sequence)
                    self._set_task_status(
                        node,
                        "running",
                        f"Waiting for true message on {result.get('topic') or signal_target}.",
                        data,
                    )
                    continue
                data = self._topic_wait_status_data("completed", signal_target, result, after_sequence=after_sequence)
                self._set_task_status(node, "completed", f"Received true message on {result.get('topic') or topic_key}.", data)
                return "completed", f"Received true message on {result.get('topic') or topic_key}."
            if result.get("code") != "ROS-R-NODATA":
                detail = result.get("detail") or result.get("code") or f"Topic wait failed: {signal_target}"
                data = self._topic_wait_status_data("failed", signal_target, result, after_sequence=after_sequence)
                self._set_task_status(node, "failed", detail, data)
                return "failed", detail

            data = self._topic_wait_status_data("waiting_true", signal_target, result, after_sequence=after_sequence)
            self._set_task_status(node, "running", f"Waiting for true message on {result.get('topic') or signal_target}.", data)

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
    def _topic_wait_result_is_true(result):
        payload = result.get("data")
        if isinstance(payload, dict):
            payload = payload.get("data")
        return payload is True

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

    def _execute_piper_joint(self, node):
        """Publish complete Piper joint targets and wait until feedback reaches them."""
        params = node.get("params") or {}
        try:
            config = self._piper_joint_config(params)
        except ValueError as exc:
            detail = f"Piper joint params invalid: {exc}"
            self._set_task_status(node, "failed", detail, self._piper_joint_status_data("failed"))
            return "failed", detail

        self._set_task_status(
            node,
            "running",
            "Publishing Piper joint target.",
            self._piper_joint_status_data("publishing", config),
        )
        publish_result = publish_joint_targets(config["payload"])
        if not publish_result.get("ok"):
            detail = publish_result.get("detail") or publish_result.get("code") or "Piper joint target publish failed."
            self._set_task_status(
                node,
                "failed",
                detail,
                self._piper_joint_status_data("failed", config, publish_result=publish_result),
            )
            return "failed", detail

        reader = get_ros_reader()
        started = time.monotonic()
        stable_since = None
        stable_elapsed = 0.0
        last_feedback_error = ""
        self._set_task_status(
            node,
            "running",
            "Waiting for Piper joint feedback to reach target.",
            self._piper_joint_status_data("waiting_feedback", config, publish_result=publish_result),
        )

        while not self._stop_event.is_set():
            now = time.monotonic()
            elapsed = now - started
            if elapsed > config["timeoutSec"]:
                detail = f"Piper joint target not reached within {config['timeoutSec']:.1f}s."
                self._set_task_status(
                    node,
                    "failed",
                    detail,
                    self._piper_joint_status_data(
                        "failed",
                        config,
                        publish_result=publish_result,
                        stable_elapsed=stable_elapsed,
                        elapsed=elapsed,
                        last_feedback_error=last_feedback_error,
                    ),
                )
                return "failed", detail

            try:
                feedback = self._read_piper_joint_feedback(reader, config["sides"])
            except ValueError as exc:
                last_feedback_error = str(exc)
                stable_since = None
                stable_elapsed = 0.0
                self._set_task_status(
                    node,
                    "running",
                    "Waiting for Piper joint feedback.",
                    self._piper_joint_status_data(
                        "waiting_feedback",
                        config,
                        publish_result=publish_result,
                        stable_elapsed=stable_elapsed,
                        elapsed=elapsed,
                        last_feedback_error=last_feedback_error,
                    ),
                )
                self._stop_event.wait(self._poll_interval_sec)
                continue

            last_feedback_error = ""
            errors = self._piper_joint_target_errors(config, feedback)
            if errors["withinTolerance"]:
                if stable_since is None:
                    stable_since = now
                stable_elapsed = 0.0 if config["stableSec"] <= 0 else now - stable_since
                if config["stableSec"] <= 0 or stable_elapsed >= config["stableSec"]:
                    detail = "Piper joint target reached."
                    self._set_task_status(
                        node,
                        "completed",
                        detail,
                        self._piper_joint_status_data(
                            "completed",
                            config,
                            publish_result=publish_result,
                            feedback=feedback,
                            errors=errors,
                            stable_elapsed=stable_elapsed,
                            elapsed=elapsed,
                        ),
                    )
                    return "completed", detail
                phase = "stable_timing"
                detail = f"Piper joint target reached, stable for {stable_elapsed:.1f}/{config['stableSec']:.1f}s."
            else:
                stable_since = None
                stable_elapsed = 0.0
                phase = "moving_to_target"
                detail = "Waiting for Piper joint target to be reached."

            self._set_task_status(
                node,
                "running",
                detail,
                self._piper_joint_status_data(
                    phase,
                    config,
                    publish_result=publish_result,
                    feedback=feedback,
                    errors=errors,
                    stable_elapsed=stable_elapsed,
                    elapsed=elapsed,
                ),
            )
            self._stop_event.wait(self._poll_interval_sec)

        hold_result = publish_joint_targets({"hold": True})
        self._set_task_status(
            node,
            "stopped",
            "State machine run stopped.",
            self._piper_joint_status_data("stopped", config, publish_result=publish_result, hold_result=hold_result),
        )
        return "stopped", "State machine run stopped."

    @staticmethod
    def _piper_joint_config(params):
        sides = StateMachineExecutor._piper_joint_sides(params)
        targets = {side: StateMachineExecutor._piper_joint_positions(params, side) for side in sides}
        max_joint_speed = _bounded_float(
            params.get("maxJointSpeedDegS", params.get("max_joint_speed_deg_s")),
            "maxJointSpeedDegS",
            PIPER_JOINT_DEFAULT_SPEED_DEG_S,
            PIPER_JOINT_MIN_SPEED_DEG_S,
            PIPER_JOINT_MAX_SPEED_DEG_S,
        )
        gripper_effort = _bounded_float(
            params.get("gripperEffort", params.get("gripper_effort")),
            "gripperEffort",
            PIPER_JOINT_DEFAULT_GRIPPER_EFFORT,
            PIPER_JOINT_MIN_GRIPPER_EFFORT,
            PIPER_JOINT_MAX_GRIPPER_EFFORT,
        )
        if not _blank(params.get("toleranceRad")):
            tolerance_rad = _bounded_float(params.get("toleranceRad"), "toleranceRad", math.radians(PIPER_JOINT_DEFAULT_TOLERANCE_DEG), 0.0001, math.pi)
            tolerance_deg = math.degrees(tolerance_rad)
        else:
            tolerance_deg = _bounded_float(
                params.get("toleranceDeg"),
                "toleranceDeg",
                PIPER_JOINT_DEFAULT_TOLERANCE_DEG,
                PIPER_JOINT_MIN_TOLERANCE_DEG,
                PIPER_JOINT_MAX_TOLERANCE_DEG,
            )
            tolerance_rad = math.radians(tolerance_deg)
        gripper_tolerance = _bounded_float(
            params.get("gripperToleranceM"),
            "gripperToleranceM",
            PIPER_JOINT_DEFAULT_GRIPPER_TOLERANCE_M,
            PIPER_JOINT_MIN_GRIPPER_TOLERANCE_M,
            PIPER_JOINT_MAX_GRIPPER_TOLERANCE_M,
        )
        stable_sec = _bounded_float(
            params.get("stableSec"),
            "stableSec",
            PIPER_JOINT_DEFAULT_STABLE_SEC,
            0.0,
            PIPER_JOINT_MAX_STABLE_SEC,
        )
        timeout_sec = _bounded_float(
            params.get("timeoutSec"),
            "timeoutSec",
            PIPER_JOINT_DEFAULT_TIMEOUT_SEC,
            PIPER_JOINT_MIN_TIMEOUT_SEC,
            PIPER_JOINT_MAX_TIMEOUT_SEC,
        )
        payload = {
            "max_joint_speed_deg_s": max_joint_speed,
            "gripper_effort": gripper_effort,
        }
        for side, positions in targets.items():
            payload[side] = {"positions": list(positions)}
        return {
            "side": "both" if sides == ["left", "right"] else sides[0],
            "sides": sides,
            "targets": targets,
            "payload": payload,
            "maxJointSpeedDegS": max_joint_speed,
            "gripperEffort": gripper_effort,
            "toleranceRad": tolerance_rad,
            "toleranceDeg": tolerance_deg,
            "gripperToleranceM": gripper_tolerance,
            "stableSec": stable_sec,
            "timeoutSec": timeout_sec,
        }

    @staticmethod
    def _piper_joint_sides(params):
        has_side_param = any(key in params for key in ("side", "arm", "arms", "targetSide"))
        raw = params.get("side", params.get("arm", params.get("arms", params.get("targetSide", ""))))
        if not has_side_param:
            present = [side for side in ("left", "right") if StateMachineExecutor._piper_side_target_present(params, side)]
            if present:
                return present

        value = str(raw or "both").strip().lower()
        aliases = {
            "left": "left",
            "l": "left",
            "左": "left",
            "左臂": "left",
            "right": "right",
            "r": "right",
            "右": "right",
            "右臂": "right",
            "both": "both",
            "all": "both",
            "双臂": "both",
            "左右": "both",
            "左右臂": "both",
        }
        normalized = aliases.get(value)
        if normalized is None:
            raise ValueError("side must be left, right, or both.")
        return ["left", "right"] if normalized == "both" else [normalized]

    @staticmethod
    def _piper_side_target_present(params, side):
        side_payload = params.get(side)
        if isinstance(side_payload, dict) and any(key in side_payload for key in ("positions", "position", "joints")):
            return True
        if any(key in params for key in (f"{side}Positions", f"{side}Position", f"{side}Joints")):
            return True
        return any(key in params for key in StateMachineExecutor._piper_joint_field_keys(side, 1))

    @staticmethod
    def _piper_joint_positions(params, side):
        side_payload = params.get(side)
        if isinstance(side_payload, dict):
            for key in ("positions", "position", "joints"):
                if key in side_payload:
                    return StateMachineExecutor._piper_position_list(side_payload[key], f"{side}.{key}")

        for key in (f"{side}Positions", f"{side}Position", f"{side}Joints"):
            if key in params:
                return StateMachineExecutor._piper_position_list(params[key], key)

        positions = []
        for index in range(1, 7):
            deg = StateMachineExecutor._piper_required_number(
                params,
                StateMachineExecutor._piper_joint_field_keys(side, index),
                f"{side}Joint{index}Deg",
            )
            positions.append(math.radians(deg))
        positions.append(
            StateMachineExecutor._piper_required_number(
                params,
                StateMachineExecutor._piper_gripper_field_keys(side),
                f"{side}GripperM",
            )
        )
        return positions

    @staticmethod
    def _piper_position_list(values, field):
        if not isinstance(values, (list, tuple)):
            raise ValueError(f"{field} must be a list of 7 numbers.")
        parsed = [_finite_float(value, f"{field}[{index}]") for index, value in enumerate(values)]
        if len(parsed) != 7:
            raise ValueError(f"{field} must contain exactly 7 numbers.")
        return parsed

    @staticmethod
    def _piper_required_number(params, keys, field):
        for key in keys:
            if key in params:
                return _finite_float(params.get(key), field)
        raise ValueError(f"{field} is required.")

    @staticmethod
    def _piper_joint_field_keys(side, index):
        return (
            f"{side}Joint{index}Deg",
            f"{side}J{index}Deg",
            f"{side}_joint{index}_deg",
            f"{side}_j{index}_deg",
        )

    @staticmethod
    def _piper_gripper_field_keys(side):
        return (
            f"{side}GripperM",
            f"{side}Gripper",
            f"{side}_gripper_m",
            f"{side}_gripper",
        )

    def _read_piper_joint_feedback(self, reader, sides):
        snapshot = {}
        for side in sides:
            keys = WAIT_LEFT_JOINT_STATE_KEYS if side == "left" else WAIT_RIGHT_JOINT_STATE_KEYS
            try:
                key, result, positions = read_joint_state_candidate(
                    reader,
                    side,
                    keys,
                    timeout_sec=WAIT_JOINT_READ_WAIT_SEC,
                    min_positions=7,
                    accept_stale=False,
                )
            except Exception as exc:
                raise ValueError(str(exc)) from exc
            snapshot[side] = {
                "key": key,
                "topic": result.get("topic", ""),
                "positions": [_finite_float(value, f"{side}.position[{index}]") for index, value in enumerate(positions[:7])],
            }
        return snapshot

    @staticmethod
    def _piper_joint_target_errors(config, feedback):
        side_errors = {}
        max_joint_error = 0.0
        max_gripper_error = 0.0
        within_tolerance = True
        for side in config["sides"]:
            target = config["targets"][side]
            current = feedback[side]["positions"]
            joint_errors = [abs(current[index] - target[index]) for index in range(6)]
            gripper_error = abs(current[6] - target[6])
            side_max_joint_error = max(joint_errors) if joint_errors else 0.0
            side_within = side_max_joint_error <= config["toleranceRad"]
            gripper_within = gripper_error <= config["gripperToleranceM"]
            side_errors[side] = {
                "maxJointErrorRad": side_max_joint_error,
                "maxJointErrorDeg": math.degrees(side_max_joint_error),
                "gripperErrorM": gripper_error,
                "withinTolerance": side_within,
                "gripperWithinTolerance": gripper_within,
            }
            max_joint_error = max(max_joint_error, side_max_joint_error)
            max_gripper_error = max(max_gripper_error, gripper_error)
            within_tolerance = within_tolerance and side_within
        return {
            "withinTolerance": within_tolerance,
            "jointWithinTolerance": within_tolerance,
            "gripperWithinTolerance": max_gripper_error <= config["gripperToleranceM"],
            "maxJointErrorRad": max_joint_error,
            "maxJointErrorDeg": math.degrees(max_joint_error),
            "maxGripperErrorM": max_gripper_error,
            "sideErrors": side_errors,
        }

    @staticmethod
    def _piper_joint_status_data(
        phase,
        config=None,
        publish_result=None,
        hold_result=None,
        feedback=None,
        errors=None,
        stable_elapsed=0.0,
        elapsed=0.0,
        last_feedback_error="",
    ):
        data = {
            "phase": phase,
            "stableElapsedSec": stable_elapsed,
            "elapsedSec": elapsed,
        }
        if config:
            data.update(
                {
                    "side": config["side"],
                    "sides": list(config["sides"]),
                    "targets": copy.deepcopy(config["targets"]),
                    "maxJointSpeedDegS": config["maxJointSpeedDegS"],
                    "gripperEffort": config["gripperEffort"],
                    "toleranceRad": config["toleranceRad"],
                    "toleranceDeg": config["toleranceDeg"],
                    "gripperToleranceM": config["gripperToleranceM"],
                    "stableSec": config["stableSec"],
                    "timeoutSec": config["timeoutSec"],
                }
            )
        if publish_result:
            data["publishCode"] = publish_result.get("code", "")
            data["topics"] = copy.deepcopy(publish_result.get("topics", []))
            data["publishedAt"] = publish_result.get("publishedAt", "")
        if hold_result:
            data["holdCode"] = hold_result.get("code", "")
        if feedback:
            data["feedback"] = copy.deepcopy(feedback)
        if errors:
            data.update(copy.deepcopy(errors))
        if last_feedback_error:
            data["lastFeedbackError"] = last_feedback_error
        return data

    def _execute_inference(self, node):
        """Run remote inference closed-loop until the remote reports success."""
        params = node.get("params") or {}
        try:
            config = self._inference_config(params)
        except ValueError as exc:
            detail = f"Inference params invalid: {exc}"
            self._set_task_status(node, "failed", detail, self._inference_status_data("failed"))
            return "failed", detail

        manager = get_inference_manager()
        self._set_task_status(
            node,
            "running",
            f"Connecting to remote inference: {config['remoteUrl']}.",
            self._inference_status_data("connecting", config),
        )
        connect_result = manager.connect(config["remoteUrl"])
        if not connect_result.get("ok"):
            detail = connect_result.get("detail") or connect_result.get("code") or "Inference connect failed."
            self._set_task_status(node, "failed", detail, self._inference_status_data("failed", config, connect_result=connect_result))
            return "failed", detail

        if config["autoEnablePiper"]:
            outcome, detail = self._enable_piper_for_inference(node, config)
            if outcome != "completed":
                return outcome, detail

        round_index = 0
        total_executed = 0
        while not self._stop_event.is_set():
            round_index += 1
            request_payload = {
                "prompt": config["prompt"],
                "chassisLimits": copy.deepcopy(config["chassisLimits"]),
            }
            self._set_task_status(
                node,
                "running",
                f"Requesting inference chunk #{round_index}.",
                self._inference_status_data("requesting", config, round_index=round_index, total_executed=total_executed),
            )
            request_result = manager.request_chunk(request_payload)
            request_data = self._inference_status_data(
                "success" if request_result.get("isSuccess") is True else "chunk_ready",
                config,
                round_index=round_index,
                total_executed=total_executed,
                request_result=request_result,
            )
            if not request_result.get("ok"):
                detail = request_result.get("detail") or request_result.get("code") or "Inference chunk request failed."
                self._set_task_status(node, "failed", detail, self._inference_status_data("failed", config, round_index, total_executed, request_result))
                return "failed", detail
            if request_result.get("isSuccess") is True:
                detail = "Remote inference reported task success."
                self._set_task_status(node, "completed", detail, request_data)
                return "completed", detail
            if self._stop_event.is_set():
                break

            execute_payload = {
                "steps": config["steps"],
                "frequencyHz": config["frequencyHz"],
                "maxJointSpeedDegS": config["maxJointSpeedDegS"],
            }
            self._set_task_status(
                node,
                "running",
                f"Executing inference chunk #{round_index}.",
                self._inference_status_data(
                    "executing",
                    config,
                    round_index=round_index,
                    total_executed=total_executed,
                    request_result=request_result,
                ),
            )
            execute_result = manager.execute_chunk(execute_payload)
            total_executed += int(execute_result.get("executedSteps") or 0)
            execute_data = self._inference_status_data(
                "executed",
                config,
                round_index=round_index,
                total_executed=total_executed,
                request_result=request_result,
                execute_result=execute_result,
            )
            if not execute_result.get("ok"):
                detail = execute_result.get("detail") or execute_result.get("code") or "Inference chunk execution failed."
                if self._stop_event.is_set() or execute_result.get("code") == "INFER-STOPPED":
                    self._set_task_status(node, "stopped", detail, execute_data)
                    return "stopped", detail
                self._set_task_status(node, "failed", detail, self._inference_status_data("failed", config, round_index, total_executed, request_result, execute_result))
                return "failed", detail

            self._set_task_status(node, "running", f"Inference round #{round_index} executed.", execute_data)

        manager.stop(reason="state_machine")
        self._set_task_status(
            node,
            "stopped",
            "State machine run stopped.",
            self._inference_status_data("stopped", config, round_index=round_index, total_executed=total_executed),
        )
        return "stopped", "State machine run stopped."

    def _enable_piper_for_inference(self, node, config):
        writer = get_ros_writer()
        result = None
        for index in range(config["enableRepeat"]):
            if self._stop_event.is_set():
                self._set_task_status(
                    node,
                    "stopped",
                    "State machine run stopped.",
                    self._inference_status_data("stopped", config, enable_result=result),
                )
                return "stopped", "State machine run stopped."
            detail = f"Enabling Piper for inference ({index + 1}/{config['enableRepeat']})."
            self._set_task_status(
                node,
                "running",
                detail,
                self._inference_status_data("enabling_piper", config, enable_result=result),
            )
            result = writer.publish(INFERENCE_PIPER_ENABLE_ACTION_KEY, {"enabled": True})
            if not result.get("ok"):
                detail = result.get("detail") or result.get("code") or "Piper enable failed."
                self._set_task_status(node, "failed", detail, self._inference_status_data("failed", config, enable_result=result))
                return "failed", detail
            if index < config["enableRepeat"] - 1 and self._stop_event.wait(config["enableIntervalSec"]):
                self._set_task_status(
                    node,
                    "stopped",
                    "State machine run stopped.",
                    self._inference_status_data("stopped", config, enable_result=result),
                )
                return "stopped", "State machine run stopped."

        self._set_task_status(
            node,
            "running",
            "Piper enabled for inference.",
            self._inference_status_data("piper_enabled", config, enable_result=result),
        )
        return "completed", "Piper enabled for inference."

    @staticmethod
    def _inference_config(params):
        remote_url = str(params.get("remoteUrl") or params.get("url") or "").strip()
        if not remote_url:
            raise ValueError("remoteUrl is required.")
        prompt = str(params.get("prompt") or "")
        steps = _bounded_int(params.get("steps"), "steps", INFERENCE_DEFAULT_STEPS, INFERENCE_MIN_STEPS, INFERENCE_MAX_STEPS)
        frequency_hz = _bounded_float(
            params.get("frequencyHz"),
            "frequencyHz",
            INFERENCE_DEFAULT_FREQUENCY_HZ,
            INFERENCE_MIN_FREQUENCY_HZ,
            INFERENCE_MAX_FREQUENCY_HZ,
        )
        max_joint_speed = _bounded_float(
            params.get("maxJointSpeedDegS"),
            "maxJointSpeedDegS",
            INFERENCE_DEFAULT_JOINT_SPEED_DEG_S,
            INFERENCE_MIN_JOINT_SPEED_DEG_S,
            INFERENCE_MAX_JOINT_SPEED_DEG_S,
        )
        chassis_limits = {}
        for key, default in INFERENCE_DEFAULT_CHASSIS_LIMITS.items():
            chassis_limits[key] = _bounded_float(params.get(key), key, default, 0.0, 10.0)
        enable_repeat = _bounded_int(params.get("enableRepeat"), "enableRepeat", INFERENCE_PIPER_ENABLE_REPEAT, 1, 10)
        enable_interval_ms = _bounded_float(
            params.get("enableIntervalMs"),
            "enableIntervalMs",
            INFERENCE_PIPER_ENABLE_INTERVAL_SEC * 1000.0,
            0.0,
            2000.0,
        )
        return {
            "remoteUrl": remote_url,
            "prompt": prompt,
            "steps": steps,
            "frequencyHz": frequency_hz,
            "maxJointSpeedDegS": max_joint_speed,
            "chassisLimits": chassis_limits,
            "autoEnablePiper": _bool_param(params.get("autoEnablePiper"), True),
            "enableRepeat": enable_repeat,
            "enableIntervalSec": enable_interval_ms / 1000.0,
        }

    @staticmethod
    def _inference_status_data(
        phase,
        config=None,
        round_index=0,
        total_executed=0,
        request_result=None,
        execute_result=None,
        connect_result=None,
        enable_result=None,
    ):
        data = {
            "phase": phase,
            "round": round_index,
            "totalExecutedSteps": total_executed,
        }
        if config:
            data.update(
                {
                    "remoteUrl": config["remoteUrl"],
                    "prompt": config["prompt"],
                    "steps": config["steps"],
                    "frequencyHz": config["frequencyHz"],
                    "maxJointSpeedDegS": config["maxJointSpeedDegS"],
                    "chassisLimits": copy.deepcopy(config["chassisLimits"]),
                    "autoEnablePiper": config["autoEnablePiper"],
                }
            )
        if connect_result:
            data["connectCode"] = connect_result.get("code", "")
        if enable_result:
            data["enableCode"] = enable_result.get("code", "")
            data["enableTopic"] = enable_result.get("topic", "")
            data["enablePublishedAt"] = enable_result.get("publishedAt", "")
        if request_result:
            data.update(
                {
                    "requestCode": request_result.get("code", ""),
                    "isSuccess": request_result.get("isSuccess") is True,
                    "chunkId": request_result.get("chunkId"),
                    "chunkSteps": request_result.get("chunkSteps", 0),
                    "clipped": request_result.get("clipped", 0),
                    "chunkTiming": copy.deepcopy(request_result.get("chunkTiming")),
                }
            )
        if execute_result:
            data.update(
                {
                    "executeCode": execute_result.get("code", ""),
                    "executedSteps": execute_result.get("executedSteps", 0),
                    "requestedSteps": execute_result.get("requestedSteps", 0),
                    "executionTiming": copy.deepcopy(execute_result.get("executionTiming")),
                }
            )
        return data

    def _execute_grasp_inference(self, params):
        """Remote inference grasp; left/right targets + prompt."""
        return "failed", "Inference grasp task is not implemented yet."

    def _execute_grasp_auto(self, params):
        """End-effector pose grasp (fake interface for now)."""
        return "failed", "Auto grasp task is not implemented yet."

    # ----- run state helpers -----

    def _begin_iteration(self, iteration):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return False
            self._run.update(
                {
                    "active": True,
                    "status": "running",
                    "currentId": "sm_start",
                    "completedIds": [],
                    "edgePath": [],
                    "path": ["sm_start"],
                    "iteration": iteration,
                    "error": "",
                    "taskStatus": None,
                }
            )
            return True

    def _mark_iteration_completed(self):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return
            self._run["completedIterations"] = int(self._run.get("completedIterations") or 0) + 1

    def _set_current_node(self, node_id):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return
            self._run["currentId"] = node_id
            if not self._run["path"] or self._run["path"][-1] != node_id:
                self._run["path"].append(node_id)

    def _mark_node_completed(self, node_id):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return
            if node_id not in self._run["completedIds"]:
                self._run["completedIds"].append(node_id)

    def _mark_edge_taken(self, from_id, to_id):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return
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
