"""Launch the project-local XRoboToolkit PC Service and Unity client on Linux."""

import argparse
from contextlib import ExitStack
import fcntl
import json
import os
from pathlib import Path
import socket
import select
import signal
import subprocess
import time


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RUNTIME = PROJECT_ROOT / "external_dependencies/XRoboToolkit-PC-Service-runtime"
LOG_DIR = PROJECT_ROOT / "outputs/xrobotoolkit"
GRPC_PORT = 60061


def runtime_dir() -> Path:
    return Path(os.environ.get("XROBOTOOLKIT_RUNTIME_DIR", DEFAULT_RUNTIME)).expanduser().resolve()


def runtime_env() -> dict[str, str]:
    root = runtime_dir()
    env = os.environ.copy()
    paths = {
        "LD_LIBRARY_PATH": [root, root / "lib", root / "SDK/x64"],
        "QT_PLUGIN_PATH": [root / "plugins"],
        "QT_QML_PATH": [root / "qml"],
        "QML2_IMPORT_PATH": [root / "qml"],
    }
    for key, directories in paths.items():
        env[key] = ":".join([*(str(p) for p in directories), *([env[key]] if env.get(key) else [])])
    return env


def _processes(executable_name: str) -> list[dict]:
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            executable = (entry / "exe").readlink()
            if executable.name == executable_name:
                found.append({"pid": int(entry.name), "executable": str(executable),
                              "start_ticks": (entry / "stat").read_text().rsplit(")", 1)[1].split()[19]})
        except OSError:
            continue
    return sorted(found, key=lambda process: process["pid"])


def _grpc_ready() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", GRPC_PORT), timeout=0.25):
            return True
    except OSError:
        return False


def _validate_files() -> None:
    root = runtime_dir()
    for name in (
        "RoboticsServiceProcess",
        "SDK/x64/libPXREARobotSDK.so",
        "SDKDemo/RobotUnityDemo/RobotLinuxDemo.x86_64",
        "SDKDemo/RobotUnityDemo/UnityPlayer.so",
        "SDKDemo/RobotUnityDemo/RobotLinuxDemo_Data/Managed/Assembly-CSharp.dll",
        "plugins/platforms/libqoffscreen.so",
    ):
        if not (root / name).is_file():
            raise RuntimeError(f"XRoboToolkit runtime file missing: {root / name}")
    for name in ("RoboticsServiceProcess", "SDKDemo/RobotUnityDemo/RobotLinuxDemo.x86_64"):
        if not os.access(root / name, os.X_OK):
            raise RuntimeError(f"XRoboToolkit executable permission missing: {root / name}")


def ensure_service(timeout: float = 15.0, *, explicit_start: bool = False) -> dict:
    """Reuse a running PC Service, or start this checkout's copy and wait for gRPC."""
    _validate_files()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "service.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        marker = LOG_DIR / "service.stopped"
        if marker.exists():
            if not explicit_start:
                raise RuntimeError("XRoboToolkit was stopped by the operator; explicitly start it before use.")
            marker.unlink()
        services = _processes("RoboticsServiceProcess")
        if len(services) > 1:
            raise RuntimeError("Multiple XRoboToolkit services are running; inspect status before continuing.")
        child = None
        reused = bool(services)
        if not reused:
            if _grpc_ready():
                raise RuntimeError(f"Port {GRPC_PORT} is occupied without a visible XRoboToolkit service.")
            env = runtime_env()
            if not env.get("DISPLAY") and not env.get("WAYLAND_DISPLAY"):
                env.setdefault("QT_QPA_PLATFORM", "offscreen")
            with (LOG_DIR / "service.log").open("ab") as log:
                child = subprocess.Popen(
                    [str(runtime_dir() / "RoboticsServiceProcess")],
                    cwd=runtime_dir(),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            services = [{"pid": child.pid, "executable": str(runtime_dir() / "RoboticsServiceProcess")}]
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if child is not None and child.poll() is not None:
                raise RuntimeError(
                    f"XRoboToolkit service exited ({child.returncode}); see {LOG_DIR / 'service.log'}"
                )
            if not Path(f"/proc/{services[0]['pid']}").exists():
                raise RuntimeError("The existing XRoboToolkit service exited while waiting for gRPC.")
            if _grpc_ready():
                result = {**services[0], "reused": reused, "grpc": f"127.0.0.1:{GRPC_PORT}"}
                action = "Reusing" if reused else "Started"
                print(f"{action} XRoboToolkit PC Service: {json.dumps(result)}", flush=True)
                return result
            time.sleep(0.1)
        if child is not None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass
        raise RuntimeError(f"XRoboToolkit gRPC did not become ready; see {LOG_DIR / 'service.log'}")


def _active_users() -> list[int]:
    """Visible robot controllers/teleop/recorders must exit before infrastructure stops."""
    names = {"g1_deploy_onnx_ref", "run_vla_inference.py", "pico_manager_thread_server.py",
             "run_data_exporter.py", "run_sim_loop.py", "launch_data_collection.py",
             "launch_inference.py", "console_real_worker.py"}
    found = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            args = (proc / "cmdline").read_bytes().decode(errors="replace").split("\0")
            if any(Path(arg).name in names or arg in {
                "gear_sonic.scripts.run_vla_inference", "gear_sonic.scripts.run_data_exporter",
                "gear_sonic.scripts.pico_manager_thread_server"} for arg in args):
                found.append(int(proc.name))
        except OSError:
            continue
    return sorted(found)


def stop_runtime(timeout: float = 8.0) -> dict:
    """Stop only this runtime's processes using stable pidfds; no forced kill."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "service.lock").open("a") as lock, ExitStack() as stack:
        fcntl.flock(lock, fcntl.LOCK_EX)
        users = _active_users()
        if users:
            raise RuntimeError(f"SONIC/teleop/recording still active (PIDs {users}); stop those tasks first.")
        root = runtime_dir()
        expected = {"RoboticsServiceProcess": root / "RoboticsServiceProcess",
                    "RobotLinuxDemo.x86_64": root / "SDKDemo/RobotUnityDemo/RobotLinuxDemo.x86_64"}
        rows = [row for name in expected for row in _processes(name)]
        if any(Path(row["executable"]) != expected[Path(row["executable"]).name] for row in rows):
            raise RuntimeError("Another XRoboToolkit installation is active; refusing to stop it.")
        if _grpc_ready() and not any(Path(row["executable"]).name == "RoboticsServiceProcess" for row in rows):
            raise RuntimeError("gRPC port is occupied without an owned service; refusing to stop it.")
        handles = []
        for row in rows:
            proc = Path(f"/proc/{row['pid']}")
            try:
                fd = os.pidfd_open(row["pid"])
                stack.callback(os.close, fd)
                if (proc.stat().st_uid != os.getuid() or (proc / "exe").resolve(strict=True) != Path(row["executable"])
                    or (proc / "stat").read_text().rsplit(")", 1)[1].split()[19] != row["start_ticks"]):
                    raise RuntimeError("Process identity/ownership changed; refusing to signal it.")
                handles.append((fd, row["pid"]))
            except ProcessLookupError:
                continue
            except FileNotFoundError:
                continue
        # Implicit PICO/SDK preparation must not immediately restart an operator-stopped service.
        (LOG_DIR / "service.stopped").touch()
        poller = select.poll()
        pending = {}
        for fd, pid in handles:
            try:
                signal.pidfd_send_signal(fd, signal.SIGTERM)
            except ProcessLookupError:
                continue
            poller.register(fd, select.POLLIN)
            pending[fd] = pid
        deadline = time.monotonic() + timeout
        while pending and time.monotonic() < deadline:
            for fd, _ in poller.poll(min(200, max(1, int((deadline-time.monotonic())*1000)))):
                poller.unregister(fd)
                pending.pop(fd, None)
        if pending:
            raise RuntimeError(f"XRoboToolkit did not exit before timeout (PIDs {list(pending.values())}); no forced kill sent.")
        if _processes("RoboticsServiceProcess") or _processes("RobotLinuxDemo.x86_64") or _grpc_ready():
            raise RuntimeError("XRoboToolkit stop could not be confirmed; inspect current status.")
        return {"stopped": True, "pids": [pid for _, pid in handles], "unity_stopped": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="3d", choices=("3d", "service", "status", "check", "stop"))
    args = parser.parse_args()
    if args.command == "status":
        print(json.dumps({
            "runtime": str(runtime_dir()),
            "service": _processes("RoboticsServiceProcess"),
            "unity": _processes("RobotLinuxDemo.x86_64"),
            "grpc_ready": _grpc_ready(),
            "log": str(LOG_DIR / "service.log"),
        }, indent=2))
        return 0
    if args.command == "stop":
        print(json.dumps(stop_runtime()))
        return 0
    _validate_files()
    if args.command == "check":
        for name in (
            "RoboticsServiceProcess",
            "SDK/x64/libPXREARobotSDK.so",
            "SDKDemo/RobotUnityDemo/RobotLinuxDemo.x86_64",
            "SDKDemo/RobotUnityDemo/UnityPlayer.so",
        ):
            result = subprocess.run(
                ["ldd", str(runtime_dir() / name)], env=runtime_env(), capture_output=True, text=True
            )
            missing = [line.strip() for line in result.stdout.splitlines() if "not found" in line]
            if result.returncode or missing:
                raise RuntimeError(f"Dependency check failed for {name}: {missing or result.stderr}")
            if "/opt/apps/roboticsservice" in result.stdout:
                raise RuntimeError(f"Dependency check still resolves the old installation for {name}")
        print(f"XRoboToolkit runtime and shared libraries OK: {runtime_dir()}")
        return 0
    if args.command == "3d" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        raise RuntimeError(
            "No graphical session. Run this command in an Ubuntu desktop terminal, or use 'service'."
        )
    ensure_service(explicit_start=True)
    if args.command == "service":
        return 0
    with (LOG_DIR / "service.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (LOG_DIR / "service.stopped").exists():
            raise RuntimeError("XRoboToolkit was stopped before Unity could start.")
        existing = _processes("RobotLinuxDemo.x86_64")
        if existing:
            print(f"Unity 3D client is already running: {json.dumps(existing)}")
            return 0
        unity_dir = runtime_dir() / "SDKDemo/RobotUnityDemo"
        child = subprocess.Popen([str(unity_dir / "RobotLinuxDemo.x86_64")], cwd=unity_dir, env=runtime_env())
    return child.wait()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"XRoboToolkit: {error}", flush=True)
        raise SystemExit(1) from None
