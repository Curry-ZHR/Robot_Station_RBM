import time

from modules.state_machine import executor as executor_module
from modules.state_machine.event_executor import EventSequenceExecutor


def _node(node_id, task_type, params=None, outgoing=None):
    return {
        "id": node_id,
        "type": "task",
        "taskType": task_type,
        "title": node_id,
        "params": params or {},
        "outgoingIds": outgoing or [],
    }


def _start(outgoing):
    return {"id": "sm_start", "type": "start", "title": "Start", "params": {}, "outgoingIds": outgoing}


def _end():
    return {"id": "sm_end", "type": "end", "title": "End", "params": {}, "outgoingIds": []}


def _reset_graph(name, node_id):
    return {
        "id": f"graph_{node_id}",
        "name": name,
        "nodes": [
            _start([node_id]),
            _node(node_id, "reset_odom", outgoing=["sm_end"]),
            _end(),
        ],
    }


def _wait_terminal(manager, timeout_sec=1.0):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        run = manager.status()["run"]
        if not run["active"]:
            return run
        time.sleep(0.01)
    raise AssertionError(f"Event sequence did not finish: {manager.status()['run']}")


def test_event_sequence_runs_saved_graphs_in_order(monkeypatch):
    graphs = {
        "g1": _reset_graph("靠近货柜", "reset_a"),
        "g2": _reset_graph("夹取完成", "reset_b"),
    }
    calls = []

    def fake_reset(payload):
        calls.append(payload)
        return {
            "ok": True,
            "code": "CHASSIS-C-ODOM-RESET",
            "detail": "reset ok",
            "action": "reset_odom",
            "service": "/reset_odom",
        }

    monkeypatch.setattr(executor_module, "reset_chassis_odometry", fake_reset)
    manager = EventSequenceExecutor(poll_interval_sec=0.01, graph_lookup=lambda graph_id: graphs.get(graph_id))

    result = manager.start(
        {
            "name": "完整任务",
            "events": [
                {"id": "event_a", "title": "靠近货柜", "graphId": "g1"},
                {"id": "event_b", "title": "夹取完成", "graphId": "g2"},
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert calls == [{}, {}]
    assert run["status"] == "completed"
    assert run["currentEventId"] is None
    assert run["path"] == ["event_a", "event_b"]
    assert run["completedEventIds"] == ["event_a", "event_b"]
    assert run["eventStatus"]["eventId"] == "event_b"
    assert run["eventStatus"]["status"] == "completed"
    assert run["childRun"]["status"] == "completed"
    assert run["childRun"]["path"] == ["sm_start", "reset_b", "sm_end"]


def test_event_sequence_fails_when_child_graph_fails(monkeypatch):
    graphs = {
        "g1": _reset_graph("靠近货柜", "reset_a"),
        "g2": _reset_graph("夹取失败", "reset_b"),
    }
    results = [
        {"ok": True, "code": "CHASSIS-C-ODOM-RESET", "detail": "reset ok", "service": "/reset_odom"},
        {"ok": False, "code": "CHASSIS-C-ODOM-RESET-FAILED", "detail": "reset failed", "service": "/reset_odom"},
    ]

    def fake_reset(payload):
        return dict(results.pop(0))

    monkeypatch.setattr(executor_module, "reset_chassis_odometry", fake_reset)
    manager = EventSequenceExecutor(poll_interval_sec=0.01, graph_lookup=lambda graph_id: graphs.get(graph_id))

    result = manager.start(
        {
            "name": "失败任务",
            "events": [
                {"id": "event_a", "graphId": "g1"},
                {"id": "event_b", "graphId": "g2"},
            ],
        }
    )
    run = _wait_terminal(manager)

    assert result["ok"] is True
    assert run["status"] == "failed"
    assert run["currentEventId"] == "event_b"
    assert run["completedEventIds"] == ["event_a"]
    assert run["eventStatus"]["eventId"] == "event_b"
    assert run["eventStatus"]["status"] == "failed"
    assert run["error"] == "reset failed"
    assert run["childRun"]["status"] == "failed"


def test_event_sequence_rejects_missing_graph():
    manager = EventSequenceExecutor(poll_interval_sec=0.01, graph_lookup=lambda graph_id: None)

    result = manager.start({"name": "缺失流程", "events": [{"id": "event_a", "graphId": "missing"}]})

    assert result["ok"] is False
    assert result["code"] == "SM-EVENT-RUN-PAYLOAD"
    assert "Graph not found" in result["detail"]
