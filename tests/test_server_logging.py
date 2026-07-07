import backend.server as server


class FakeLogger:
    def __init__(self):
        self.errors = []
        self.successes = []

    def error(self, message):
        self.errors.append(message)

    def success(self, message):
        self.successes.append(message)


def test_log_action_result_includes_calibration_camera_context(monkeypatch):
    logger = FakeLogger()
    monkeypatch.setattr(server, "LOGGER", logger)

    server.log_action_result(
        "Calibration sample capture",
        {
            "ok": False,
            "code": "CAL-SAMPLE-CORNERS",
            "detail": "Checkerboard corners were not detected in the RGB image.",
            "camera": "camera_l",
            "expectedCornerCount": 88,
            "detectedCornerCount": 0,
            "board": {"columns": 11, "rows": 8},
        },
    )

    assert len(logger.errors) == 1
    assert "camera=camera_l" in logger.errors[0]
    assert "corners=0/88" in logger.errors[0]
    assert "board=11x8" in logger.errors[0]
