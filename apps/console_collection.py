"""Durable, exclusive recording sessions with explicit acknowledged commands."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import threading
import time
import uuid

from console_support import ConsoleError, age, atomic_json, now, read_json


class CollectionManager:
    def __init__(self, adapter, driver, directory):
        self.adapter,self.driver,self.directory=adapter,driver,Path(directory)/"collection"
        self.directory.mkdir(parents=True,exist_ok=True)
        self.pointer=self.directory/"active.json"
        self.lock=threading.RLock()

    @staticmethod
    def validate(payload):
        if not isinstance(payload.get("dataset"),str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",payload["dataset"]):
            raise ConsoleError("数据集名称限 1～80 位字母、数字、下划线和短横线")
        if not isinstance(payload.get("task"),str) or not payload["task"].strip() or len(payload["task"])>240:
            raise ConsoleError("任务描述应为 1～240 个字符")
        if type(payload.get("fps")) is not int or not 1<=payload["fps"]<=120:
            raise ConsoleError("采集频率必须为 1～120 的整数")
        cameras=payload.get("camera_ids")
        if not isinstance(cameras,list) or len(cameras)!=3 or not all(isinstance(v,str) for v in cameras) or set(cameras)!={"head","left_wrist","right_wrist"}:
            raise ConsoleError("第一版采集需要头部、左腕、右腕三路相机")
        return {"dataset":payload["dataset"],"task":payload["task"].strip(),"fps":payload["fps"],"camera_ids":sorted(cameras)}

    def raw(self):
        record=read_json(self.pointer)
        if not record.get("session_id"):return {},{}
        path=self.directory/record["session_id"]
        state=read_json(path/"status.json",{"state":"preparing","message":"正在启动数据导出器"})
        alive=self.driver.supervisor.running("record-"+record["session_id"])
        if state.get("state") not in {"ended","failed"} and not alive:
            state.update(state="failed",message="采集进程已退出；已有数据保留，请检查采集日志",observed_at=now())
        pending=record.get("pending_command")
        if pending:
            result=read_json(path/"commands"/(pending["id"]+".result.json"))
            if not result and not alive and state.get('state') in {'ended','failed'}:
                result={'id':pending['id'],'action':pending['action'],'ok':False,'at':now(),
                        'message':'采集进程已退出，该操作未获得确认；请检查已保留的数据'}
            if result:
                record["last_command"]=result
                record.pop("pending_command",None)
                atomic_json(self.pointer,record)
        return record,state

    def snapshot(self,mode):
        with self.lock:
            record,state=self.raw()
            active=state.get("state") not in {None,"ended","failed"}
            if active and record.get("mode")!=mode:
                return {"prepared":False,"recording":False,"elapsed_seconds":0,"mode_conflict":True,
                        "message":"另一个运行模式有采集任务，请先结束该任务"}
            if not record or record.get("mode")!=mode:
                return {"prepared":False,"recording":False,"elapsed_seconds":0}
            heartbeat=age(state.get("observed_at"))<=5
            return {**state,"session_id":record["session_id"],"dataset":record["payload"]["dataset"],
                    "prepared":active and state.get("state") in {"ready","recording","saving"} and heartbeat,
                    "recording":state.get("state")=="recording" and active and heartbeat,
                    "elapsed_seconds":state.get("elapsed_seconds",0),
                    "busy":bool(record.get("pending_command")) or state.get("state") in {"preparing","saving"},
                    "pending_command":record.get("pending_command"),"last_command":record.get("last_command"),
                    "mode":record.get("mode"),"stale":active and not heartbeat}

    def active(self):
        with self.lock:
            record,state=self.raw()
            return bool(record and state.get("state") not in {"ended","failed"})

    def prepare(self,mode,payload):
        payload=self.validate(payload)
        with self.lock:
            if self.active():raise ConsoleError("已有采集任务，请先结束后再准备",409,"task_conflict")
            if self.adapter.session_running():raise ConsoleError("检测到旧采集会话，请先结束旧会话",409,"legacy_session_conflict")
            if getattr(self.driver,"external_recorders",lambda:[])():
                raise ConsoleError("检测到外部 SONIC 导出器，请先结束后再由工作台准备",409,"external_recorder_conflict")
            output=self.adapter.repo_root/"outputs"/payload["dataset"]
            if output.exists() or output.is_symlink():raise ConsoleError("数据集目录已存在，请使用新的名称；不会覆盖原数据",409,"output_exists")
            python=self.driver.app_root/".venv_collection/bin/python"
            if not python.is_file():raise ConsoleError("独立采集环境未安装",503,"collector_unavailable")
            session=uuid.uuid4().hex
            folder=self.directory/session
            folder.mkdir()
            settings=self.driver.config(mode)
            config={**settings,**payload,"mode":mode,"sonic_root":str(self.adapter.repo_root),"output":str(output),
                    "probe_status_path":str(self.driver.directory/"telemetry"/mode/"status.json")}
            atomic_json(folder/"config.json",config)
            atomic_json(folder/"status.json",{"state":"preparing","observed_at":now(),"message":"正在启动官方 SONIC 数据导出器"})
            atomic_json(self.pointer,{"session_id":session,"mode":mode,"payload":payload,"sequence":0})
            try:
                self.driver.supervisor.start("record-"+session,[str(python),"-u",str(self.driver.app_root/"console_collection_worker.py"),
                    "--session",str(folder)],self.adapter.repo_root)
            except Exception:
                atomic_json(folder/"status.json",{"state":"failed","observed_at":now(),"message":"无法启动导出进程"})
                raise
            return {"state":"accepted","session_id":session,"message":"正在准备采集；等导出器确认就绪后开始录制"}

    def command(self,mode,action,payload,command_id):
        with self.lock:
            record,state=self.raw()
            if not record or (record.get("mode")!=mode and action!="stop") or state.get("state") in {"ended","failed"}:
                if action=="stop":return {"message":"当前没有运行中的采集任务"}
                raise ConsoleError("请先准备当前模式的采集任务",412,"collection_not_prepared")
            if record.get("pending_command") and action!="stop":
                raise ConsoleError("上一条采集操作仍在处理",409,"command_pending")
            phase=state.get("state")
            if action=="start":
                if self.validate(payload)!=record["payload"]:raise ConsoleError("采集配置已修改，请结束任务后重新准备",409,"config_changed")
                if phase!="ready":raise ConsoleError("导出器尚未就绪或已在录制",412,"collection_not_ready")
            elif action in {"save","discard"}:
                if phase!="recording":raise ConsoleError("当前没有待保存的录制",409,"not_recording")
            elif action=="end":
                if phase in {"recording","saving"}:raise ConsoleError("请先保存或舍弃当前片段",409,"recording_active")
            elif action!="stop":raise ConsoleError("未知采集操作")
            sequence=record.get("sequence",0)+1
            request={"id":command_id,"action":action,"created_at":now(),"sequence":sequence}
            folder=self.directory/record["session_id"]
            atomic_json(folder/"commands"/f"{sequence:08d}-{command_id}.request.json",request)
            record.update(sequence=sequence,pending_command={"id":command_id,"action":action})
            atomic_json(self.pointer,record)
            return {"state":"accepted","session_id":record["session_id"],"message":"已提交采集操作，等待导出器确认"}

    def logs(self):
        record,state=self.raw()
        if not record:return ""
        return self.driver.supervisor.logs("record-"+record["session_id"])
