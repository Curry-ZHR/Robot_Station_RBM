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

            cleaned = self._cleanup_external_processes_locked()
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
            detail = f"{self.spec.name} process is running."
            if cleaned:
                detail = f"{detail} Cleaned stale processes: {', '.join(str(item['pid']) for item in cleaned)}."
            return _result(
                True,
                "SVC-STARTED",
                detail,
                self._status_payload_locked(),
            )

    def stop(self):
        with self._lock:
            self._refresh_locked()
            process = self._process
            if process is None:
                cleaned = self._cleanup_external_processes_locked()
                self._status = "stopped"
                code = "SVC-STOPPED" if cleaned else "SVC-ALREADY-STOPPED"
                detail = f"{self.spec.name} is already stopped."
                if cleaned:
                    detail = f"{self.spec.name} stale processes cleaned: {', '.join(str(item['pid']) for item in cleaned)}."
                return _result(
                    True,
                    code,
                    detail,
                    self._status_payload_locked(),
                )
            self._status = "stopping"
            pid = process.pid
            LOGGER.info("Service %s stopping pid=%s", self.spec.key, pid)

        self._terminate_process_group(process)

        with self._lock:
            self._refresh_locked()
            cleaned = self._cleanup_external_processes_locked()
            self._refresh_locked()
            if self._process is None:
                self._status = "stopped"
                self._stopped_at = time.strftime("%H:%M:%S")
                detail = f"{self.spec.name} stopped."
                if cleaned:
                    detail = f"{detail} Cleaned stale processes: {', '.join(str(item['pid']) for item in cleaned)}."
                return _result(
                    True,
                    "SVC-STOPPED",
                    detail,
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
        external_processes = self._matching_processes_locked(exclude_pids={pid} if pid else set())
        status = "external" if self._process is None and external_processes else self._status
        return {
            "key": self.spec.key,
            "name": self.spec.name,
            "status": status,
            "pid": pid,
            "externalProcesses": external_processes,
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

    def _matching_processes_locked(self, exclude_pids=None):
        patterns = tuple(pattern for pattern in self.spec.cleanup_process_patterns if pattern)
        if not patterns:
            return []

        excluded = {os.getpid()}
        excluded.update(pid for pid in (exclude_pids or set()) if pid)
        matches = []
        for proc_dir in Path("/proc").iterdir():
            if not proc_dir.name.isdigit():
                continue
            pid = int(proc_dir.name)
            if pid in excluded:
                continue
            try:
                raw = (proc_dir / "cmdline").read_bytes()
            except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
                continue
            if not raw:
                continue
            cmdline = raw.replace(b"\x00", b" ").decode(errors="replace").strip()
            if any(pattern in cmdline for pattern in patterns):
                matches.append({"pid": pid, "cmdline": cmdline})
        return sorted(matches, key=lambda item: item["pid"])

    def _pid_alive(self, pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _cleanup_external_processes_locked(self):
        matches = self._matching_processes_locked()
        if not matches:
            return []

        remaining = list(matches)
        for sig, wait_sec in ((signal.SIGINT, 0.8), (signal.SIGTERM, 0.6), (signal.SIGKILL, 0.2)):
            for item in remaining:
                try:
                    os.kill(item["pid"], sig)
                except ProcessLookupError:
                    continue
                except OSError as exc:
                    LOGGER.warning("Failed to signal stale %s process pid=%s: %s", self.spec.key, item["pid"], exc)
            time.sleep(wait_sec)
            remaining = [item for item in remaining if self._pid_alive(item["pid"])]
            if not remaining:
                break

        cleaned = [item for item in matches if not self._pid_alive(item["pid"])]
        if cleaned:
            LOGGER.info(
                "Service %s cleaned stale processes: %s",
                self.spec.key,
                ", ".join(str(item["pid"]) for item in cleaned),
            )
        return cleaned
