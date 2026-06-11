"""State machine executor skeleton.

Only the interface is defined for now; task handlers are stubs that will be
implemented one by one later.

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
       }}

- POST /api/state-machine/run/start   body: {name: str, nodes: [node]}
    Node shape matches the editor snapshot (id/type/taskType/title/params/outgoingIds).
    Returns the same result shape; fails with SM-RUN-UNIMPLEMENTED for now.

- POST /api/state-machine/run/stop
    Stops the current run; SM-RUN-UNIMPLEMENTED for now.

Execution semantics (agreed, to implement):
- Walk the graph from sm_start; multiple outgoingIds -> random choice.
- Any task failure stops the whole run (status "failed", node reported in
  currentId, reason in error). Manual chassis override interrupting
  navigation also fails the run. No retry, no failure branches in v1.
- Task dispatch (all in-process, reusing existing managers):
    navigation       -> modules.navigation get_navigation_manager().start(params)
                        then poll status() until completed/failed.
                        params: {targetName, x, y, yawDeg, mode}
    wait             -> interruptible sleep. params: {durationSec, reason}
    grasp(inference) -> modules.inference manager (remote WS inference).
                        params: {graspMethod: "inference", leftTarget,
                                 rightTarget, prompt}
    grasp(auto)      -> end-effector pose grasp (fake interface for now).
                        params: {graspMethod: "auto", leftTarget, rightTarget,
                                 leftPose, rightPose}
                        pose format: "x, y, z, roll, pitch, yaw"
"""

import threading

_EXECUTOR = None
_EXECUTOR_LOCK = threading.Lock()


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
    }


class StateMachineExecutor:
    """Walks a state machine graph and dispatches each task to robot modules.

    All methods are stubs except status(); implementations land one by one.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._run = _idle_run()
        self._worker = None
        self._stop_event = threading.Event()

    # ----- public API -----

    def status(self):
        with self._lock:
            return _result(True, "SM-RUN-STATUS", "State machine run status.", run=dict(self._run))

    def start(self, payload):
        """Validate the graph, spawn the worker thread, return immediately."""
        return _result(False, "SM-RUN-UNIMPLEMENTED", "State machine executor is not implemented yet.")

    def stop(self):
        """Signal the worker to stop after the current task aborts."""
        return _result(False, "SM-RUN-UNIMPLEMENTED", "State machine executor is not implemented yet.")

    # ----- run loop -----

    def _run_loop(self, name, nodes):
        """Walk the graph from sm_start; random choice on multiple outgoing."""
        pass

    # ----- task handlers, implemented one by one -----

    def _execute_navigation(self, params):
        """Drive the chassis to params x/y/yawDeg via NavigationManager."""
        pass

    def _execute_wait(self, params):
        """Interruptible sleep for params durationSec."""
        pass

    def _execute_grasp_inference(self, params):
        """Remote inference grasp; left/right targets + prompt."""
        pass

    def _execute_grasp_auto(self, params):
        """End-effector pose grasp (fake interface for now)."""
        pass


def get_state_machine_executor():
    global _EXECUTOR
    with _EXECUTOR_LOCK:
        if _EXECUTOR is None:
            _EXECUTOR = StateMachineExecutor()
        return _EXECUTOR
