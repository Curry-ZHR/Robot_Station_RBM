import backend.server as server


def _check(name, status="正常", code="OK", advice="ok"):
    return {
        "name": name,
        "status": status,
        "source": "测试",
        "code": code,
        "advice": advice,
        "detail": advice,
        "metric": {"label": name, "value": status, "percent": 0, "level": "ok"},
    }


def _reset_cache():
    with server.SELF_CHECK_CACHE_LOCK:
        server.SELF_CHECK_CACHE = None


def _handler(path):
    handler = object.__new__(server.RobotStationHandler)
    handler.path = path
    return handler


def test_self_check_summary_blocks_only_hard_errors():
    results = [
        _check("ROS2 daemon"),
        _check("CAN 接口"),
        _check("磁盘空间", status="警告", code="DSK-S-WARN", advice="low but usable"),
        _check("GPU 可用性", status="错误", code="GPU-A-CMD", advice="no gpu"),
    ]

    summary = server.summarize_self_check(results)

    assert summary["state"] == "warn"
    assert summary["blockers"] == []
    assert [item["name"] for item in summary["warnings"]] == ["磁盘空间", "GPU 可用性"]

    results[2] = _check("磁盘空间", status="错误", code="DSK-S-CRITICAL", advice="disk full")

    summary = server.summarize_self_check(results)

    assert summary["state"] == "blocked"
    assert [item["name"] for item in summary["blockers"]] == ["磁盘空间"]


def test_run_self_check_caches_result(monkeypatch):
    _reset_cache()
    seen = {}

    monkeypatch.setattr(server, "ensure_ros_daemon", lambda: _check("ROS2 daemon"))

    def fake_can(auto_activate=True):
        seen["auto_activate"] = auto_activate
        return _check("CAN 接口")

    monkeypatch.setattr(server, "check_can_interface", fake_can)
    monkeypatch.setattr(server, "check_disk_space", lambda: _check("磁盘空间"))
    monkeypatch.setattr(server, "check_gpu_status", lambda: _check("GPU 可用性", status="错误", code="GPU-A-CMD"))
    monkeypatch.setattr(server, "log_check_result", lambda result: None)

    payload = server.run_self_check(auto_activate=False)
    cached = server.cached_self_check_status()

    assert seen["auto_activate"] is False
    assert payload["ran"] is True
    assert payload["summary"]["state"] == "warn"
    assert cached["ranAtMs"] == payload["ranAtMs"]
    assert [item["name"] for item in cached["results"]] == ["ROS2 daemon", "CAN 接口", "磁盘空间", "GPU 可用性"]


def test_self_check_status_endpoint_returns_idle_when_uncached():
    _reset_cache()
    responses = []
    handler = _handler("/api/self-check/status")
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))

    server.RobotStationHandler.do_GET(handler)

    assert responses == [(server.empty_self_check_status(), 200)]


def test_self_check_run_endpoint_passes_auto_activate_query(monkeypatch):
    responses = []
    seen = {}
    handler = _handler("/api/self-check/run?auto_activate=0")
    handler.write_json = lambda payload, status=200, headers=None: responses.append((payload, status))

    def fake_run_self_check(auto_activate=True):
        seen["auto_activate"] = auto_activate
        return {"ok": True, "code": "SELF-CHECK-RUN"}

    monkeypatch.setattr(server, "run_self_check", fake_run_self_check)

    server.RobotStationHandler.do_POST(handler)

    assert seen["auto_activate"] is False
    assert responses == [({"ok": True, "code": "SELF-CHECK-RUN"}, 200)]
