"""Fixed, reviewable SONIC service recipes and real host diagnostics."""
from __future__ import annotations

import copy
import json
import ipaddress
import re
import os
from pathlib import Path
import shutil
import socket
import signal
import subprocess
import threading
import time
import uuid
import hashlib

from console_support import ConsoleError, ProcessSupervisor, age, atomic_json, finite, now, read_json
from ros2_camera_bridge import default_ros2_config, validate_ros2_config


def default_config(mode):
    return {"interface": "eno1" if mode == "real" else "lo", "dds_domain": 0,
            "state_endpoint": "tcp://127.0.0.1:" + ("5557" if mode == "real" else "15557"),
            "pose_endpoint": "tcp://127.0.0.1:" + ("5556" if mode == "real" else "15556"),
            "camera_endpoint": "tcp://127.0.0.1:5555", "camera_source": "zmq", "ros2_camera": default_ros2_config(),
            "bms_topics": ["rt/bmsstate", "rt/lf/bmsstate"],
            "camera_keys": {"head": "ego_view", "left_wrist": "left_wrist", "right_wrist": "right_wrist"},
            "pico_calibration_confirmed": False, "source_max_age_seconds": .5,
            "prepare_timeout_seconds": 15}


class SystemDriver:
    def __init__(self, root, directory, app_root=None):
        self.root, self.directory = Path(root).resolve(), Path(directory).resolve()
        self.app_root = Path(app_root or Path(__file__).parent)
        self.supervisor = ProcessSupervisor(self.directory / "processes")
        self.config_path = self.directory / "runtime-config.json"
        self._cache, self._at = None, 0
        self._collection_ready,self._collection_at=False,0
        self.lock = threading.RLock()

    def config(self, mode, document=None):
        document=read_json(self.config_path) if document is None else document
        if not isinstance(document,dict) or not isinstance(document.get(mode,{}),dict):
            raise ConsoleError("运行配置必须按 real / sim 保存对象",412,"runtime_config")
        value = document.get(mode, {})
        result = {**default_config(mode), **value}
        # Endpoints are operator-edited local configuration, never arbitrary HTTP payloads.
        networks=[ipaddress.ip_network(n) for n in ['127.0.0.0/8','10.0.0.0/8','172.16.0.0/12','192.168.0.0/16']]
        for key in ("state_endpoint", "pose_endpoint", "camera_endpoint"):
            import re
            match=re.fullmatch(r"tcp://([0-9.]+):([1-9][0-9]{0,4})",result[key]) if isinstance(result[key],str) else None
            if not match:raise ConsoleError(f"{key} 必须为本机或局域网 IPv4 的 tcp://地址:端口",412,"runtime_config")
            try:address=ipaddress.ip_address(match.group(1))
            except ValueError:raise ConsoleError(f"{key} 的 IPv4 无效",412,"runtime_config")
            if not any(address in network for network in networks):
                raise ConsoleError("数据源地址限本机或局域网",412,"runtime_config")
            if int(match.group(2)) > 65535:
                raise ConsoleError("运行端口超出范围", 412, "runtime_config")
        if not isinstance(result["interface"], str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,15}",result["interface"]):
            raise ConsoleError("DDS 网卡配置无效", 412, "runtime_config")
        if not isinstance(result["camera_keys"],dict) or set(result["camera_keys"]) != {"head", "left_wrist", "right_wrist"}:
            raise ConsoleError("相机映射必须包含头部和左右腕", 412, "runtime_config")
        keys=list(result["camera_keys"].values())
        if any(not isinstance(k,str) or not k or len(k)>128 for k in keys) or len(set(keys))!=3:
            raise ConsoleError("三个相机来源键必须是不同的非空字符串",412,"runtime_config")
        if type(result["pico_calibration_confirmed"]) is not bool:
            raise ConsoleError("标定确认必须为布尔值",412,"runtime_config")
        for key,lower,upper in [("source_max_age_seconds",.1,2),("prepare_timeout_seconds",0,60)]:
            if not finite(result[key]) or not lower<=result[key]<=upper:
                raise ConsoleError(key+" 配置超出范围",412,"runtime_config")
        if type(result["dds_domain"]) is not int or not 0<=result["dds_domain"]<=232:
            raise ConsoleError("DDS domain 配置无效",412,"runtime_config")
        if result["camera_source"] not in {"zmq", "ros2"}:
            raise ConsoleError("camera_source 必须为 zmq 或 ros2",412,"runtime_config")
        try:result["ros2_camera"] = validate_ros2_config(result["ros2_camera"])
        except ValueError as exc:raise ConsoleError(str(exc),412,"runtime_config") from exc
        if not isinstance(result["bms_topics"],list) or not result["bms_topics"] or len(result["bms_topics"])>4 or any(not isinstance(v,str) or not v.startswith("rt/") or len(v)>128 for v in result["bms_topics"]):
            raise ConsoleError("BMS 话题配置无效",412,"runtime_config")
        return result

    def collection_available(self):
        with self.lock:
            if time.monotonic()-self._collection_at < (60 if self._collection_ready else 10):
                return self._collection_ready
            python=self.app_root/".venv_collection/bin/python"
            if python.is_file():
                code,_=self.command([python,"-I","-c","from gear_sonic.scripts.run_data_exporter import GrootDataCollector; from gear_sonic.data.exporter import Gr00tDataExporter"],8)
                self._collection_ready=code==0
            else:self._collection_ready=False
            self._collection_at=time.monotonic()
            return self._collection_ready

    def external_recorders(self):
        found=[]
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():continue
            try:
                arguments=(entry/'cmdline').read_bytes().decode(errors='replace').split('\0')
                script=any(arg.endswith('/run_data_exporter.py') or arg=='run_data_exporter.py' for arg in arguments)
                module=any(arg=='-m' and i+1<len(arguments) and arguments[i+1]=='gear_sonic.scripts.run_data_exporter' for i,arg in enumerate(arguments))
                if script or module:
                    if (entry/'cwd').resolve()==self.root:found.append(int(entry.name))
            except OSError:pass
        return found

    def pc_service_status(self):
        processes=[]
        unity=[]
        owned=True
        root=self.root/"external_dependencies/XRoboToolkit-PC-Service-runtime"
        expected={"RoboticsServiceProcess":root/"RoboticsServiceProcess",
                  "RobotLinuxDemo.x86_64":root/"SDKDemo/RobotUnityDemo/RobotLinuxDemo.x86_64"}
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():continue
            try:
                executable=(entry/'exe').resolve(strict=True)
                if executable.name in expected:
                    owned=owned and executable==expected[executable.name] and entry.stat().st_uid==os.getuid()
                    (processes if executable.name=='RoboticsServiceProcess' else unity).append(int(entry.name))
            except OSError:pass
        grpc=self.port(60061)
        if grpc and not processes:owned=False
        stopped=(self.root/"outputs/xrobotoolkit/service.stopped").exists()
        state='running' if len(processes)==1 and grpc else 'failed' if grpc or processes else 'stopped' if stopped else 'offline'
        detail="PC Service 进程与本机 gRPC 已就绪；追踪有效性单独检查" if state=='running' else "已停止 PC Service 与 Unity 3D；可显式重新启动" if state=='stopped' and not unity else "等待唯一的 PC Service 进程和 gRPC 就绪"
        return {"state":state,"owned":owned,"unity_running":bool(unity),"observed_at":now(),"detail":detail}

    def service_stop_blockers(self, service):
        names={"g1_deploy_onnx_ref","run_vla_inference.py","pico_manager_thread_server.py",
               "run_data_exporter.py","run_sim_loop.py","launch_data_collection.py",
               "launch_inference.py","console_real_worker.py"}
        modules={"gear_sonic.scripts.run_vla_inference","gear_sonic.scripts.run_data_exporter",
                 "gear_sonic.scripts.pico_manager_thread_server"}
        users=[]
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():continue
            try:
                args=(entry/'cmdline').read_bytes().decode(errors='replace').split('\0')
                if any(Path(a).name in names or a in modules for a in args):users.append(int(entry.name))
            except OSError:pass
        blockers=["SONIC、遥操作或采集进程仍在运行，请先结束任务"] if users else []
        if service=="docker":
            state=self.container()
            if state.get("running"):
                code,text=self.command(["docker","top",state.get("container_id") or "sonic-4070","-eo","pid,comm"],4)
                if code:blockers.append("无法核验容器内进程，暂不能停止")
                else:
                    rows=[line.split(None,1) for line in text.splitlines()[1:] if line.strip()]
                    if not rows or any(len(row)!=2 or not row[0].isdigit() for row in rows):
                        blockers.append("容器进程列表无效，暂不能停止")
                    elif any(row[1].strip() not in {"docker-init","tini","sleep"} for row in rows):
                        blockers.append("容器内有活动进程，请先退出控制器、构建或终端会话")
        return blockers

    def stop_service(self, service):
        blockers=self.service_stop_blockers(service)
        if blockers:raise ConsoleError("、".join(blockers),409,"service_in_use")
        if service=="docker":
            state=self.container()
            if not state.get("owned"):raise ConsoleError("容器不存在或不属于本项目，拒绝停止",409,"service_not_owned")
            container_id=state.get("container_id","")
            if not re.fullmatch(r"[0-9a-f]{64}",container_id):raise ConsoleError("无法确认容器身份",409,"service_not_owned")
            if state.get("running"):
                code,text=self.command(["docker","stop","--timeout","15",container_id],25)
                if code:raise ConsoleError("容器停止失败："+text[-400:],503,"service_stop_failed")
            code,text=self.command(["docker","inspect","--format","{{.State.Running}}",container_id],4)
            if code or text.strip()!="false":raise ConsoleError("尚未确认容器停止，请刷新状态",503,"service_stop_unconfirmed")
            result={"message":"SONIC 容器已停止，模型和容器文件保留","service_id":service,"state":"stopped"}
        elif service=="pc_service":
            if not self.pc_service_status().get("owned"):raise ConsoleError("XRoboToolkit属于其他运行目录，拒绝停止",409,"service_not_owned")
            runtime=self.root/"external_dependencies/XRoboToolkit-PC-Service-runtime"
            code,text=self.command(["env","XROBOTOOLKIT_RUNTIME_DIR="+str(runtime),"bash",str(self.root/"run_xrobotoolkit.sh"),"stop"],35)
            if code:raise ConsoleError("XRoboToolkit停止未确认："+text[-500:],503,"service_stop_failed")
            state=self.pc_service_status()
            if state["state"]!="stopped" or state["unity_running"]:raise ConsoleError("尚未确认XRoboToolkit完全停止，请刷新状态",503,"service_stop_unconfirmed")
            result={"message":"XRoboToolkit PC Service 与 Unity 3D 已停止","service_id":service,"state":"stopped"}
        else:raise ConsoleError("不支持停止该服务",400,"unsupported_service")
        self._cache=None
        self._at=0
        return result

    def command(self, argv, timeout=10):
        try:
            result = subprocess.run([str(v) for v in argv], cwd=self.root, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=timeout)
            return result.returncode, (result.stdout + result.stderr)[-12000:]
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 124, str(exc)[:500]

    @staticmethod
    def port(port):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=.15):
                return True
        except OSError:
            return False

    def inspect(self, force=False):
        with self.lock:
            if self._cache is not None and not force and time.monotonic()-self._at < 10:
                return copy.deepcopy(self._cache)
            if force:self._collection_at=0
            checks = []
            def add(key, label, ok, detail, blocking=True):
                checks.append({"id": key, "label": label, "status": "passed" if ok else "blocked" if blocking else "warning",
                               "detail": detail, "scope": "环境", "source": "4070 系统检查", "observed_at": now()})
            disk = shutil.disk_usage(self.root)
            add("disk", "数据存储空间", disk.free > 5*1024**3, f"可用 {disk.free/1024**3:.1f} GiB")
            code, gpu = self.command(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"], 5)
            gpu_ok = code == 0
            add("gpu", "GPU / NVIDIA 驱动", code == 0, gpu.strip())
            code, image = self.command(["docker", "image", "inspect", "g1-deploy-dev:latest", "--format", "{{.Id}}"], 5)
            add("docker_image", "Docker 与 SONIC 镜像", code == 0, image.strip())
            container = self.container()
            script = self.root / "gear_sonic_deploy/docker/sonic-runtime.sh"
            add("runtime_script", "项目 Docker 启动入口", script.is_file(), str(script))
            binary = self.root / "gear_sonic_deploy/target/release/g1_deploy_onnx_ref"
            add("controller_binary", "SONIC 控制程序", binary.is_file() and os.access(binary, os.X_OK),
                str(binary), blocking=False)
            model_names = ["policy/release/model_decoder.onnx", "policy/release/model_encoder.onnx", "planner/target_vel/V2/planner_sonic.onnx"]
            missing = [name for name in model_names if not (self.root/"gear_sonic_deploy"/name).is_file()]
            add("models", "SONIC 模型文件", not missing, "三个 ONNX 模型齐全" if not missing else "缺失："+", ".join(missing))
            python = self.root / ".venv_teleop/bin/python"
            modules = ["gear_sonic", "zmq", "cv2", "msgpack", "msgpack_numpy", "unitree_sdk2py", "xrobotoolkit_sdk"]
            code, modules_result = self.command([python, "-I", "-c", "import importlib.util,json; print(json.dumps({x:bool(importlib.util.find_spec(x)) for x in " + repr(modules) + "}))"], 8)
            try:
                found = json.loads(modules_result) if code == 0 else {}
            except ValueError:
                found = {}
            add("teleop_env", "遥操作 SDK 与读取环境", all(found.get(x) for x in modules),
                "依赖可定位；实际读数由订阅器验证" if all(found.get(x) for x in modules) else "缺失："+", ".join(x for x in modules if not found.get(x)))
            service = self.root / "external_dependencies/XRoboToolkit-PC-Service-runtime/RoboticsServiceProcess"
            add("pc_service_files", "XRoboToolkit PC Service 文件", service.is_file(), str(service))
            collection_python = self.app_root / ".venv_collection/bin/python"
            add("collection_env", "独立采集环境", self.collection_available(),
                "官方导出器依赖可实际导入" if self._collection_ready else "依赖尚未安装完整或导入失败；运行 scripts/install_collection.sh", blocking=False)
            self._cache = {"checks": checks, "container": container, "gpu": gpu.strip() if gpu_ok else None,
                           "disk_free_bytes": disk.free, "observed_at": now()}
            self._at = time.monotonic()
            return copy.deepcopy(self._cache)

    def container(self):
        code, text = self.command(["docker", "container", "inspect", "--format",
            '{"id":{{json .Id}},"running":{{json .State.Running}},"labels":{{json .Config.Labels}}}', "sonic-4070"], 4)
        if code:
            return {"state": "offline", "detail": "SONIC 容器未创建或 Docker 不可用"}
        try:
            data = json.loads(text)
            labels = data.get("labels") or {}
            owned = labels.get("io.robot-station.sonic-runtime") == "1" and labels.get("io.robot-station.sonic-root") == str(self.root)
            return {"state": "ready" if data["running"] and owned else "stopped" if owned else "failed",
                    "running": bool(data["running"]), "owned": owned, "container_id":data.get("id"),
                    "detail": "项目待命容器，无自动运动" if owned else "同名容器属于其他入口，禁止接管"}
        except (KeyError, ValueError, IndexError):
            return {"state": "failed", "detail": "Docker 状态无法解析"}

    def telemetry(self, mode):
        row = read_json(self.directory / "telemetry" / mode / "status.json")
        if row.get("mode") != mode or row.get('worker_version')!=self.probe_version() or not self.supervisor.running("probe-"+mode) or age(row.get("heartbeat_at")) > 3:
            return {}
        return row

    def probe_version(self):
        return hashlib.sha256((self.app_root/'console_probe_worker.py').read_bytes()+(self.app_root/'console_support.py').read_bytes()+(self.app_root/'sonic_feedback.py').read_bytes()).hexdigest()[:16]

    def start_probe(self, mode, start_cameras=True):
        if start_cameras:
            self.start_camera_source(mode)
            (self.directory/"camera-paused").unlink(missing_ok=True)
        config = {**self.config(mode),'_worker_version':self.probe_version()}
        path = self.directory / "telemetry" / mode / "config.json"
        if path.is_file() and read_json(path) != config and self.supervisor.running("probe-"+mode):
            self.supervisor.stop("probe-"+mode)
        atomic_json(path, config)
        return self.supervisor.start("probe-"+mode, [str(self.root/".venv_teleop/bin/python"),
            str(self.app_root/"console_probe_worker.py"), "--sonic-root", str(self.root),
            "--directory", str(path.parent), "--config", str(path), "--mode", mode], self.root)

    def start_camera_source(self, mode):
        from console_camera_source import CameraSourceManager
        return CameraSourceManager(self).start(mode)

    def camera_source_status(self, mode):
        from console_camera_source import CameraSourceManager
        return CameraSourceManager(self).status(mode)

    def stop_camera_source(self):
        from console_camera_source import CameraSourceManager
        return CameraSourceManager(self).stop()

    def run_recipe(self, recipe, cancelled, log):
        commands = {
            "docker_start": ["bash", str(self.root/"gear_sonic_deploy/docker/sonic-runtime.sh"), "start"],
            "docker_build": ["bash", str(self.root/"gear_sonic_deploy/docker/sonic-runtime.sh"), "build"],
            "docker_check": ["bash", str(self.root/"gear_sonic_deploy/docker/sonic-runtime.sh"), "check"],
            "pc_service_start": ["bash", str(self.root/"run_xrobotoolkit.sh"), "service"],
        }
        if recipe not in commands:
            raise ConsoleError("未定义的服务操作", 400)
        cancel_marker=None
        if recipe=="docker_build":
            state=self.container()
            if not state.get("owned") or not state.get("running"):
                raise ConsoleError("构建前项目容器必须已就绪",412,"container_not_ready")
            token=uuid.uuid4().hex
            cancel_marker=self.root/"gear_sonic_deploy/build/.robot-station-jobs"/(token+".cancel")
            cancel_marker.parent.mkdir(parents=True,exist_ok=True)
            # The cancellation marker is on the existing bind mount. The container
            # wrapper owns a new process group, and only terminates that build.
            script='''source /opt/ros/humble/setup.bash
set -euo pipefail
setsid bash -c 'set -e; cmake -S /workspace/g1_deploy -B /workspace/g1_deploy/build -DCMAKE_BUILD_TYPE=Release -DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=/usr/src/googletest; cmake --build /workspace/g1_deploy/build --target g1_deploy_onnx_ref --parallel 2' &
build_pid=$!
stop_build() { kill -TERM -- -"$build_pid" 2>/dev/null || true; }
trap stop_build TERM INT EXIT
while kill -0 "$build_pid" 2>/dev/null; do
 if [[ -f /workspace/g1_deploy/build/.robot-station-jobs/TOKEN.cancel ]]; then
  stop_build
  wait "$build_pid" || true
  exit 130
 fi
 sleep 0.2
done
wait "$build_pid"
trap - EXIT
'''.replace('TOKEN',token)
            commands[recipe]=["docker","exec","sonic-4070","bash","-lc",script]
        process = subprocess.Popen(commands[recipe], cwd=self.root, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        start = time.monotonic()
        timeout = 600 if recipe == "docker_build" else 45
        while process.poll() is None:
            if cancelled.is_set() or time.monotonic()-start > timeout:
                if cancel_marker is not None:
                    cancel_marker.touch()
                else:os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10 if cancel_marker else 5)
                except subprocess.TimeoutExpired:
                    raise ConsoleError("准备子进程尚未退出，请检查日志", 409, "stop_timeout")
                if cancelled.is_set():
                    raise ConsoleError("准备任务已取消", 409, "cancelled")
                raise ConsoleError("服务准备超时", 504, "recipe_timeout")
            cancelled.wait(.1)
        if process.returncode:
            raise ConsoleError(f"{recipe} 执行失败，请查看任务日志", 412, "recipe_failed")
        self._at = 0

    def camera_frame(self, mode, camera):
        if camera not in {"head", "left_wrist", "right_wrist"}:
            raise ConsoleError("未知相机", 404)
        data = self.telemetry(mode).get("cameras", {}).get(camera, {})
        path = self.directory/"telemetry"/mode/(camera+".jpg")
        if age(data.get("observed_at")) > 5 or not path.is_file():
            raise ConsoleError("相机尚无新鲜帧", 503, "camera_offline")
        return path.read_bytes(), data["observed_at"]
