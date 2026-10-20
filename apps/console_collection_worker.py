"""Managed wrapper around the official SONIC exporter; never starts robot control."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import sys
import threading
import time

from console_support import age, atomic_json, now, read_json


class RecordingSession:
    def __init__(self,folder):
        self.folder=Path(folder)
        self.config=read_json(self.folder/"config.json")
        self.stop=threading.Event()
        self.lock=threading.RLock()
        self.state={"state":"preparing","message":"等待数据源","recording":False,"prepared":False,"frames":0}
        self.collector=None
        self.started=None
        self.progress={}
        self.previous={}
        self.exporter=None

    def update(self,**kwargs):
        with self.lock:self.state.update(kwargs)

    def heartbeat(self):
        while not self.stop.wait(.2):self.write_status()

    def write_status(self):
        with self.lock:
            row={**self.state,"observed_at":now(),"elapsed_seconds":time.monotonic()-self.started if self.started else 0}
            if self.exporter is not None:
                row["frames"]=self.exporter.episode_buffer.get("size",0)
                row["episodes_saved"]=self.exporter.meta.total_episodes
            atomic_json(self.folder/"status.json",row)

    def initialize(self):
        root=Path(self.config["sonic_root"])
        sys.path.insert(0,str(root))
        from gear_sonic.scripts.run_data_exporter import GrootDataCollector, get_g1_robot_model, get_features_sonic_vla, get_modality_config_sonic_vla, get_wrist_camera_features, get_wrist_camera_modality_config, poll_robot_config_zmq
        from gear_sonic.data.exporter import Gr00tDataExporter
        import gear_sonic.data.exporter as exporter_module
        from console_video_writer import ManagedVideoWriter
        # The upstream writer flushes while its encoder thread may still be active.
        # Keep the official dataset writer, with per-video serialized finalization.
        exporter_module.VideoWriter=ManagedVideoWriter

        class NonDeletingExporter(Gr00tDataExporter):
            def _get_image_file_path(self,episode_index,image_key,frame_index):
                # The official writer only uses this as a placeholder for videos.
                # Use the actual MP4 path, so no temporary image tree is created.
                return Path(self.root)/self.meta.get_video_file_path(episode_index,image_key)

            def save_episode(self,episode_data=None):
                # This installation uses video writers. Never enter the upstream image-tree cleanup branch.
                if (Path(self.root)/"images").exists():
                    raise RuntimeError("检测到 image 临时目录；保留全部文件，请检查数据布局")
                return super().save_episode(episode_data)

        class ManagedCollector(GrootDataCollector):
            def _check_recording_commands(self):
                # Explicit durable commands replace keyboard/PICO toggle flags.
                self._manager_toggle_dc=False
                self._manager_toggle_da=False

        output=Path(self.config["output"])
        if output.exists():raise RuntimeError("输出目录已存在，拒绝覆盖或恢复其他会话")
        robot=get_g1_robot_model()
        features=get_features_sonic_vla(robot)
        features.update(get_wrist_camera_features())
        modalities=get_modality_config_sonic_vla(robot)
        for key,value in get_wrist_camera_modality_config().items():modalities.setdefault(key,{}).update(value)
        endpoint=lambda key:self.config[key].rsplit(":",1)
        state_host,state_port=endpoint("state_endpoint")
        robot_config=poll_robot_config_zmq(state_host.removeprefix("tcp://"),int(state_port),20)
        self.exporter=NonDeletingExporter.create(save_root=str(output),fps=self.config["fps"],features=features,
            modality_config=modalities,task=self.config["task"],robot_type="unitree_g1",
            script_config={**robot_config,"record_wrist_cameras":True,"robot_station_mode":self.config["mode"]},overwrite_existing=False)
        (output/".incomplete").write_text("采集任务尚未正常结束；请以片段文件和任务状态核实数据完整性。\n")
        camera_host,camera_port=endpoint("camera_endpoint")
        pose_host,pose_port=endpoint("pose_endpoint")
        self.collector=ManagedCollector(camera_host=camera_host.removeprefix("tcp://"),camera_port=int(camera_port),
            data_exporter=self.exporter,robot_model=robot,frequency=self.config["fps"],text_to_speech=None,
            sonic_data_zmq_host=pose_host.removeprefix("tcp://"),sonic_data_zmq_port=int(pose_port),
            state_zmq_host=state_host.removeprefix("tcp://"),state_zmq_port=int(state_port))
        self.collector._keyboard_listener.close()

    def poll(self):
        c=self.collector
        c._poll_state_zmq()
        c._poll_sonic_zmq_messages()
        image=c._image_subscriber.read()
        if image is not None:
            # Map deployment-specific camera keys into the official exporter names.
            mapping=self.config["camera_keys"]
            c.latest_image_msg={"images":{("ego_view" if name=="head" else name):image.get("images",{}).get(key)
                for name,key in mapping.items() if key in image.get("images",{})},
                "timestamps":{("ego_view" if name=="head" else name):image.get("timestamps",{}).get(key) for name,key in mapping.items()}}
        state=c.latest_proprio_msg
        if state:
            token=state.get("control_index",state.get("ros_timestamp"))
            if token is not None and self.previous.get("state") is not None and token<self.previous["state"]:
                raise RuntimeError("SONIC 控制序号回退，请重新准备采集")
            if token is not None and token!=self.previous.get("state"):
                self.previous["state"]=token;self.progress["state"]=time.monotonic()
        pose=c.latest_sonic_msg
        if pose is not None:
            stamp=pose.get("frame_index")
            token=int(stamp.flat[0]) if stamp is not None else None
            if token is not None and token!=self.previous.get("pose"):
                self.previous["pose"]=token;self.progress["pose"]=time.monotonic()

    def source_errors(self):
        errors=[]
        deadline=self.config.get("source_max_age_seconds",.5)
        for name in ("state","pose"):
            if time.monotonic()-self.progress.get(name,0)>deadline:errors.append(name+" 数据未更新")
        c=self.collector
        if not c.latest_image_msg:errors.append("相机尚无数据")
        else:
            for key in ("ego_view","left_wrist","right_wrist"):
                stamp=c.latest_image_msg.get("timestamps",{}).get(key)
                if not isinstance(stamp,(int,float)) or not -.5<=time.time()-stamp<=deadline:
                    errors.append(key+" 相机过期或时钟未同步")
                if c.latest_image_msg.get("images",{}).get(key) is None:errors.append(key+" 缺少图像")
                else:
                    frame=c.latest_image_msg["images"][key]
                    feature="observation.images."+key
                    expected=tuple(self.exporter.features[feature]["shape"])
                    if getattr(frame,"shape",None)!=expected:errors.append(key+" 相机分辨率不符合采集配置")
        probe=read_json(self.config["probe_status_path"])
        pico=probe.get("pico",{})
        if age(probe.get("heartbeat_at"))>3 or age(pico.get("observed_at"))>2 or pico.get("body_ready") is not True:
            errors.append("PICO 追踪反馈缺失或过期")
        return errors

    def finish_episode(self,discard):
        size=self.exporter.episode_buffer.get("size",0)
        if size:
            self.update(state="saving",recording=False,message="正在写入三路视频与 Parquet")
            if discard:self.exporter.save_episode_as_discarded()
            else:self.exporter.save_episode()
        elif not discard:raise RuntimeError("当前片段没有有效帧，未生成空片段")
        self.collector._episode_state.reset_state()
        self.started=None
        self.collector._initial_yaw=None
        self.update(state="ready",recording=False,prepared=True,message="已舍弃当前片段并保留原始数据标记" if discard else "片段已保存")

    def process_commands(self):
        for path in sorted((self.folder/"commands").glob("*.request.json")):
            request=read_json(path)
            result_path=path.parent/(request["id"]+".result.json")
            if result_path.exists():continue
            action=request["action"]
            try:
                phase=self.state["state"]
                if action=="start":
                    if phase!="ready":raise RuntimeError("导出器尚未就绪或已在录制")
                    errors=self.source_errors()
                    if errors:raise RuntimeError("；".join(errors))
                    self.collector._episode_state.change_state()
                    self.started=time.monotonic()
                    self.update(state="recording",recording=True,prepared=True,message="正在录制")
                elif action in {"save","discard"}:
                    if phase!="recording":raise RuntimeError("当前没有录制片段")
                    self.finish_episode(action=="discard")
                elif action in {"end","stop"}:
                    if action=="end" and phase=="recording":raise RuntimeError("请先保存或舍弃当前片段")
                    if phase=="recording":self.finish_episode(True)
                    self.update(state="ended",recording=False,prepared=False,message="采集任务已结束")
                    self.stop.set()
                else:raise RuntimeError("未知采集操作")
                atomic_json(result_path,{"id":request["id"],"action":action,"ok":True,"at":now(),"state":self.state["state"]})
            except Exception as exc:
                atomic_json(result_path,{"id":request["id"],"action":action,"ok":False,"at":now(),"message":str(exc)[:500]})
                self.update(message=str(exc)[:500])
                if self.state["state"]=="saving":
                    self.update(state="failed",recording=False,prepared=False)
                    self.stop.set()
            self.write_status()
            if self.stop.is_set():break

    def run(self):
        thread=threading.Thread(target=self.heartbeat,daemon=True);thread.start()
        try:
            self.initialize()
            deadline=time.monotonic()+20
            while not self.stop.is_set():
                started=time.monotonic()
                self.poll()
                errors=self.source_errors()
                if self.state["state"]=="preparing":
                    if not errors:self.update(state="ready",prepared=True,message="官方导出器与三路数据源已就绪")
                    elif time.monotonic()>deadline:raise RuntimeError("准备超时："+"；".join(errors))
                self.process_commands()
                if self.state["state"]=="recording":
                    if errors:
                        self.finish_episode(True)
                        raise RuntimeError("数据源中断，当前片段已标记舍弃："+"；".join(errors))
                    self.collector._add_data_frame()
                self.stop.wait(max(0,1/self.config["fps"]-(time.monotonic()-started)))
            if self.state["state"]=="recording":self.finish_episode(True)
            if self.state["state"]!="failed":
                self.update(state="ended",prepared=False,recording=False,message="采集任务已结束")
                marker=Path(self.config["output"])/".incomplete"
                if marker.is_file():marker.unlink()
        except Exception as exc:
            detail=str(exc)
            if self.exporter is not None and self.exporter.episode_buffer.get("size",0)>0 and self.state["state"]!="saving":
                try:
                    self.finish_episode(True)
                    detail += "；当前有效帧已保存并标记舍弃"
                except Exception as finalization_error:
                    print(f"Partial episode finalization failed: {finalization_error}",flush=True)
                    detail += "；未完成文件已保留，需检查完整性"
            self.update(state="failed",prepared=False,recording=False,message=detail[:700])
            print(f"Collection failed: {exc}",flush=True)
        finally:
            if self.exporter is not None:
                try:self.exporter.stop_video_writers()
                except Exception as exc:print(f"Video finalization: {exc}",flush=True)
            self.stop.set();thread.join(timeout=1);self.write_status()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--session",type=Path,required=True)
    args=parser.parse_args()
    session=RecordingSession(args.session)
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:session.stop.set())
    session.run()
