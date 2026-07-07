"""Event-level state machine executor.

An event sequence is an ordered list of saved state-machine graphs. Each event
resolves a graph snapshot at run start, then executes it start-to-end with a
dedicated child StateMachineExecutor.
"""

import copy
import threading
import time

from .executor import StateMachineExecutor
from .manager import get_state_machine_store

_EVENT_EXECUTOR = None
_EVENT_EXECUTOR_LOCK = threading.Lock()
_TERMINAL_RUN_STATUSES = {"completed", "failed", "stopped"}
EVENT_LOOP_RESTART_PAUSE_SEC = 0.05


def _result(ok, code, detail, **extra):
    payload = {"ok": ok, "code": code, "detail": detail}
    payload.update(extra)
    return payload


def _now_text():
    return time.strftime("%H:%M:%S")


def _idle_event_run():
    return {
        "active": False,
        "status": "idle",
        "sequenceName": "",
        "currentEventId": None,
        "currentEventIndex": -1,
        "completedEventIds": [],
        "path": [],
        "loop": False,
        "iteration": 0,
        "completedIterations": 0,
        "error": "",
        "eventStatus": None,
        "childRun": None,
    }


class EventSequenceExecutor:
    def __init__(self, poll_interval_sec=0.2, graph_lookup=None):
        self._lock = threading.Lock()
        self._run = _idle_event_run()
        self._worker = None
        self._child_executor = None
        self._stop_event = threading.Event()
        self._poll_interval_sec = poll_interval_sec
        self._graph_lookup = graph_lookup or (lambda graph_id: get_state_machine_store().graph_snapshot(graph_id))

    def is_active(self):
        with self._lock:
            return bool(self._run.get("active"))

    def status(self):
        with self._lock:
            return _result(True, "SM-EVENT-RUN-STATUS", "Event sequence run status.", run=copy.deepcopy(self._run))

    def start(self, payload):
        if not isinstance(payload, dict):
            return _result(False, "SM-EVENT-RUN-PAYLOAD", "Request body must be a JSON object.")
        raw_events = payload.get("events")
        if not isinstance(raw_events, list):
            return _result(False, "SM-EVENT-RUN-PAYLOAD", "events must be a JSON array.")
        name = str(payload.get("name") or "未命名事件序列")
        loop = payload.get("loop") is True

        try:
            events = self._resolve_events(raw_events)
        except ValueError as exc:
            return _result(False, "SM-EVENT-RUN-PAYLOAD", str(exc))
        if not events:
            return _result(False, "SM-EVENT-RUN-PAYLOAD", "Event sequence must contain at least one enabled event.")

        with self._lock:
            if self._run.get("active"):
                return _result(False, "SM-EVENT-RUN-BUSY", "Event sequence is already running.", run=copy.deepcopy(self._run))
            self._stop_event.clear()
            self._child_executor = None
            self._run = _idle_event_run()
            self._run.update(
                {
                    "active": True,
                    "status": "running",
                    "sequenceName": name,
                    "currentEventId": events[0]["id"],
                    "currentEventIndex": 0,
                    "path": [events[0]["id"]],
                    "loop": loop,
                    "iteration": 1,
                    "completedIterations": 0,
                    "error": "",
                    "eventStatus": self._event_status_payload(events[0], 0, "pending", "Waiting to start event."),
                    "childRun": None,
                }
            )
            worker_events = copy.deepcopy(events)
            thread = threading.Thread(
                target=self._run_loop,
                args=(worker_events, loop),
                name="robot_station_state_machine_events",
                daemon=True,
            )
            self._worker = thread
            thread.start()
            return _result(True, "SM-EVENT-RUN-STARTED", "Event sequence run started.", run=copy.deepcopy(self._run))

    def stop(self):
        with self._lock:
            if not self._run.get("active"):
                return _result(True, "SM-EVENT-RUN-NOTRUNNING", "Event sequence is not running.", run=copy.deepcopy(self._run))
            self._stop_event.set()
            child = self._child_executor
            current_event_id = self._run.get("currentEventId")
            event_status = self._run.get("eventStatus") or {}

        if child is not None:
            child.stop()
            self._set_child_run_from(child)

        self._finish_run(
            "stopped",
            "Event sequence run stopped.",
            current_event_id=current_event_id,
            event_status=self._event_status_from_existing(event_status, "stopped", "Event sequence run stopped."),
        )
        return _result(True, "SM-EVENT-RUN-STOPPED", "Event sequence run stopped.", run=self.status()["run"])

    def _resolve_events(self, raw_events):
        events = []
        for index, event in enumerate(raw_events):
            if not isinstance(event, dict):
                raise ValueError(f"events[{index}] must be a JSON object.")
            if event.get("enabled") is False:
                continue
            graph_id = str(event.get("graphId") or "").strip()
            if not graph_id:
                raise ValueError(f"events[{index}].graphId must not be empty.")
            graph = self._graph_lookup(graph_id)
            if not isinstance(graph, dict):
                raise ValueError(f"Graph not found for event {index + 1}: {graph_id}")
            nodes = graph.get("nodes")
            if not isinstance(nodes, list):
                raise ValueError(f"Graph has no nodes for event {index + 1}: {graph.get('name') or graph_id}")
            event_id = str(event.get("id") or "").strip() or f"event_{index + 1}"
            graph_name = str(graph.get("name") or graph_id)
            title = str(event.get("title") or graph_name).strip() or graph_name
            events.append(
                {
                    "id": event_id,
                    "title": title,
                    "graphId": graph_id,
                    "graphName": graph_name,
                    "index": index,
                    "nodes": copy.deepcopy(nodes),
                }
            )
        return events

    def _run_loop(self, events, loop=False):
        iteration = 1
        while True:
            if not self._begin_iteration(iteration, events[0]):
                return
            outcome, detail, event = self._run_sequence_once(events)
            if outcome == "completed":
                self._mark_iteration_completed()
                if not loop:
                    self._finish_run("completed", "Event sequence run completed.", current_event_id=None)
                    return
                if self._stop_event.wait(EVENT_LOOP_RESTART_PAUSE_SEC):
                    self._finish_run("stopped", "Event sequence run stopped.", current_event_id=None)
                    return
                iteration += 1
                continue
            current_event_id = event.get("id") if event else None
            if outcome == "stopped":
                self._finish_run("stopped", detail or "Event sequence run stopped.", current_event_id=current_event_id)
                return
            self._fail_run(detail or "Event sequence run failed.", event=event)
            return

    def _run_sequence_once(self, events):
        for event_index, event in enumerate(events):
            if self._stop_event.is_set():
                return "stopped", "Event sequence run stopped.", event
            self._set_current_event(event, event_index)
            child = StateMachineExecutor(poll_interval_sec=self._poll_interval_sec)
            with self._lock:
                self._child_executor = child

            start_result = child.start({"name": event["graphName"], "nodes": event["nodes"]})
            self._set_child_run_from(child)
            if not start_result.get("ok"):
                detail = start_result.get("detail") or start_result.get("code") or "Event graph failed to start."
                self._set_event_status(event, event_index, "failed", detail)
                return "failed", detail, event

            while not self._stop_event.is_set():
                child_run = self._set_child_run_from(child)
                if not child_run.get("active"):
                    break
                self._stop_event.wait(self._poll_interval_sec)

            if self._stop_event.is_set():
                child.stop()
                self._set_child_run_from(child)
                self._set_event_status(event, event_index, "stopped", "Event sequence run stopped.")
                return "stopped", "Event sequence run stopped.", event

            child_run = self._set_child_run_from(child)
            child_status = str(child_run.get("status") or "")
            if child_status == "completed":
                self._mark_event_completed(event, event_index, child_run)
                continue
            if child_status == "stopped":
                detail = "Event graph stopped."
                self._set_event_status(event, event_index, "stopped", detail)
                return "stopped", detail, event
            detail = self._child_failure_detail(child_run)
            self._set_event_status(event, event_index, "failed", detail)
            return "failed", detail, event

        with self._lock:
            self._child_executor = None
        return "completed", "Event sequence run completed.", None

    @staticmethod
    def _child_failure_detail(child_run):
        task_status = child_run.get("taskStatus") or {}
        return (
            child_run.get("error")
            or task_status.get("detail")
            or f"Event graph ended with status: {child_run.get('status') or 'unknown'}."
        )

    def _begin_iteration(self, iteration, first_event):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return False
            self._run.update(
                {
                    "active": True,
                    "status": "running",
                    "currentEventId": first_event["id"],
                    "currentEventIndex": 0,
                    "completedEventIds": [],
                    "path": [first_event["id"]],
                    "iteration": iteration,
                    "error": "",
                    "eventStatus": self._event_status_payload(first_event, 0, "running", "Starting event."),
                    "childRun": None,
                }
            )
            return True

    def _set_current_event(self, event, event_index):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return
            self._run["currentEventId"] = event["id"]
            self._run["currentEventIndex"] = event_index
            if not self._run["path"] or self._run["path"][-1] != event["id"]:
                self._run["path"].append(event["id"])
            self._run["eventStatus"] = self._event_status_payload(event, event_index, "running", "Event graph is running.")
            self._run["childRun"] = None

    def _mark_event_completed(self, event, event_index, child_run):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return
            if event["id"] not in self._run["completedEventIds"]:
                self._run["completedEventIds"].append(event["id"])
            self._run["eventStatus"] = self._event_status_payload(event, event_index, "completed", "Event graph completed.")
            self._run["childRun"] = copy.deepcopy(child_run)

    def _mark_iteration_completed(self):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES:
                return
            self._run["completedIterations"] = int(self._run.get("completedIterations") or 0) + 1

    def _set_event_status(self, event, event_index, status, detail):
        with self._lock:
            self._run["eventStatus"] = self._event_status_payload(event, event_index, status, detail)

    def _set_child_run_from(self, child):
        child_run = child.status()["run"] if child is not None else None
        with self._lock:
            self._run["childRun"] = copy.deepcopy(child_run)
        return child_run or {}

    @staticmethod
    def _event_status_payload(event, event_index, status, detail):
        return {
            "eventId": str(event.get("id") or ""),
            "eventIndex": event_index,
            "title": str(event.get("title") or ""),
            "graphId": str(event.get("graphId") or ""),
            "graphName": str(event.get("graphName") or ""),
            "status": str(status or ""),
            "detail": str(detail or ""),
            "updatedAt": _now_text(),
        }

    @staticmethod
    def _event_status_from_existing(event_status, status, detail):
        if not event_status:
            return None
        updated = copy.deepcopy(event_status)
        updated.update({"status": status, "detail": detail, "updatedAt": _now_text()})
        return updated

    def _finish_run(self, status, detail, current_event_id=None, event_status=None):
        with self._lock:
            if self._run.get("status") in _TERMINAL_RUN_STATUSES and self._run.get("status") != "running":
                return
            self._run.update(
                {
                    "active": False,
                    "status": status,
                    "currentEventId": current_event_id,
                    "error": detail if status == "failed" else "",
                }
            )
            if event_status is not None:
                self._run["eventStatus"] = event_status

    def _fail_run(self, detail, event=None):
        event_status = None
        with self._lock:
            existing = self._run.get("eventStatus") or {}
            if event is not None and existing.get("eventId") == event.get("id"):
                event_status = self._event_status_from_existing(existing, "failed", detail)
        self._finish_run("failed", detail, current_event_id=event.get("id") if event else None, event_status=event_status)


def get_state_machine_event_executor():
    global _EVENT_EXECUTOR
    with _EVENT_EXECUTOR_LOCK:
        if _EVENT_EXECUTOR is None:
            _EVENT_EXECUTOR = EventSequenceExecutor()
        return _EVENT_EXECUTOR
