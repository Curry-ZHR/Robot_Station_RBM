from modules.self_check.ros_check import ros_daemon


def _result(status, code):
    return ros_daemon._result(
        status,
        code,
        f"detail {code}",
        f"advice {code}",
    )


def test_ensure_ros_daemon_repairs_stuck_domain_99(monkeypatch):
    monkeypatch.setenv("ROS_DOMAIN_ID", "99")
    repaired = []

    monkeypatch.setattr(
        ros_daemon,
        "check_ros_daemon",
        lambda timeout_sec=2.5: _result("错误", "ROS2-D-TIMEOUT"),
    )

    def fake_repair(timeout_sec=4.0):
        repaired.append(timeout_sec)
        return _result("正常", "ROS2-D-REPAIRED")

    monkeypatch.setattr(ros_daemon, "_repair_stuck_daemon", fake_repair)

    result = ros_daemon.ensure_ros_daemon(timeout_sec=1.0, startup_timeout_sec=3.0)

    assert result["status"] == "正常"
    assert result["code"] == "ROS2-D-REPAIRED"
    assert repaired == [3.0]


def test_ensure_ros_daemon_does_not_repair_other_domains(monkeypatch):
    monkeypatch.setenv("ROS_DOMAIN_ID", "0")
    calls = []

    monkeypatch.setattr(
        ros_daemon,
        "check_ros_daemon",
        lambda timeout_sec=2.5: _result("错误", "ROS2-D-TIMEOUT"),
    )
    monkeypatch.setattr(
        ros_daemon,
        "_start_daemon",
        lambda timeout_sec=4.0: _result("正常", "ROS2-D-STARTED"),
    )
    monkeypatch.setattr(
        ros_daemon,
        "_wait_until_running",
        lambda timeout_sec=4.0: _result("正常", "ROS2-D-STARTED"),
    )
    monkeypatch.setattr(
        ros_daemon,
        "_repair_stuck_daemon",
        lambda timeout_sec=4.0: calls.append(timeout_sec),
    )

    result = ros_daemon.ensure_ros_daemon(timeout_sec=1.0, startup_timeout_sec=3.0)

    assert result["status"] == "正常"
    assert result["code"] == "ROS2-D-STARTED"
    assert calls == []


def test_repair_stuck_daemon_restarts_only_domain_99(monkeypatch):
    monkeypatch.setenv("ROS_DOMAIN_ID", "99")
    seen = {}

    def fake_find_pids(domain_id):
        seen["domain_id"] = domain_id
        return [1234]

    monkeypatch.setattr(ros_daemon, "_daemon_pids_for_domain", fake_find_pids)

    def fake_terminate(pids):
        seen["pids"] = pids
        return {"terminated": pids, "forced": [], "errors": []}

    monkeypatch.setattr(ros_daemon, "_terminate_daemon_pids", fake_terminate)
    monkeypatch.setattr(
        ros_daemon,
        "_start_daemon",
        lambda timeout_sec=4.0: _result("正常", "ROS2-D-STARTED"),
    )
    monkeypatch.setattr(
        ros_daemon,
        "_wait_until_running",
        lambda timeout_sec=4.0: _result("正常", "ROS2-D-STARTED"),
    )

    result = ros_daemon._repair_stuck_daemon(timeout_sec=2.0)

    assert seen == {"domain_id": "99", "pids": [1234]}
    assert result["status"] == "正常"
    assert result["code"] == "ROS2-D-REPAIRED"
    assert "ROS_DOMAIN_ID=99" in result["detail"]
