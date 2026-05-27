import os
import shlex
import signal
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from modules.logger import get_logger


ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs" / "runtime"
LOGGER = get_logger()


def _result(ok, code, detail, service):
    return {
        "ok": ok,
        "code": code,
        "detail": detail,
        "service": service,
    }


class ManagedService:
    def __init__(self, spec):
        self.spec = spec
        self._lock = threading.RLock()
        self._process = None
        self._status = "stopped"
        self._last_error = ""
        self._last_returncode = None
        self._started_at = ""
        self._stopped_at = ""
        self._log_file = ""

    def status(self):
        with self._lock:
            self._refresh_locked()
            return self._status_payload_locked()

    def start(self):
        with self._lock:
            self._refresh_locked()
            if self._process is not None:
                return _result(
                    True,
                    "SVC-ALREADY-RUNNING",
                    f"{self.spec.name} is already {self._status}.",
                    self._status_payload_locked(),
                )

            LOG_DIR.mkdir(parents=True, exist_ok=True)
            self._log_file = str(LOG_DIR / f"{self.spec.key}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log")
            shell_command = self._shell_command()
            try:
                with open(self._log_file, "ab") as log:
                    self._process = subprocess.Popen(
                        ["/bin/bash", "-lc", shell_command],
                        cwd=self._resolve_cwd(),
                        env=os.environ.copy(),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
            except OSError as exc:
                self._process = None
                self._status = "failed"
                self._last_error = str(exc)
                self._last_returncode = None
                return _result(
                    False,
                    "SVC-START-EXEC",
                    f"Failed to start {self.spec.name}: {exc}",
                    self._status_payload_locked(),
                )

            self._status = "starting"
            self._last_error = ""
            self._last_returncode = None
            self._started_at = time.strftime("%H:%M:%S")
            self._stopped_at = ""
            LOGGER.info("Service %s starting: %s", self.spec.key, " ".join(self.spec.command))

        time.sleep(max(0.0, float(self.spec.startup_grace_sec)))

        with self._lock:
            self._refresh_locked()
            if self._process is None:
                ok = self._status == "running"
                return _result(
                    ok,
                    "SVC-STARTED" if ok else "SVC-START-FAILED",
                    f"{self.spec.name} startup finished with status {self._status}.",
                    self._status_payload_locked(),
                )

            self._status = "running"
            return _result(
                True,
                "SVC-STARTED",
                f"{self.spec.name} process is running.",
                self._status_payload_locked(),
            )

    def stop(self):
        with self._lock:
            self._refresh_locked()
            process = self._process
            if process is None:
                self._status = "stopped"
                return _result(
                    True,
                    "SVC-ALREADY-STOPPED",
                    f"{self.spec.name} is already stopped.",
                    self._status_payload_locked(),
                )
            self._status = "stopping"
            pid = process.pid
            LOGGER.info("Service %s stopping pid=%s", self.spec.key, pid)

        self._terminate_process_group(process)

        with self._lock:
            self._refresh_locked()
            if self._process is None:
                self._status = "stopped"
                self._stopped_at = time.strftime("%H:%M:%S")
                return _result(
                    True,
                    "SVC-STOPPED",
                    f"{self.spec.name} stopped.",
                    self._status_payload_locked(),
                )
            return _result(
                False,
                "SVC-STOP-FAILED",
                f"{self.spec.name} did not stop cleanly.",
                self._status_payload_locked(),
            )

    def restart(self):
        stop_result = self.stop()
        if not stop_result.get("ok"):
            return stop_result
        return self.start()

    def shutdown(self):
        with self._lock:
            self._refresh_locked()
            should_stop = self._process is not None
        if should_stop:
            self.stop()

    def _resolve_cwd(self):
        cwd = Path(self.spec.cwd)
        if not cwd.is_absolute():
            cwd = ROOT_DIR / cwd
        return str(cwd)

    def _shell_command(self):
        lines = []
        for setup_script in self.spec.setup_scripts:
            quoted = shlex.quote(str(setup_script))
            lines.append(f"if [ -f {quoted} ]; then source {quoted}; fi")
        lines.append(f"exec {shlex.join(self.spec.command)}")
        return "\n".join(lines)

    def _status_payload_locked(self):
        pid = self._process.pid if self._process is not None else None
        return {
            "key": self.spec.key,
            "name": self.spec.name,
            "status": self._status,
            "pid": pid,
            "startedAt": self._started_at,
            "stoppedAt": self._stopped_at,
            "logFile": self._log_file,
            "lastError": self._last_error,
            "lastReturnCode": self._last_returncode,
            "spec": self.spec.to_dict(),
        }

    def _refresh_locked(self):
        if self._process is None:
            return
        returncode = self._process.poll()
        if returncode is None:
            if self._status == "starting":
                return
            if self._status != "stopping":
                self._status = "running"
            return

        self._last_returncode = returncode
        self._process = None
        self._stopped_at = time.strftime("%H:%M:%S")
        if self._status == "stopping":
            self._status = "stopped"
            return
        if returncode == 0:
            self._status = "stopped"
            self._last_error = ""
            return
        self._status = "failed"
        self._last_error = f"process exited with code {returncode}"

    def _terminate_process_group(self, process):
        timeout = max(1.0, float(self.spec.shutdown_timeout_sec))
        signals = (
            (signal.SIGINT, timeout),
            (signal.SIGTERM, 2.0),
            (signal.SIGKILL, 1.0),
        )
        for sig, wait_sec in signals:
            if process.poll() is not None:
                return
            try:
                os.killpg(os.getpgid(process.pid), sig)
            except ProcessLookupError:
                return
            except OSError as exc:
                LOGGER.warning("Failed to signal service %s: %s", self.spec.key, exc)
                return
            try:
                process.wait(timeout=wait_sec)
                return
            except subprocess.TimeoutExpired:
                continue

