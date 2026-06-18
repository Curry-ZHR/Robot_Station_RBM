from modules.runtime.managed_service import ManagedService
from modules.runtime.service_specs import default_service_specs


EXCLUSIVE_SERVICE_PEERS = {
    "piper": ("piper_remote",),
    "piper_remote": ("piper",),
}


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


class ServiceManager:
    def __init__(self, specs):
        self._services = {
            key: ManagedService(spec)
            for key, spec in specs.items()
        }

    @classmethod
    def with_default_services(cls):
        return cls(default_service_specs())

    def list_services(self):
        return _result(
            True,
            "SVC-LIST",
            "Managed services listed.",
            services=[service.status() for service in self._services.values()],
        )

    def get_service(self, key):
        service = self._services.get(key)
        if service is None:
            return _result(False, "SVC-UNKNOWN", f"Unknown service: {key}", key=key)
        return _result(True, "SVC-STATUS", f"Service {key} status.", service=service.status())

    def start_service(self, key):
        service = self._services.get(key)
        if service is None:
            return _result(False, "SVC-UNKNOWN", f"Unknown service: {key}", key=key)
        for peer_key in EXCLUSIVE_SERVICE_PEERS.get(key, ()):
            peer = self._services.get(peer_key)
            if peer is None:
                continue
            result = peer.stop()
            if not result.get("ok"):
                return result
        return service.start()

    def stop_service(self, key):
        service = self._services.get(key)
        if service is None:
            return _result(False, "SVC-UNKNOWN", f"Unknown service: {key}", key=key)
        return service.stop()

    def restart_service(self, key):
        stop_result = self.stop_service(key)
        if not stop_result.get("ok"):
            return stop_result
        return self.start_service(key)

    def perform(self, key, action):
        if action == "start":
            return self.start_service(key)
        if action == "stop":
            return self.stop_service(key)
        if action == "restart":
            return self.restart_service(key)
        return _result(False, "SVC-ACTION", f"Unsupported service action: {action}", key=key, action=action)

    def shutdown(self):
        for service in self._services.values():
            service.shutdown()
