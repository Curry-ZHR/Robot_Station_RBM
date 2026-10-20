"""Versioned backend for host checks, no-motion preparation and recording tasks."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import threading
import time
import uuid
import fcntl

from console_driver import SystemDriver
from console_support import ConsoleError, age, atomic_json, finite, now, read_json
from console_collection import CollectionManager
from console_configuration import ConfigurationStore
from console_poses import PoseStore, trajectory
from console_manual import ManualControl
from console_real import RealManualControl
from console_diagnostics import Diagnostics

PROFILE_ID = "unitree-g1-29"
PREFIX = "/api/v1/console"
STAGES = [("environment", "环境自检"), ("runtime", "准备 SONIC"), ("sensors", "相机就绪"),
          ("input", "输入源就绪"), ("robot", "机器人反馈")]


class ConsoleRuntime:
    def __init__(self, adapter, workspace, driver=None):
        self.adapter, self.workspace = adapter, workspace
        self.directory = adapter.runtime_dir / "console"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.instance_lock=(self.directory/"backend.lock").open("a")
        try:fcntl.flock(self.instance_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.instance_lock.close()
            raise ConsoleError("同一工作目录已有执行后端在运行",409,"backend_owner_conflict") from exc
        self.driver = driver or SystemDriver(adapter.repo_root, self.directory)
        self.lock = threading.RLock()
        self.path = self.directory / "state.json"
        self.state = read_json(self.path, {"revision": 0, "events": [], "jobs": {}, "idempotency": {}, "collection": {}})
        self.cancel_flags = {}
        self.threads = []
        self.recorder = CollectionManager(adapter,self.driver,self.directory)
        profile_path = self.driver.app_root/"static/assets/g1/profile.json"
        if not profile_path.is_file():
            profile_path = self.driver.app_root.parent/"static/assets/g1/profile.json"
        self.profile = read_json(profile_path)
        self.joint_names = self.profile.get("body_joints", [])
        self.manual = ManualControl(self.driver,self.directory,self.profile)
        self.real_manual = RealManualControl(self.driver,self.directory,self.profile)
        self.configuration = ConfigurationStore(self.driver) if hasattr(self.driver,"directory") else None
        self.poses = PoseStore(self.directory,self.profile)
        self.diagnostics = Diagnostics(self)
        for job in self.state["jobs"].values():
            if job["state"] in {"running", "pending"}:
                job.update(state="failed", message="网页服务重启；请查看实际服务状态后重新准备", updated_at=now())
                for step in job["steps"]:
                    if step["state"] in {"pending", "running"}:
                        step["state"] = "failed"
        self._save()

    def _save(self):
        atomic_json(self.path, self.state)

    def _changed(self):
        self.state["revision"] += 1
        self._save()

    def event(self, title, detail="", level="info"):
        self.state["events"].insert(0, {"id": uuid.uuid4().hex, "at": now(), "level": level,
                                      "title": title, "detail": detail, "source": "Robot Station"})
        self.state["events"] = self.state["events"][:100]

    @staticmethod
    def validate_mode(mode, profile=PROFILE_ID):
        if not isinstance(mode,str) or mode not in {"real", "sim"} or profile != PROFILE_ID:
            raise ConsoleError("运行模式或机器人配置无效")

    def snapshot(self, mode="sim", profile=PROFILE_ID):
        self.validate_mode(mode, profile)
        system = self.driver.inspect()
        telemetry = self.driver.telemetry(mode)
        config = self.driver.config(mode)
        camera_source = self.driver.camera_source_status(mode) if hasattr(self.driver, "camera_source_status") else {"kind": "zmq", "state": "external"}
        manual = self.manual.status() if mode == "sim" else self.real_manual.status()
        manual_feedback = manual.get("joints") and age(manual.get("observed_at"))<.3
        robot = manual if (mode == "sim" and manual["state"] == "running") or (mode == "real" and manual_feedback) else telemetry.get("robot", {})
        valid = age(robot.get("observed_at")) <= 5 and len(robot.get("joints", [])) == 29
        joint_map = {r.get("name"): r for r in robot.get("joints", []) if isinstance(r, dict)}
        valid = valid and len(joint_map) == 29 and set(joint_map) == set(self.joint_names) and all(finite(r.get("position_rad")) for r in joint_map.values())
        robot = {**robot, "connected": bool(valid), "stale": not valid, "observed_at": robot.get("observed_at"),
                 "joints": list(joint_map.values()) if valid else [], "owner": manual.get("owner"), "mode": "MANUAL_SIM" if mode == "sim" and manual["state"] == "running" else robot.get("mode", "UNKNOWN"), "initialized": (mode == "sim" and manual["state"] == "running") or (mode == "real" and bool(manual.get("initialized"))), "initialization_profile_id": "mujoco-fixed-base" if mode == "sim" else "g1-sdk2-hg-pr"}
        battery = {} if mode == "sim" and manual["state"] == "running" else telemetry.get("battery", {})
        battery_valid = bool(valid and age(battery.get("observed_at")) <= 15 and finite(battery.get("percent")) and 0 <= battery["percent"] <= 100)
        battery = {**battery, "percent": battery.get("percent") if battery_valid else None,
                   "observed_at": battery.get("observed_at"), "stale": not battery_valid}
        cameras = []
        for name in ("head", "left_wrist", "right_wrist"):
            row = telemetry.get("cameras", {}).get(name, {})
            live = row.get("state") == "streaming" and age(row.get("observed_at")) <= 5
            if camera_source["kind"] == "ros2":
                live = live and camera_source.get("views", {}).get(name, {}).get("live") is True and "synchronization" not in camera_source.get("errors", {})
            cameras.append({**row, "id": name, "state": "streaming" if live else "offline", "stale": not live,
                            "observed_at": row.get("observed_at"), "url": row.get("url", "") if live else ""})
        pico = telemetry.get("pico", {})
        pico_ready = pico.get("body_ready") is True and age(pico.get("observed_at")) <= 2
        controller = telemetry.get("controller", {})
        controller_ready = age(controller.get("observed_at")) <= 2
        services = {"docker": {**system["container"], "observed_at": system["observed_at"]},
                    "pc_service": self.driver.pc_service_status(),
                    "controller": {"state": "running" if controller_ready else "offline", "observed_at": controller.get("observed_at"),
                                   "detail": "收到持续更新的 SONIC 反馈" if controller_ready else "等待 SONIC g1_debug 数据"},
                    "cameras": {"state": "running" if all(c["state"] == "streaming" for c in cameras) else "offline",
                                "detail": f"{sum(c['state']=='streaming' for c in cameras)} / 3 路有效帧", "observed_at": now()},
                    "exporter": {"state": "offline", "detail": "采集任务未准备", "observed_at": now()}}
        if camera_source["kind"] == "ros2":
            services["cameras"]["detail"] = f"ROS 2 Domain {camera_source['domain_id']} · {camera_source['state']} · "+services["cameras"]["detail"]
            if camera_source["state"] == "failed":
                services["cameras"].update(state="failed", detail=camera_source["message"])
        checks = copy.deepcopy(system["checks"])
        for key, label, ok, detail in [("robot_feedback", "G1 29 关节反馈", valid, robot.get("source", "等待只读订阅器收到有效反馈")),
            ("camera_frames", "三路相机有效帧", all(c["state"] == "streaming" for c in cameras), services["cameras"]["detail"]),
            ("pico_tracking", "PICO 身体追踪", pico_ready, "设备时间戳持续更新" if pico_ready else "等待 PICO 连接并发送身体追踪"),
            ("pico_calibration", "PICO / 腿部追踪器标定确认", config["pico_calibration_confirmed"] is True, "现场标定结果由运行配置确认"),
            ("controller_feedback", "SONIC 控制器反馈", controller_ready, services["controller"]["detail"])]:
            checks.append({"id": key, "label": label, "status": "passed" if ok else "blocked", "detail": detail,
                           "scope": "设备", "source": "只读数据订阅"})
        interface = Path("/sys/class/net") / config["interface"]
        carrier = read_text(interface/"carrier")
        checks.append({"id": "network", "label": "机器人网卡链路", "status": "passed" if carrier == "1" else "warning",
                       "detail": config["interface"]+": "+("链路在线" if carrier == "1" else "未接线或状态不可用"), "scope": "网络", "source": "Linux 网卡状态"})
        with self.lock:
            collection = self.collection_snapshot(mode)
            if collection.get("prepared") or collection.get("recording"):
                services["exporter"] = {"state": "running", "detail": collection.get("message", "采集导出器在线"), "observed_at": collection.get("observed_at", now())}
            reasons = [c["label"] for c in checks if c["scope"] == "设备" and c["status"] != "passed"]
            if collection.get("mode_conflict"):
                reasons.append("另一个运行模式已有采集任务")
            if not self.driver.collection_available():
                reasons.append("独立采集环境尚未安装")
            if collection.get("stale"):
                reasons.append("采集导出器状态过期")
            manual_busy = self.manual.active() or self.real_manual.active()
            if manual_busy:reasons.append("手动调试正在占用控制权")
            can_collect = not reasons and not collection.get("busy", False)
            task_busy = collection.get("prepared") or collection.get("busy") or any(j["state"] in {"running","pending"} for j in self.state["jobs"].values())
            gate_ready = mode == "sim" or manual.get("gate",{}).get("ready") is True
            if gate_ready:commands_manual = ["robot.initialize","robot.claim","robot.release","robot.apply_pose"]
            else:commands_manual = []
            commands = ["self_check.run", "deployment.prepare", "deployment.cancel", "robot.connect", "safety.stop"]
            commands += ["services.docker.start", "services.pc_service.start", "services.cameras.start"]
            for service in ("docker","pc_service"):
                commands.append("services."+service+".stop")
                reason=self._service_stop_reason(service,services[service])
                services[service].update(stop_allowed=not reason,stop_reason=reason)
            if config["camera_source"] == "ros2":commands.append("services.cameras.stop")
            commands += self.collection_capabilities(mode) + commands_manual
            groups = self.workspace.groups()
            real = [g for g in groups if not g["demo_only"]]
            latest_jobs = [j for j in self.state["jobs"].values() if j["mode"] == mode]
            deployment = copy.deepcopy(latest_jobs[-1]) if latest_jobs else {"id": "", "state": "idle", "steps": []}
            return {"ok": True, "snapshot": {"revision": self.state["revision"], "observed_at": now(), "mode": mode, "manual": manual,
                "capabilities": {"commands": commands, "camera_transports": ["mjpeg"]}, "robot": robot, "battery": battery,
                "services": services, "cameras": cameras, "camera_source": camera_source, "pico": {**pico, "ready": pico_ready},
                "model": {"connected": False, "state": "disconnected", "steps": 0, "adapter": {"validated": False}},
                "collection": {**collection,"control_scope":"recording_only"},
                "active_task": {"kind":"manual","owner":"manual","mode":"real" if self.real_manual.active() else "sim"} if manual_busy else {"kind":"collection","owner":"pico","mode":mode} if collection.get("prepared") else None,
                "interlocks": {"can_initialize": gate_ready and not task_busy and not manual_busy, "can_claim": gate_ready and not task_busy and not manual_busy and robot["initialized"], "can_apply_pose": gate_ready and manual.get("owner")=="manual" and not task_busy,
                    "can_infer": False, "can_collect": can_collect, "reasons": {"can_collect": "、".join(reasons) or "采集任务正在处理", "can_infer": "任务模型接入按规划留待真机采集后开发", "can_initialize": manual.get("gate",{}).get("message","设备或任务未就绪"), "can_claim": manual.get("reason") or manual.get("gate",{}).get("message","请先初始化并等待反馈"), "can_apply_pose": manual.get("reason") or manual.get("gate",{}).get("message","请先取得手动控制权")}},
                "checks": checks, "events": copy.deepcopy(self.state["events"]), "deployment": deployment,
                "groups": groups, "totals": {"datasets": len(real), "episodes": sum(g["retained"] for g in real),
                    "demo_episodes": sum(g["retained"] for g in groups if g["demo_only"])},
                "workflow": {"run_id":"", "graph_id":"", "state": "idle", "node_states": {}}, "output_root": str(self.adapter.repo_root/"outputs"),
                "message": "工作站后端已连接；设备就绪情况见自检"}}

    def busy(self):
        return bool(self.recorder.active() or self.manual.active() or self.real_manual.active() or any(j["state"] in {"running","pending"} for j in self.state["jobs"].values()))

    def _service_stop_reason(self, service, state, allow_stopped=False):
        if self.busy():return "采集、手动控制或准备任务正在占用服务，请先结束任务"
        if state.get("owned") is False:return "服务不属于本项目，不能从工作台停止"
        if not allow_stopped and state.get("state") in {"offline","stopped"} and not state.get("unity_running"):
            return "服务当前已停止"
        for mode in ("real","sim"):
            if age(self.driver.telemetry(mode).get("controller",{}).get("observed_at"))<=2:
                return "SONIC控制器仍在运行，请先按现场流程停止控制器"
        blockers=self.driver.service_stop_blockers(service) if hasattr(self.driver,"service_stop_blockers") else []
        return "、".join(blockers)

    def configure(self,payload):
        with self.lock:
            result=self.configuration.write(payload,self.busy())
            if result.get("requires_reconnect"):
                (self.directory/"readonly-paused").touch()
                for mode in ("sim","real"):
                    self.driver.supervisor.stop("probe-"+mode)
                self.driver.stop_camera_source()
            return result

    def manual_target(self,payload):
        with self.lock:
            self.validate_mode(payload.get("mode"),payload.get("profile_id",PROFILE_ID))
            if payload.get("action") not in {"heartbeat","apply_pose"}:raise ConsoleError("高频通道仅支持heartbeat/apply_pose；接管须使用普通命令接口")
            if self.recorder.active() or any(j["state"] in {"running","pending"} for j in self.state["jobs"].values()):raise ConsoleError("另一个任务正在运行",409,"task_conflict")
            return self._manual_command(payload["mode"],payload.get("action"),payload)

    def _manual_command(self,mode,action,payload):
        if action not in {"stop","release"}:
            if mode=="real" and self.manual.active() or mode=="sim" and self.real_manual.active():raise ConsoleError("另一运行模式已有手动控制任务",409,"owner_conflict")
            if age(self.driver.telemetry(mode).get("controller",{}).get("observed_at"))<2:raise ConsoleError("SONIC控制器仍在运行",409,"owner_conflict")
        return self.real_manual.command(action,payload) if mode=="real" else self.manual.command(mode,action,payload)

    def pose_preview(self,payload):
        target=payload.get("joints");mode=payload.get("mode","sim");self.validate_mode(mode)
        robot=self.snapshot(mode)["snapshot"]["robot"]
        start=payload.get("start") or robot["joints"]
        if not start:raise ConsoleError("请先初始化仿真或提供完整起始姿态",412,"feedback_stale")
        return {"ok":True,"trajectory":trajectory(self.profile,start,target,payload.get("transition_seconds",3),payload.get("velocity_limit_rad_s",.5))}

    def collection_snapshot(self, mode):
        return self.recorder.snapshot(mode)

    def collection_capabilities(self, mode):
        return ["collection."+action for action in ("prepare","start","save","discard","end")]

    def command(self, scope, body, key):
        if not isinstance(body, dict):
            raise ConsoleError("命令必须为对象")
        mode, profile, action, payload = (body.get(k) for k in ("mode", "profile_id", "action", "payload"))
        self.validate_mode(mode, profile)
        if not isinstance(payload, dict) or not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", key):
            raise ConsoleError("命令参数或 Idempotency-Key 无效")
        if not isinstance(action,str):raise ConsoleError("action 必须为字符串")
        exempt = scope == "safety" or action == "cancel"
        if not exempt and (not isinstance(body.get("expected_revision"), int) or isinstance(body.get("expected_revision"), bool) or body["expected_revision"]<0):
            raise ConsoleError("expected_revision 必须为快照中的整数版本")
        digest = hashlib.sha256(json.dumps([scope, body], sort_keys=True).encode()).hexdigest()
        with self.lock:
            prior = self.state["idempotency"].get(key)
            if prior:
                if prior["digest"] != digest:
                    raise ConsoleError("同一 Idempotency-Key 对应不同命令", 409, "idempotency_conflict")
                return copy.deepcopy(prior["result"])
            if not (scope == "safety" or action == "cancel") and body["expected_revision"] != self.state["revision"]:
                raise ConsoleError("状态已变化，请刷新后重试", 409, "revision_conflict")
            command_id = uuid.uuid4().hex
            result = self._dispatch(scope, action, mode, payload, command_id)
            result = {"ok": True, "command_id": command_id, "state": "succeeded", **(result or {})}
            self.state["idempotency"][key] = {"digest": digest, "result": result}
            while len(self.state["idempotency"]) > 500:
                self.state["idempotency"].pop(next(iter(self.state["idempotency"])))
            self._changed()
            return copy.deepcopy(result)

    def _dispatch(self, scope, action, mode, payload, command_id):
        if scope == "self_check" and action == "run":
            if payload.get("read_only") is not True:
                raise ConsoleError("自检必须 read_only:true")
            self.driver.inspect(force=True)
            self.event("只读自检完成", "设备状态以最新快照为准")
            return {"message": "只读自检完成"}
        if scope == "robot" and action == "connect":
            if self.recorder.active():raise ConsoleError("采集任务进行中，不能更改只读订阅配置",409,"task_conflict")
            self.driver.start_probe(mode)
            atomic_json(self.directory/"readonly-mode.json",{"mode":mode})
            (self.directory/"readonly-paused").unlink(missing_ok=True)
            self.event("只读订阅器已启动", f"{mode}：等待机器人、PICO 和相机数据")
            return {"message": "只读连接已启动，尚不代表收到反馈"}
        if scope == "robot" and action in {"initialize","claim","release","apply_pose"}:
            if self.recorder.active() or any(j["state"] in {"running","pending"} for j in self.state["jobs"].values()):raise ConsoleError("另一个任务正在运行",409,"task_conflict")
            return self._manual_command(mode,action,payload)
        if scope == "deployment":
            return self.deployment(action, mode, payload)
        if scope == "services":
            service = payload.get("service_id")
            if action == "stop" and service in {"docker","pc_service"}:
                state=self.driver.container() if service=="docker" else self.driver.pc_service_status()
                reason=self._service_stop_reason(service,state,allow_stopped=True)
                if reason:raise ConsoleError(reason,409,"service_in_use")
                result=self.driver.stop_service(service)
                self.event("SONIC容器已停止" if service=="docker" else "XRoboToolkit已停止",result["message"])
                return result
            if service == "cameras" and action in {"start", "stop"}:
                if self.recorder.active():raise ConsoleError("采集任务进行中，不能启停相机来源",409,"task_conflict")
                if any(j["state"] in {"running", "pending"} for j in self.state["jobs"].values()):
                    raise ConsoleError("准备任务进行中，请先完成或取消准备",409,"task_conflict")
                if action == "start":
                    self.driver.start_probe(mode)
                    atomic_json(self.directory/"readonly-mode.json",{"mode":mode})
                    (self.directory/"readonly-paused").unlink(missing_ok=True)
                    self.event("相机接入已启动", "只读接收图像，不启动 SONIC 运动控制")
                    return {"message": "相机来源与只读接收器已启动，等待真实图像"}
                if self.driver.config(mode)["camera_source"] != "ros2":
                    raise ConsoleError("外部 ZMQ 发布器不属于本工作台，不能停止",501,"unsupported_service")
                (self.directory/"camera-paused").touch()
                self.driver.stop_camera_source()
                self.event("ROS 2 相机桥接已停止", "仅停止本工作台拥有的相机桥接进程")
                return {"message": "相机桥接已停止"}
            if action == "start" and service in {"docker", "pc_service", "cameras"}:
                return self.deployment("prepare", mode, {"allow_motion": False, "service_id": service})
            raise ConsoleError("该服务操作尚未开放；控制器由现场初始化流程管理", 501, "unsupported_service")
        if scope == "safety" and action == "stop":
            for flag in self.cancel_flags.values():
                flag.set()
            self.manual.stop()
            real_stop=self.real_manual.stop()
            result = self.recorder.command(mode,"stop",{},command_id)
            self.event("已请求停止本工作台任务", "取消准备、结束采集并释放手动仿真；外部运动控制器仍由现场管理", "warning")
            return {**result,"message": "已请求停止准备、采集和手动仿真；外部真机控制器由现场管理", "motion_stop_supported":False}
        if scope == "collection":
            if action in {"prepare","start"}:
                CollectionManager.validate(payload)
                snapshot=self.snapshot(mode)["snapshot"]
                if not snapshot["interlocks"]["can_collect"]:
                    reason=snapshot["interlocks"]["reasons"]["can_collect"]
                    raise ConsoleError("采集条件未就绪："+reason,412,"collection_interlock",[reason])
            if action=="prepare":
                if any(j["state"] in {"pending","running"} for j in self.state["jobs"].values()):
                    raise ConsoleError("请等待准备任务结束",409,"task_conflict")
                result=self.recorder.prepare(mode,payload)
            else:
                result=self.recorder.command(mode,action,payload,command_id)
            self.event("采集操作已提交", action+"；等待导出器确认")
            return result
        if scope in {"inference", "workflows", "robot"}:
            raise ConsoleError("此执行能力按规划留待真机接入后开放", 501, "not_implemented")
        raise ConsoleError("未知操作", 400)

    def deployment(self, action, mode, payload):
        if action == "cancel":
            job_id = payload.get("job_id")
            job = self.state["jobs"].get(job_id)
            if not job or job["mode"] != mode:
                raise ConsoleError("找不到当前模式的准备任务", 404, "not_found")
            if job["state"] in {"running", "pending"}:
                self.cancel_flags[job_id].set()
            elif job["state"] == "waiting":
                job.update(state="cancelled", message="已取消等待设备", updated_at=now())
            return {"job_id": job_id, "message": "已请求取消准备"}
        if action != "prepare" or payload.get("allow_motion") is not False:
            raise ConsoleError("准备任务必须 allow_motion:false")
        if any(j["state"] in {"running", "pending"} for j in self.state["jobs"].values()):
            raise ConsoleError("已有准备任务正在执行", 409, "task_conflict")
        if self.recorder.active() or self.manual.active() or self.real_manual.active():
            raise ConsoleError("请先结束当前采集或手动任务", 409, "task_conflict")
        job_id = uuid.uuid4().hex
        self.state["jobs"][job_id] = {"id": job_id, "mode": mode, "state": "pending", "created_at": now(),
            "updated_at": now(), "allow_motion": False, "service_id": payload.get("service_id"), "message": "等待环境自检",
            "steps": [{"id": key, "label": label, "state": "pending", "detail": ""} for key, label in STAGES]}
        flag = self.cancel_flags[job_id] = threading.Event()
        thread = threading.Thread(target=self._prepare, args=(job_id, mode, flag), daemon=True)
        self.threads.append(thread)
        thread.start()
        self.event("SONIC 准备任务已提交", f"{mode}；不启动运动控制程序")
        return {"job_id": job_id, "state": "accepted", "message": "开始分步准备 SONIC"}

    def _job_update(self, job_id, **values):
        with self.lock:
            self.state["jobs"][job_id].update(**values, updated_at=now())
            self._changed()

    def _step(self, job_id, index, state, detail=""):
        with self.lock:
            self.state["jobs"][job_id]["steps"][index].update(state=state, detail=detail)
            self._changed()

    def _prepare(self, job_id, mode, flag):
        path = self.directory/"jobs"/(job_id+".log")
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._job_update(job_id, state="running", message="正在检查软件运行环境")
            self._step(job_id, 0, "running")
            checks = self.driver.inspect(force=True)["checks"]
            blockers = [c["label"] for c in checks if c["status"] == "blocked"]
            if blockers:
                raise ConsoleError("环境自检未通过："+"、".join(blockers), 412, "environment_blocked")
            if flag.is_set():
                raise ConsoleError("准备已取消", 409, "cancelled")
            self._step(job_id, 0, "succeeded", "主机、GPU、镜像、SDK 与模型检查通过")
            self._step(job_id, 1, "running")
            service = self.state["jobs"][job_id].get("service_id")
            with path.open("ab", buffering=0) as log:
                if service in {None, "docker"}:
                    self.driver.run_recipe("docker_start", flag, log)
                    if not (self.adapter.repo_root/"gear_sonic_deploy/target/release/g1_deploy_onnx_ref").is_file():
                        self.driver.run_recipe("docker_build", flag, log)
                    self.driver.run_recipe("docker_check", flag, log)
                if service in {None, "pc_service"}:
                    self.driver.run_recipe("pc_service_start", flag, log)
            if flag.is_set():
                raise ConsoleError("准备已取消", 409, "cancelled")
            self.driver.start_probe(mode)
            self._step(job_id, 1, "succeeded", "请求的软件服务与只读订阅已准备")
            if service is not None:
                for index in range(2, 5):
                    self._step(job_id, index, "pending", "单项服务准备不判定完整设备就绪")
                self._job_update(job_id, state="succeeded", message=f"{service} 软件服务已准备；设备有效性见自检")
                return
            self._job_update(job_id, message="软件准备完成，等待三相机、PICO 与机器人反馈")
            timeout = max(0, min(60, self.driver.config(mode)["prepare_timeout_seconds"]))
            deadline = time.monotonic()+timeout
            ready = [False, False, False]
            while True:
                if flag.is_set():
                    raise ConsoleError("准备已取消", 409, "cancelled")
                snapshot = self.snapshot(mode)["snapshot"]
                ready = [all(c["state"] == "streaming" for c in snapshot["cameras"]),
                         snapshot["pico"]["ready"], snapshot["robot"]["connected"]]
                for index, ok in enumerate(ready, 2):
                    state = "succeeded" if ok else "running"
                    if self.state["jobs"][job_id]["steps"][index]["state"] != state:
                        self._step(job_id, index, state)
                if all(ready) or time.monotonic() >= deadline:
                    break
                flag.wait(.3)
            for index, ok in enumerate(ready, 2):
                self._step(job_id, index, "succeeded" if ok else "blocked", "已收到新鲜数据" if ok else "等待现场设备连接并发送有效数据")
            self._job_update(job_id, state="ready" if all(ready) else "waiting",
                             message="各项数据源已就绪；初始化与运动需现场验证" if all(ready) else "软件准备完成；等待现场相机、PICO 或 G1，连接后可重新检查")
            with self.lock:
                self.event("SONIC 软件准备完成", "设备就绪情况见启动向导")
                self._save()
        except Exception as exc:
            cancelled = isinstance(exc, ConsoleError) and exc.code == "cancelled"
            with self.lock:
                job = self.state["jobs"][job_id]
                for step in job["steps"]:
                    if step["state"] in {"running", "pending"}:
                        step["state"] = "cancelled" if cancelled else "failed"
                job.update(state="cancelled" if cancelled else "failed", message=str(exc)[:500], updated_at=now())
                self.event("准备任务已取消" if cancelled else "准备任务失败", job["message"], "warning" if cancelled else "error")
                self._changed()

    def job(self, job_id):
        with self.lock:
            job = self.state["jobs"].get(job_id)
            if job is None:
                raise ConsoleError("准备任务不存在", 404, "not_found")
            result = copy.deepcopy(job)
            path = self.directory/"jobs"/(job_id+".log")
            if path.is_file():
                with path.open("rb") as handle:
                    handle.seek(max(0, path.stat().st_size-16000))
                    result["log"] = handle.read(16000).decode("utf-8", errors="replace")
            return {"ok": True, "job": result}

    def close(self):
        self.manual.stop()
        self.real_manual.stop()
        # Passive readers and recording workers are durable. Web restart is not a device stop.
        for flag in self.cancel_flags.values():
            flag.set()
        for thread in self.threads:
            thread.join(timeout=8)
        if not self.instance_lock.closed:
            fcntl.flock(self.instance_lock,fcntl.LOCK_UN)
            self.instance_lock.close()


def read_text(path):
    try:
        return path.read_text().strip()
    except OSError:
        return ""
