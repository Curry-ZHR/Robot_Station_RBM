"""Persistent backend-to-remote WebSocket session for inference.

The backend HTTP server is a synchronous ThreadingHTTPServer, while the
``websockets`` client is asyncio based. This module runs a single asyncio event
loop in a dedicated daemon thread and exposes blocking helpers that HTTP request
threads can call. The connection is established once and reused for the whole
session; each request-chunk reuses the same socket.
"""

import asyncio
import concurrent.futures
import inspect
import json
import threading


class RemoteSessionError(RuntimeError):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _load_websockets():
    try:
        import websockets  # noqa: F401
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RemoteSessionError(
            "INFER-WS-DEPENDENCY",
            "The 'websockets' package is required for remote inference. Install it with 'pip install websockets'.",
        ) from exc
    return websockets


class RemoteInferenceSession:
    def __init__(self):
        self._lock = threading.RLock()
        self._loop = None
        self._thread = None
        self._ws = None
        self._url = None
        self._last_exchange_timing = None

    @property
    def url(self):
        return self._url

    @property
    def last_exchange_timing(self):
        with self._lock:
            return dict(self._last_exchange_timing) if self._last_exchange_timing else None

    def is_connected(self):
        with self._lock:
            return self._ws is not None

    def _ensure_loop(self):
        with self._lock:
            if self._loop is not None and self._thread is not None and self._thread.is_alive():
                return self._loop
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._run_loop,
                name="inference-ws-loop",
                daemon=True,
            )
            self._thread.start()
            return self._loop

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _submit(self, coro, timeout):
        loop = self._ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return future.result(timeout=timeout)
        except (asyncio.TimeoutError, concurrent.futures.TimeoutError) as exc:
            future.cancel()
            raise RemoteSessionError("INFER-WS-TIMEOUT", "Remote inference request timed out.") from exc

    def connect(self, url, timeout_sec=10.0):
        websockets = _load_websockets()
        url = str(url or "").strip()
        if not url.startswith("ws://") and not url.startswith("wss://"):
            raise RemoteSessionError("INFER-WS-URL", "Remote URL must start with ws:// or wss://.")
        connect_kwargs = {"max_size": None, "ping_interval": 20, "ping_timeout": 20}
        if "proxy" in inspect.signature(websockets.connect).parameters:
            connect_kwargs["proxy"] = None

        async def _do_connect():
            if self._ws is not None:
                try:
                    await self._ws.close()
                except Exception:
                    pass
                self._ws = None
            self._ws = await websockets.connect(url, **connect_kwargs)
            return True

        try:
            self._submit(_do_connect(), timeout=timeout_sec)
        except RemoteSessionError:
            raise
        except Exception as exc:
            raise RemoteSessionError("INFER-WS-CONNECT", f"Failed to connect to {url}: {exc}") from exc
        self._url = url
        return True

    def request_chunk(self, message, timeout_sec=15.0):
        if self._ws is None:
            raise RemoteSessionError("INFER-WS-DISCONNECTED", "Not connected to a remote inference server.")
        payload = json.dumps(message, ensure_ascii=True)

        async def _do_exchange():
            loop = asyncio.get_running_loop()
            send_started = loop.time()
            try:
                await self._ws.send(payload)
            except Exception as exc:
                self._ws = None
                raise RemoteSessionError("INFER-WS-SEND", f"Failed to send observation: {exc}") from exc
            send_finished = loop.time()

            ignored_messages = 0
            receive_started = send_finished
            deadline = loop.time() + timeout_sec
            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise RemoteSessionError("INFER-WS-TIMEOUT", "Timed out waiting for an action chunk.")
                try:
                    raw = await asyncio.wait_for(self._ws.recv(), timeout=remaining)
                except asyncio.TimeoutError as exc:
                    raise RemoteSessionError("INFER-WS-TIMEOUT", "Timed out waiting for an action chunk.") from exc
                except Exception as exc:
                    self._ws = None
                    raise RemoteSessionError("INFER-WS-RECV", f"Remote connection closed: {exc}") from exc
                try:
                    parsed = json.loads(raw)
                except (TypeError, ValueError):
                    ignored_messages += 1
                    continue
                if isinstance(parsed, dict) and parsed.get("type") == "action_chunk":
                    received_at = loop.time()
                    timing = {
                        "sendMs": (send_finished - send_started) * 1000.0,
                        "receiveMs": (received_at - receive_started) * 1000.0,
                        "roundTripMs": (received_at - send_started) * 1000.0,
                        "ignoredMessages": ignored_messages,
                    }
                    return parsed, timing
                ignored_messages += 1
                # Ignore acks/logs/other message types and keep waiting.

        # Add a little slack so the inner deadline triggers before the outer one.
        try:
            message, timing = self._submit(_do_exchange(), timeout=timeout_sec + 2.0)
        except RemoteSessionError:
            with self._lock:
                self._last_exchange_timing = None
            raise
        with self._lock:
            self._last_exchange_timing = timing
        return message

    def close(self, timeout_sec=5.0):
        if self._ws is None:
            self._url = None
            return True

        async def _do_close():
            try:
                await self._ws.close()
            finally:
                self._ws = None
            return True

        try:
            self._submit(_do_close(), timeout=timeout_sec)
        except RemoteSessionError:
            self._ws = None
        finally:
            self._url = None
        return True
