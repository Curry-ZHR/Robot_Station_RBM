"""File-backed persistence for the state machine editor.

Stores three collections as JSON files under modules/state_machine/data/:
- state_library.json: user-defined reusable states (name + task params)
- graphs.json: named state machine graphs (plus the auto-saved draft)
- event_sequences.json: ordered lists of saved graphs, run as events
"""

import json
import threading
import time
import uuid
from pathlib import Path

from modules.logger import get_logger

LOGGER = get_logger()

DATA_DIR = Path(__file__).resolve().parent / "data"
LIBRARY_FILE = DATA_DIR / "state_library.json"
GRAPHS_FILE = DATA_DIR / "graphs.json"
EVENT_SEQUENCES_FILE = DATA_DIR / "event_sequences.json"

TASK_TYPES = ("navigation", "inference", "piper_joint", "grasp", "wait", "topic_wait", "topic_publish")
DRAFT_GRAPH_ID = "__draft__"

_STORE = None
_STORE_LOCK = threading.Lock()


def _result(ok, code, detail, **extra):
    payload = {"ok": ok, "code": code, "detail": detail}
    payload.update(extra)
    return payload


def state_machine_result_status(result):
    if result.get("ok"):
        return 200
    code = result.get("code", "")
    if code.endswith("PAYLOAD"):
        return 400
    if code.endswith("UNKNOWN"):
        return 404
    if code.endswith("UNIMPLEMENTED"):
        return 501
    if code.endswith("BUSY"):
        return 409
    return 500


def _now_text():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _read_json_file(path, default):
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("State machine store failed to read %s: %s", path, exc)
        return default


def _write_json_file(path, payload):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


class StateMachineStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._states = self._load_states()
        self._graphs = self._load_graphs()
        self._event_sequences = self._load_event_sequences()

    @staticmethod
    def _load_states():
        raw = _read_json_file(LIBRARY_FILE, {})
        states = raw.get("states") if isinstance(raw, dict) else None
        return [state for state in states if isinstance(state, dict)] if isinstance(states, list) else []

    @staticmethod
    def _load_graphs():
        raw = _read_json_file(GRAPHS_FILE, {})
        graphs = raw.get("graphs") if isinstance(raw, dict) else None
        return [graph for graph in graphs if isinstance(graph, dict)] if isinstance(graphs, list) else []

    @staticmethod
    def _load_event_sequences():
        raw = _read_json_file(EVENT_SEQUENCES_FILE, {})
        sequences = raw.get("eventSequences") if isinstance(raw, dict) else None
        return [sequence for sequence in sequences if isinstance(sequence, dict)] if isinstance(sequences, list) else []

    def _persist_states(self):
        _write_json_file(LIBRARY_FILE, {"version": 1, "states": self._states})

    def _persist_graphs(self):
        _write_json_file(GRAPHS_FILE, {"version": 1, "graphs": self._graphs})

    def _persist_event_sequences(self):
        _write_json_file(EVENT_SEQUENCES_FILE, {"version": 1, "eventSequences": self._event_sequences})

    # ----- state library -----

    def list_states(self):
        with self._lock:
            return _result(True, "SM-STATES", "State library loaded.", states=json.loads(json.dumps(self._states)))

    def save_state(self, payload):
        if not isinstance(payload, dict):
            return _result(False, "SM-PAYLOAD", "Request body must be a JSON object.")
        title = str(payload.get("title") or "").strip()
        if not title:
            return _result(False, "SM-PAYLOAD", "State title must not be empty.")
        task_type = str(payload.get("taskType") or "").strip()
        if task_type not in TASK_TYPES:
            return _result(False, "SM-PAYLOAD", f"taskType must be one of {', '.join(TASK_TYPES)}.")
        params = payload.get("params")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return _result(False, "SM-PAYLOAD", "params must be a JSON object.")

        state_id = str(payload.get("id") or "").strip()
        with self._lock:
            existing = next((state for state in self._states if state.get("id") == state_id), None) if state_id else None
            if existing is not None:
                existing.update(
                    {
                        "title": title,
                        "taskType": task_type,
                        "params": params,
                        "updatedAt": _now_text(),
                    }
                )
                saved = existing
            else:
                saved = {
                    "id": f"sm_lib_{uuid.uuid4().hex[:10]}",
                    "title": title,
                    "taskType": task_type,
                    "params": params,
                    "createdAt": _now_text(),
                    "updatedAt": _now_text(),
                }
                self._states.append(saved)
            self._persist_states()
            LOGGER.info("State machine library state saved: %s (%s)", title, saved["id"])
            return _result(True, "SM-STATE-SAVED", f"State saved: {title}", state=json.loads(json.dumps(saved)))

    def delete_state(self, payload):
        state_id = str((payload or {}).get("id") or "").strip()
        if not state_id:
            return _result(False, "SM-PAYLOAD", "State id must not be empty.")
        with self._lock:
            existing = next((state for state in self._states if state.get("id") == state_id), None)
            if existing is None:
                return _result(False, "SM-STATE-UNKNOWN", f"State not found: {state_id}")
            self._states = [state for state in self._states if state.get("id") != state_id]
            self._persist_states()
            LOGGER.info("State machine library state deleted: %s", state_id)
            return _result(True, "SM-STATE-DELETED", f"State deleted: {existing.get('title', state_id)}")

    # ----- graphs -----

    def list_graphs(self):
        with self._lock:
            return _result(True, "SM-GRAPHS", "Graphs loaded.", graphs=json.loads(json.dumps(self._graphs)))

    def graph_snapshot(self, graph_id):
        graph_id = str(graph_id or "").strip()
        if not graph_id:
            return None
        with self._lock:
            graph = next((item for item in self._graphs if item.get("id") == graph_id), None)
            return json.loads(json.dumps(graph)) if graph is not None else None

    def save_graph(self, payload):
        if not isinstance(payload, dict):
            return _result(False, "SM-PAYLOAD", "Request body must be a JSON object.")
        nodes = payload.get("nodes")
        if not isinstance(nodes, list):
            return _result(False, "SM-PAYLOAD", "nodes must be a JSON array.")
        graph_id = str(payload.get("id") or "").strip()
        name = str(payload.get("name") or "").strip()
        if graph_id != DRAFT_GRAPH_ID and not name:
            return _result(False, "SM-PAYLOAD", "Graph name must not be empty.")

        with self._lock:
            existing = None
            if graph_id:
                existing = next((graph for graph in self._graphs if graph.get("id") == graph_id), None)
            if existing is None and graph_id != DRAFT_GRAPH_ID and name:
                # Saving under an existing name overwrites that graph.
                existing = next(
                    (graph for graph in self._graphs if graph.get("id") != DRAFT_GRAPH_ID and graph.get("name") == name),
                    None,
                )
            if existing is not None:
                existing.update({"name": name or existing.get("name", ""), "nodes": nodes, "savedAt": _now_text()})
                saved = existing
            else:
                saved = {
                    "id": graph_id if graph_id == DRAFT_GRAPH_ID else f"sm_graph_{uuid.uuid4().hex[:10]}",
                    "name": name,
                    "nodes": nodes,
                    "savedAt": _now_text(),
                }
                self._graphs.append(saved)
            self._persist_graphs()
            if saved["id"] != DRAFT_GRAPH_ID:
                LOGGER.info("State machine graph saved: %s (%s)", saved.get("name", ""), saved["id"])
            return _result(True, "SM-GRAPH-SAVED", f"Graph saved: {saved.get('name') or saved['id']}", graph=json.loads(json.dumps(saved)))

    def delete_graph(self, payload):
        graph_id = str((payload or {}).get("id") or "").strip()
        if not graph_id:
            return _result(False, "SM-PAYLOAD", "Graph id must not be empty.")
        with self._lock:
            existing = next((graph for graph in self._graphs if graph.get("id") == graph_id), None)
            if existing is None:
                return _result(False, "SM-GRAPH-UNKNOWN", f"Graph not found: {graph_id}")
            self._graphs = [graph for graph in self._graphs if graph.get("id") != graph_id]
            self._persist_graphs()
            LOGGER.info("State machine graph deleted: %s", graph_id)
            return _result(True, "SM-GRAPH-DELETED", f"Graph deleted: {existing.get('name') or graph_id}")

    # ----- event sequences -----

    def list_event_sequences(self):
        with self._lock:
            return _result(
                True,
                "SM-EVENT-SEQUENCES",
                "Event sequences loaded.",
                eventSequences=json.loads(json.dumps(self._event_sequences)),
            )

    def save_event_sequence(self, payload):
        if not isinstance(payload, dict):
            return _result(False, "SM-EVENT-SEQUENCE-PAYLOAD", "Request body must be a JSON object.")
        name = str(payload.get("name") or "").strip()
        if not name:
            return _result(False, "SM-EVENT-SEQUENCE-PAYLOAD", "Event sequence name must not be empty.")
        events = payload.get("events")
        if not isinstance(events, list):
            return _result(False, "SM-EVENT-SEQUENCE-PAYLOAD", "events must be a JSON array.")
        normalized_events = []
        for index, event in enumerate(events):
            if not isinstance(event, dict):
                return _result(False, "SM-EVENT-SEQUENCE-PAYLOAD", f"events[{index}] must be a JSON object.")
            graph_id = str(event.get("graphId") or "").strip()
            if not graph_id:
                return _result(False, "SM-EVENT-SEQUENCE-PAYLOAD", f"events[{index}].graphId must not be empty.")
            event_id = str(event.get("id") or "").strip() or f"sm_event_{uuid.uuid4().hex[:10]}"
            title = str(event.get("title") or "").strip()
            normalized_events.append(
                {
                    "id": event_id,
                    "title": title,
                    "graphId": graph_id,
                    "enabled": event.get("enabled") is not False,
                }
            )

        sequence_id = str(payload.get("id") or "").strip()
        with self._lock:
            existing = next((sequence for sequence in self._event_sequences if sequence.get("id") == sequence_id), None) if sequence_id else None
            if existing is None and name:
                existing = next((sequence for sequence in self._event_sequences if sequence.get("name") == name), None)
            if existing is not None:
                existing.update({"name": name, "events": normalized_events, "savedAt": _now_text()})
                saved = existing
            else:
                saved = {
                    "id": f"sm_event_seq_{uuid.uuid4().hex[:10]}",
                    "name": name,
                    "events": normalized_events,
                    "savedAt": _now_text(),
                }
                self._event_sequences.append(saved)
            self._persist_event_sequences()
            LOGGER.info("State machine event sequence saved: %s (%s)", saved.get("name", ""), saved["id"])
            return _result(
                True,
                "SM-EVENT-SEQUENCE-SAVED",
                f"Event sequence saved: {saved.get('name') or saved['id']}",
                eventSequence=json.loads(json.dumps(saved)),
            )

    def delete_event_sequence(self, payload):
        sequence_id = str((payload or {}).get("id") or "").strip()
        if not sequence_id:
            return _result(False, "SM-EVENT-SEQUENCE-PAYLOAD", "Event sequence id must not be empty.")
        with self._lock:
            existing = next((sequence for sequence in self._event_sequences if sequence.get("id") == sequence_id), None)
            if existing is None:
                return _result(False, "SM-EVENT-SEQUENCE-UNKNOWN", f"Event sequence not found: {sequence_id}")
            self._event_sequences = [sequence for sequence in self._event_sequences if sequence.get("id") != sequence_id]
            self._persist_event_sequences()
            LOGGER.info("State machine event sequence deleted: %s", sequence_id)
            return _result(True, "SM-EVENT-SEQUENCE-DELETED", f"Event sequence deleted: {existing.get('name') or sequence_id}")


def get_state_machine_store():
    global _STORE
    with _STORE_LOCK:
        if _STORE is None:
            _STORE = StateMachineStore()
        return _STORE
