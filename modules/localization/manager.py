import json
import os
import signal
import shutil
import subprocess
import threading
import time
from pathlib import Path

from modules.logger import get_logger
from modules.map import get_mapping_manager
from modules.ros_io import get_ros_reader, get_ros_writer


ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs" / "localization"
DEFAULT_CPU_LOCALIZER_COMMAND = (
    "ros2",
    "run",
    "robot_station_mapper",
    "robot_station_localizer_node",
)
DEFAULT_GPU_LOCALIZER_COMMAND = (
    "ros2",
    "run",
    "robot_station_mapper",
    "robot_station_gpu_localizer_node",
)
LOCALIZER_PACKAGE = "robot_station_mapper"
LOCALIZER_EXECUTABLES = {
    "robot_station_localizer_node",
    "robot_station_gpu_localizer_node",
}
VALID_BACKENDS = ("cpu", "gpu")
LOGGER = get_logger()


def _result(ok, code, detail, **extra):
    payload = {
        "ok": ok,
        "code": code,
        "detail": detail,
    }
    payload.update(extra)
    return payload


def localization_result_status(result):
    if result.get("ok"):
        return 200
    mapping = {
        "LOC-PAYLOAD": 400,
        "LOC-MAP": 400,
        "LOC-ACTION": 400,
        "LOC-NOMAP": 409,
        "LOC-BUSY": 409,
        "LOC-NOTRUNNING": 409,
        "LOC-GPU-UNAVAILABLE": 503,
        "LOC-MAP-LIST": 503,
        "LOC-DEPENDENCY": 503,
        "LOC-START-FAILED": 500,
        "LOC-STOP-FAILED": 500,
    }
    return mapping.get(result.get("code", ""), 500)


def _command_from_env(env_key, default):
    command_text = os.environ.get(env_key, "")
    if command_text.strip():
        return tuple(command_text.split())
    return default


def _clean_backend(value, default="cpu"):
    text = str(value or default).strip().lower()
    if text not in VALID_BACKENDS:
        return ""
    return text


def _clean_topic(value, default):
    text = str(value or "").strip()
    if not text:
        return default
    return text if text.startswith("/") else f"/{text}"


def _safe_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _safe_float(value, default, minimum, maximum):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _safe_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


class LocalizationManager:
    def __init__(self, localizer_command=None, gpu_localizer_command=None):
        self.localizer_commands = {
            "cpu": tuple(
                localizer_command
                or _command_from_env("ROBOT_STATION_LOCALIZER_COMMAND", DEFAULT_CPU_LOCALIZER_COMMAND)
            ),
            "gpu": tuple(
                gpu_localizer_command
                or _command_from_env(
                    "ROBOT_STATION_GPU_LOCALIZER_COMMAND",
                    DEFAULT_GPU_LOCALIZER_COMMAND,
                )
            ),
        }
        self.localizer_command = self.localizer_commands["cpu"]
        self._lock = threading.RLock()
        self._process = None
        self._map = None
        self._backend = "cpu"
        self._status = "stopped"
        self._started_at = ""
        self._stopped_at = ""
        self._last_error = ""
        self._last_returncode = None
        self._log_path = ""
        self._active_command = ()
        self._backend_availability_cache = {}

    def status(self):
        with self._lock:
            self._refresh_locked()
            process_payload = self._process_payload_locked()

        ros_status = self._read_localization_status()
        with self._lock:
            if process_payload["running"] and self._has_ros_state(ros_status) and self._status == "starting":
                self._status = "running"
                process_payload = self._process_payload_locked()
        pose = self._read_localization_pose()
        state = self._state_from_status(process_payload, ros_status)
        return _result(
            True,
            "LOC-STATUS",
            "Localization status loaded.",
            state=state,
            running=process_payload["running"],
            process=process_payload,
            map=self._map_payload(),
            localizationStatus=ros_status,
            pose=pose,
            backend=self._backend,
            availableBackends=self._backend_payloads(),
            localizerCommand=list(self._command_for_backend(self._backend)),
            localizerCommands={
                backend: list(command) for backend, command in self.localizer_commands.items()
            },
        )

    def start(self, payload=None):
        payload = payload or {}
        if not isinstance(payload, dict):
            return _result(False, "LOC-PAYLOAD", "Payload must be a JSON object.")
        map_name = str(payload.get("mapName") or payload.get("name") or "").strip()
        if not map_name:
            return _result(False, "LOC-NOMAP", "Localization start requires mapName.")

        map_entry_result = self._resolve_map(map_name)
        if not map_entry_result.get("ok"):
            return map_entry_result
        map_entry = map_entry_result["map"]

        with self._lock:
            self._refresh_locked()
            if self._process is not None:
                return _result(
                    False,
                    "LOC-BUSY",
                    "Localization is already running.",
                    process=self._process_payload_locked(),
                    map=self._map_payload_locked(),
                )

            settings = self._settings_from_payload(payload)
            if not settings.get("backend"):
                return _result(
                    False,
                    "LOC-PAYLOAD",
                    "Localization backend must be one of: cpu, gpu.",
                )
            if settings["backend"] == "gpu" and not self._backend_available("gpu"):
                return _result(
                    False,
                    "LOC-GPU-UNAVAILABLE",
                    "GPU localization executable is not available. Build robot_station_gpu_localizer_node with fast_gicp first.",
                    backend="gpu",
                    availableBackends=self._backend_payloads(),
                )
            command = self._build_command(map_entry, settings)
            if self._manages_localizer_command(command):
                self._cleanup_stale_localizer_processes()
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            self._log_path = str(LOG_DIR / f"localizer_{time.strftime('%Y%m%d_%H%M%S')}.log")
            try:
                with Path(self._log_path).open("ab") as log_file:
                    log_file.write((" ".join(command) + "\n").encode("utf-8"))
                    self._process = subprocess.Popen(
                        command,
                        cwd=str(ROOT_DIR),
                        env=self._localizer_environment(),
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
            except FileNotFoundError as exc:
                self._process = None
                self._status = "failed"
                self._last_error = str(exc)
                return _result(False, "LOC-DEPENDENCY", f"Localizer command is not available: {exc}")
            except OSError as exc:
                self._process = None
                self._status = "failed"
                self._last_error = str(exc)
                return _result(False, "LOC-START-FAILED", f"Failed to start localizer: {exc}")

            self._map = dict(map_entry)
            self._map["settings"] = settings
            self._backend = settings["backend"]
            self._active_command = tuple(command)
            self._status = "starting"
            self._started_at = time.strftime("%H:%M:%S")
            self._stopped_at = ""
            self._last_error = ""
            self._last_returncode = None
            LOGGER.info("Localization starting with map %s", map_name)
            return _result(
                True,
                "LOC-STARTED",
                "Localization node started.",
                backend=self._backend,
                availableBackends=self._backend_payloads(),
                process=self._process_payload_locked(),
                map=self._map_payload_locked(),
            )

    def stop(self):
        with self._lock:
            self._refresh_locked()
            process = self._process
            if process is None:
                self._status = "stopped"
                return _result(
                    True,
                    "LOC-ALREADY-STOPPED",
                    "Localization is already stopped.",
                    process=self._process_payload_locked(),
                    map=self._map_payload_locked(),
                )
            self._status = "stopping"

        should_cleanup = self._manages_localizer_command(self._active_command)
        stopped = self._terminate_process(process)
        if should_cleanup:
            self._cleanup_stale_localizer_processes()

        with self._lock:
            self._refresh_locked()
            if stopped or self._process is None:
                self._process = None
                self._status = "stopped"
                self._stopped_at = time.strftime("%H:%M:%S")
                return _result(
                    True,
                    "LOC-STOPPED",
                    "Localization node stopped.",
                    process=self._process_payload_locked(),
                    map=self._map_payload_locked(),
                )
            return _result(
                False,
                "LOC-STOP-FAILED",
                "Localization node did not stop cleanly.",
                process=self._process_payload_locked(),
                map=self._map_payload_locked(),
            )

    def restart(self):
        with self._lock:
            current_map = dict(self._map or {})
        if not current_map.get("name"):
            return _result(False, "LOC-NOMAP", "No locked localization map is available.")
        stop_result = self.stop()
        if not stop_result.get("ok"):
            return stop_result
        return self.start({"mapName": current_map["name"], **(current_map.get("settings") or {})})

    def publish_initial_pose(self, payload=None):
        payload = payload or {}
        result = get_ros_writer().publish("localization_initial_pose", payload)
        return result

    def _resolve_map(self, map_name):
        maps_result = get_mapping_manager().list_saved_maps()
        if not maps_result.get("ok"):
            return _result(
                False,
                "LOC-MAP-LIST",
                maps_result.get("detail") or "Saved map list could not be loaded.",
                mapping=maps_result,
            )
        for entry in maps_result.get("maps", []):
            if entry.get("name") != map_name:
                continue
            map_path = Path(entry.get("mapPath", ""))
            if not map_path.is_file():
                return _result(False, "LOC-MAP", "Selected map package does not contain map.pcd.")
            return _result(True, "LOC-MAP", "Localization map resolved.", map=dict(entry))
        return _result(False, "LOC-MAP", f"Saved map not found: {map_name}")

    def _settings_from_payload(self, payload):
        backend = _clean_backend(payload.get("backend"), "cpu")
        return {
            "backend": backend,
            "cloudTopic": _clean_topic(payload.get("cloudTopic"), "/rslidar_points"),
            "odomTopic": _clean_topic(payload.get("odomTopic"), "/odom"),
            "initialPoseTopic": _clean_topic(payload.get("initialPoseTopic"), "/initialpose"),
            "poseTopic": _clean_topic(payload.get("poseTopic"), "/localization/pose"),
            "statusTopic": _clean_topic(payload.get("statusTopic"), "/localization/status"),
            "mapFrame": str(payload.get("mapFrame") or "map").strip() or "map",
            "baseFrame": str(payload.get("baseFrame") or "base_link").strip() or "base_link",
            "maxFailedFrames": _safe_int(payload.get("maxFailedFrames"), 15, 1, 100),
            "minSourcePoints": _safe_int(payload.get("minSourcePoints"), 50, 1, 100000),
            "voxelLeafM": _safe_float(payload.get("voxelLeafM"), 0.08, 0.0, 0.50),
            "useNdtWhenTracking": _safe_bool(
                payload.get("useNdtWhenTracking"),
                default=True,
            ),
            "useOdomRetry": _safe_bool(payload.get("useOdomRetry"), default=True),
            "odomMaxAgeSec": _safe_float(payload.get("odomMaxAgeSec"), 1.0, 0.05, 30.0),
            "ndtResolutionM": _safe_float(payload.get("ndtResolutionM"), 0.5, 0.05, 5.0),
            "ndtMaxIterations": _safe_int(payload.get("ndtMaxIterations"), 40, 1, 100),
            "gicpMaxCorrespondenceM": _safe_float(
                payload.get("gicpMaxCorrespondenceM"),
                0.20,
                0.02,
                2.0,
            ),
            "gicpMaxIterations": _safe_int(payload.get("gicpMaxIterations"), 50, 1, 100),
            "maxPoseJumpM": _safe_float(payload.get("maxPoseJumpM"), 0.35, 0.01, 5.0),
            "maxPoseJumpYawDeg": _safe_float(payload.get("maxPoseJumpYawDeg"), 20.0, 0.1, 180.0),
            "odomTranslationMarginM": _safe_float(
                payload.get("odomTranslationMarginM"),
                0.12,
                0.0,
                2.0,
            ),
            "odomYawMarginDeg": _safe_float(payload.get("odomYawMarginDeg"), 8.0, 0.0, 180.0),
            "odomDeltaScale": _safe_float(payload.get("odomDeltaScale"), 3.0, 0.0, 20.0),
            "fitnessDegradeRatio": _safe_float(payload.get("fitnessDegradeRatio"), 6.0, 1.0, 100.0),
            "fitnessDegradeAbs": _safe_float(payload.get("fitnessDegradeAbs"), 0.08, 0.0, 10.0),
        }

    def _build_command(self, map_entry, settings):
        return [
            *self._runtime_command_for_backend(settings.get("backend", "cpu")),
            "--ros-args",
            "-p",
            f"map_path:={map_entry['mapPath']}",
            "-p",
            f"map_name:={map_entry['name']}",
            "-p",
            f"cloud_topic:={settings['cloudTopic']}",
            "-p",
            f"odom_topic:={settings['odomTopic']}",
            "-p",
            f"initial_pose_topic:={settings['initialPoseTopic']}",
            "-p",
            f"pose_topic:={settings['poseTopic']}",
            "-p",
            f"status_topic:={settings['statusTopic']}",
            "-p",
            f"map_frame:={settings['mapFrame']}",
            "-p",
            f"base_frame:={settings['baseFrame']}",
            "-p",
            f"max_failed_frames:={settings['maxFailedFrames']}",
            "-p",
            f"min_source_points:={settings['minSourcePoints']}",
            "-p",
            f"voxel_leaf:={settings['voxelLeafM']}",
            "-p",
            f"use_ndt_when_tracking:={str(settings['useNdtWhenTracking']).lower()}",
            "-p",
            f"use_odom_retry:={str(settings['useOdomRetry']).lower()}",
            "-p",
            f"odom_max_age_sec:={settings['odomMaxAgeSec']}",
            "-p",
            f"ndt_resolution:={settings['ndtResolutionM']}",
            "-p",
            f"ndt_max_iterations:={settings['ndtMaxIterations']}",
            "-p",
            f"gicp_max_correspondence:={settings['gicpMaxCorrespondenceM']}",
            "-p",
            f"gicp_max_iterations:={settings['gicpMaxIterations']}",
            "-p",
            f"max_pose_jump_m:={settings['maxPoseJumpM']}",
            "-p",
            f"max_pose_jump_yaw_deg:={settings['maxPoseJumpYawDeg']}",
            "-p",
            f"odom_translation_margin_m:={settings['odomTranslationMarginM']}",
            "-p",
            f"odom_yaw_margin_deg:={settings['odomYawMarginDeg']}",
            "-p",
            f"odom_delta_scale:={settings['odomDeltaScale']}",
            "-p",
            f"fitness_degrade_ratio:={settings['fitnessDegradeRatio']}",
            "-p",
            f"fitness_degrade_abs:={settings['fitnessDegradeAbs']}",
        ]

    def _command_for_backend(self, backend):
        return self.localizer_commands.get(backend) or self.localizer_commands["cpu"]

    def _runtime_command_for_backend(self, backend):
        command = self._command_for_backend(backend)
        if self._is_ros2_run_command(command):
            executable = self._local_ros2_run_executable(command)
            if executable and executable.is_file():
                return (str(executable),)
        return command

    def _backend_payloads(self):
        return [
            {
                "id": backend,
                "label": backend.upper(),
                "available": True if backend == "cpu" else self._backend_available(backend),
                "command": list(self._command_for_backend(backend)),
            }
            for backend in VALID_BACKENDS
        ]

    def _backend_available(self, backend):
        if backend == "cpu":
            return True
        now = time.monotonic()
        cached = self._backend_availability_cache.get(backend)
        if cached and now - cached["checkedAt"] < 5.0:
            return cached["available"]
        available = self._probe_backend_available(backend)
        self._backend_availability_cache[backend] = {
            "available": available,
            "checkedAt": now,
        }
        return available

    def _probe_backend_available(self, backend):
        command = self._command_for_backend(backend)
        if not command:
            return False
        executable = command[0]
        if Path(executable).is_file() or shutil.which(executable):
            if self._is_ros2_run_command(command):
                return self._ros2_run_executable_available(command)
            return True
        return False

    def _is_ros2_run_command(self, command):
        return len(command) >= 4 and Path(command[0]).name == "ros2" and command[1] == "run"

    def _ros2_run_executable_available(self, command):
        package_name = command[2]
        executable_name = command[3]
        local_executable = (
            self._local_ros2_run_executable(command)
        )
        if local_executable and local_executable.is_file():
            return True
        try:
            completed = subprocess.run(
                [command[0], "pkg", "executables", package_name],
                cwd=str(ROOT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2.0,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        if completed.returncode != 0:
            return False
        expected = f"{package_name} {executable_name}"
        return any(line.strip() == expected for line in completed.stdout.splitlines())

    def _local_ros2_run_executable(self, command):
        if not self._is_ros2_run_command(command):
            return None
        package_name = command[2]
        executable_name = command[3]
        return (
            ROOT_DIR
            / "ros_packages"
            / "localization"
            / "robot_station_mapper"
            / "install"
            / package_name
            / "lib"
            / package_name
            / executable_name
        )

    def _localizer_environment(self):
        env = os.environ.copy()
        env.setdefault("RMW_IMPLEMENTATION", "rmw_fastrtps_cpp")
        fastdds_transports = os.environ.get(
            "ROBOT_STATION_LOCALIZER_FASTDDS_BUILTIN_TRANSPORTS",
            "UDPv4",
        ).strip()
        if fastdds_transports:
            env.setdefault("FASTDDS_BUILTIN_TRANSPORTS", fastdds_transports)
        env.setdefault("RCUTILS_LOGGING_BUFFERED_STREAM", "0")
        return env

    def _read_localization_status(self):
        result = get_ros_reader().read("localization_status", timeout_sec=0.0)
        payload = {
            "ok": result.get("ok", False),
            "code": result.get("code", ""),
            "detail": result.get("detail", ""),
            "ageMs": result.get("ageMs"),
            "stale": result.get("stale"),
            "receivedAt": result.get("receivedAt"),
            "raw": result,
            "data": None,
        }
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        text = data.get("data")
        if isinstance(text, str) and text.strip():
            try:
                payload["data"] = json.loads(text)
            except json.JSONDecodeError:
                payload["data"] = None
                payload["parseError"] = "Invalid localization status JSON."
        return payload

    def _read_localization_pose(self):
        result = get_ros_reader().read("localization_pose", timeout_sec=0.0)
        return {
            "ok": result.get("ok", False),
            "code": result.get("code", ""),
            "detail": result.get("detail", ""),
            "ageMs": result.get("ageMs"),
            "stale": result.get("stale"),
            "receivedAt": result.get("receivedAt"),
            "data": result.get("data"),
        }

    def _state_from_status(self, process_payload, ros_status):
        if not process_payload.get("running"):
            return "stopped"
        data = ros_status.get("data") if isinstance(ros_status, dict) else None
        if isinstance(data, dict) and data.get("state"):
            return str(data["state"])
        return process_payload.get("status") or "starting"

    def _has_ros_state(self, ros_status):
        data = ros_status.get("data") if isinstance(ros_status, dict) else None
        return isinstance(data, dict) and bool(data.get("state"))

    def _refresh_locked(self):
        if self._process is None:
            return
        return_code = self._process.poll()
        if return_code is None:
            return
        self._last_returncode = return_code
        self._process = None
        was_stopping = self._status == "stopping"
        self._status = "stopped" if return_code == 0 or was_stopping else "failed"
        self._stopped_at = time.strftime("%H:%M:%S")
        if return_code == 0 or was_stopping:
            self._last_error = ""
        else:
            self._last_error = f"Localizer exited with code {return_code}."

    def _terminate_process(self, process):
        if process is None or process.poll() is not None:
            return True
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except Exception:
            try:
                process.terminate()
            except Exception:
                LOGGER.exception("Failed to terminate localization process")
                return False
        try:
            process.wait(timeout=3.0)
            return True
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except Exception:
            try:
                process.kill()
            except Exception:
                LOGGER.exception("Failed to kill localization process")
                return False
        try:
            process.wait(timeout=1.0)
            return True
        except subprocess.TimeoutExpired:
            LOGGER.warning("Localization process did not exit after kill")
            return False

    def _manages_localizer_command(self, command):
        return self._is_localizer_cmdline([str(part) for part in command])

    def _is_localizer_cmdline(self, cmdline):
        if not cmdline:
            return False
        for part in cmdline:
            if Path(part).name in LOCALIZER_EXECUTABLES:
                return True
        for index, part in enumerate(cmdline[:-3]):
            if Path(part).name != "ros2":
                continue
            if (
                cmdline[index + 1] == "run"
                and cmdline[index + 2] == LOCALIZER_PACKAGE
                and cmdline[index + 3] in LOCALIZER_EXECUTABLES
            ):
                return True
        return False

    def _localizer_pids(self):
        pids = []
        proc_dir = Path("/proc")
        if not proc_dir.is_dir():
            return pids
        own_pid = os.getpid()
        for entry in proc_dir.iterdir():
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            if pid == own_pid:
                continue
            try:
                raw_cmdline = (entry / "cmdline").read_bytes()
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
            cmdline = [part.decode("utf-8", errors="ignore") for part in raw_cmdline.split(b"\0") if part]
            if self._is_localizer_cmdline(cmdline):
                pids.append(pid)
        return pids

    def _signal_process_or_group(self, pid, sig):
        try:
            pgid = os.getpgid(pid)
        except ProcessLookupError:
            return
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            return
        except PermissionError:
            try:
                os.kill(pid, sig)
            except (ProcessLookupError, PermissionError):
                return

    def _cleanup_stale_localizer_processes(self):
        pids = self._localizer_pids()
        if not pids:
            return
        for pid in pids:
            self._signal_process_or_group(pid, signal.SIGTERM)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if not self._localizer_pids():
                return
            time.sleep(0.05)
        for pid in self._localizer_pids():
            self._signal_process_or_group(pid, signal.SIGKILL)

    def _process_payload_locked(self):
        running = self._process is not None and self._process.poll() is None
        return {
            "status": self._status,
            "running": running,
            "pid": self._process.pid if running else None,
            "startedAt": self._started_at,
            "stoppedAt": self._stopped_at,
            "lastError": self._last_error,
            "lastReturnCode": self._last_returncode,
            "logPath": self._log_path,
        }

    def _map_payload(self):
        with self._lock:
            return self._map_payload_locked()

    def _map_payload_locked(self):
        return dict(self._map or {})


_manager = None
_manager_lock = threading.Lock()


def get_localization_manager():
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = LocalizationManager()
        return _manager
