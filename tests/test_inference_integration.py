import asyncio
import json
import threading

import pytest

websockets = pytest.importorskip("websockets")

from modules.inference.manager import InferenceManager
from modules.inference.session import RemoteInferenceSession


def _arm():
    return {"joint1": 0.0, "joint2": 0.1, "joint3": -0.1, "joint4": 0.0, "joint5": 0.0, "joint6": 0.0, "gripper": 0.05}


def _chunk_payload():
    return {
        "type": "action_chunk",
        "chunk_id": "chunk_int",
        "actions": [
            {"left": _arm(), "right": _arm(), "lift": {"height": 400.0}, "speed": {"vx": 0.0, "vy": 0.0, "wz": 0.0}},
            {"left": _arm(), "right": _arm(), "lift": {"height": 410.0}, "speed": {"vx": 0.05, "vy": 0.0, "wz": 0.2}},
        ],
    }


class MockServer:
    def __init__(self):
        self.loop = None
        self.server = None
        self.port = None
        self.received = []
        self._ready = threading.Event()
        self._thread = None

    async def _handler(self, websocket):
        async for raw in websocket:
            message = json.loads(raw)
            self.received.append(message)
            if message.get("type") == "observation":
                await websocket.send(json.dumps(_chunk_payload()))

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def _start():
            self.server = await websockets.serve(self._handler, "127.0.0.1", 0)
            self.port = self.server.sockets[0].getsockname()[1]
            self._ready.set()

        self.loop.run_until_complete(_start())
        self.loop.run_forever()

    def start(self):
        self._thread = threading.Thread(target=self._run, name="mock-ws-server", daemon=True)
        self._thread.start()
        assert self._ready.wait(timeout=5.0)
        return f"ws://127.0.0.1:{self.port}"

    def stop(self):
        if self.loop is None:
            return
        self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread:
            self._thread.join(timeout=2.0)


@pytest.fixture
def mock_server():
    server = MockServer()
    url = server.start()
    try:
        yield server, url
    finally:
        server.stop()


def test_end_to_end_with_mock_server(mock_server):
    server, url = mock_server
    joint_calls = []
    chassis_calls = []

    manager = InferenceManager(
        session=RemoteInferenceSession(),
        joint_publisher=lambda payload: (joint_calls.append(payload) or {"ok": True, "code": "PIPER-C-PUBLISHED", "detail": "ok"}),
        chassis_publisher=lambda payload: (chassis_calls.append(payload) or {"ok": True, "code": "CHASSIS-C-PUBLISHED", "detail": "ok"}),
        chassis_stopper=lambda payload=None: {"ok": True},
        lift_mover=lambda payload: {"ok": True},
        lift_stopper=lambda payload=None: {"ok": True},
        observation_builder=lambda prompt: {"type": "observation", "prompt": prompt, "observation": {}},
    )

    try:
        assert manager.connect(url)["ok"]
        req = manager.request_chunk({"prompt": "grasp the bottle"})
        assert req["ok"], req
        assert req["chunkId"] == "chunk_0000"
        assert req["chunkSteps"] == 2

        result = manager.execute_chunk({"steps": 2, "frequencyHz": 30, "maxJointSpeedDegS": 20})
        assert result["ok"], result
        assert result["executedSteps"] == 2
        assert len(joint_calls) == 2
        assert len(chassis_calls) == 2
        # Second step carries the forward velocity and yaw rate from the chunk.
        assert chassis_calls[1]["linearX"] == pytest.approx(0.05)
        assert chassis_calls[1]["angularZ"] == pytest.approx(0.2)

        # The server saw exactly one observation for the single request.
        assert sum(1 for m in server.received if m.get("type") == "observation") == 1
    finally:
        manager.disconnect()
