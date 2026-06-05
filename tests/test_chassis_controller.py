from modules.control.chassis import controller


class FakeTrigger:
    class Request:
        pass


class FakeResponse:
    def __init__(self, success=True, message="reset ok"):
        self.success = success
        self.message = message


class FakeRuntime:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def call_service(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def test_reset_chassis_odometry_calls_trigger_service(monkeypatch):
    runtime = FakeRuntime(FakeResponse(success=True, message="reset ok"))
    monkeypatch.setattr(controller, "get_ros_runtime", lambda: runtime)
    monkeypatch.setattr(controller, "import_service_class", lambda service_type: FakeTrigger)

    result = controller.reset_chassis_odometry({})

    assert result["ok"]
    assert result["code"] == "CHASSIS-C-ODOM-RESET"
    assert result["detail"] == "reset ok"
    assert result["service"] == "/reset_odom"
    assert runtime.calls[0]["key"] == "chassis_reset_odom"
    assert runtime.calls[0]["service_type"] == "std_srvs/srv/Trigger"
    assert runtime.calls[0]["service_name"] == "/reset_odom"
    assert isinstance(runtime.calls[0]["request"], FakeTrigger.Request)


def test_reset_chassis_odometry_reports_service_failure(monkeypatch):
    runtime = FakeRuntime(FakeResponse(success=False, message="reset failed"))
    monkeypatch.setattr(controller, "get_ros_runtime", lambda: runtime)
    monkeypatch.setattr(controller, "import_service_class", lambda service_type: FakeTrigger)

    result = controller.reset_chassis_odometry({})

    assert not result["ok"]
    assert result["code"] == "CHASSIS-C-ODOM-RESET-FAILED"
    assert result["detail"] == "reset failed"
