import json
import os
import signal
import subprocess
import threading
import time
from pathlib import Path

from modules.logger import get_logger
from modules.map import get_mapping_manager
from modules.ros_io import get_ros_reader, get_ros_writer


ROOT_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT_DIR / "logs" / "localization"
DEFAULT_LOCALIZER_COMMAND = (
    "ros2",
    "run",
    "robot_station_mapper",
    "robot_station_localizer_node",
)
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
        "LOC-MAP-LIST": 503,
        "LOC-DEPENDENCY": 503,
        "LOC-START-FAILED": 500,
        "LOC-STOP-FAILED": 500,
    }
    return mapping.get(result.get("code", ""), 500)


def _command_from_env():
    command_text = os.environ.get("ROBOT_STATION_LOCALIZER_COMMAND", "")
    if command_text.strip():
        return tuple(command_text.split())
    return DEFAULT_LOCALIZER_COMMAND


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


class LocalizationManager:
    def __init__(self, localizer_command=None):
        self.localizer_command = tuple(localizer_command or _command_from_env())
        self._lock = threading.RLock()
        self._process = None
        self._map = None
        self._status = "stopped"
        self._started_at = ""
        self._stopped_at = ""
        self._last_error = ""
        self._last_returncode = None
        self._log_path = ""

    def status(self):
        with self._lock:
            self._refresh_locked()
            process_payload = self._process_payload_locked()

        ros_status = self._read_localization_status()
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
            localizerCommand=list(self.localizer_command),
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
            command = self._build_command(map_entry, settings)
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            self._log_path = str(LOG_DIR / f"localizer_{time.strftime('%Y%m%d_%H%M%S')}.log")
            try:
                with Path(self._log_path).open("ab") as log_file:
                    log_file.write((" ".join(command) + "\n").encode("utf-8"))
                    self._process = subprocess.Popen(
                        command,
                        cwd=str(ROOT_DIR),
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

        stopped = self._terminate_process(process)

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
        return {
            "cloudTopic": _clean_topic(payload.get("cloudTopic"), "/rslidar_points"),
            "initialPoseTopic": _clean_topic(payload.get("initialPoseTopic"), "/initialpose"),
            "poseTopic": _clean_topic(payload.get("poseTopic"), "/localization/pose"),
            "statusTopic": _clean_topic(payload.get("statusTopic"), "/localization/status"),
            "mapFrame": str(payload.get("mapFrame") or "map").strip() or "map",
            "baseFrame": str(payload.get("baseFrame") or "base_link").strip() or "base_link",
            "maxFailedFrames": _safe_int(payload.get("maxFailedFrames"), 3, 1, 20),
            "minSourcePoints": _safe_int(payload.get("minSourcePoints"), 50, 1, 100000),
        }

    def _build_command(self, map_entry, settings):
        return [
            *self.localizer_command,
            "--ros-args",
            "-p",
            f"map_path:={map_entry['mapPath']}",
            "-p",
            f"map_name:={map_entry['name']}",
            "-p",
            f"cloud_topic:={settings['cloudTopic']}",
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
        ]

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

    def _refresh_locked(self):
        if self._process is None:
            return
        return_code = self._process.poll()
        if return_code is None:
            if self._status == "starting":
                self._status = "running"
            return
        self._last_returncode = return_code
        self._process = None
        self._status = "stopped" if return_code == 0 else "failed"
        self._stopped_at = time.strftime("%H:%M:%S")
        if return_code != 0:
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
