"""Explicit manual ownership, velocity-limited targets and expiring browser leases."""
from __future__ import annotations
import hmac
from pathlib import Path
import secrets
import threading
import time
import uuid
from console_support import ConsoleError, age, atomic_json, read_json
from console_poses import joint_targets, trajectory

class ManualControl:
    def __init__(self,driver,directory,profile):
        self.driver,self.directory,self.profile=driver,Path(directory)/'manual-sim',profile
        self.lock=threading.RLock();self.token=None;self.expires=0;self.sequence=-1
        self.directory.mkdir(parents=True,exist_ok=True)
        # Server restart revokes old browser ownership; an independent worker also enforces expiry.
        atomic_json(self.directory/'command.json',{})

    def status(self):
        if not hasattr(self.driver,'supervisor'):return {'state':'stopped','owner':None}
        row=read_json(self.directory/'status.json');record=self.driver.supervisor.record('manual-sim')
        valid=self.driver.supervisor.running('manual-sim') and row.get('pid')==record.get('pid') and age(row.get('heartbeat_at'))<2 and row.get('state')=='running'
        owner='manual' if self.token and time.monotonic()<self.expires and valid else None
        return {**(row if valid else {}),'state':'running' if valid else 'stopped','owner':owner,'lease_seconds':max(0,self.expires-time.monotonic()) if owner else 0}

    def active(self):return self.status().get('owner')=='manual'

    def initialize(self,mode):
        if mode!='sim':raise ConsoleError('真机手动控制需现场完成支撑、控制器互斥与停止策略验证；当前禁止 DDS 运动输出',412,'onsite_validation_required')
        python=self.driver.root/'.venv_teleop/bin/python';model=self.driver.root/'gear_sonic_deploy/g1/g1_29dof.xml'
        profile=self.driver.app_root/'static/assets/g1/profile.json'
        if not python.is_file() or not model.is_file():raise ConsoleError('MuJoCo 环境或 G1 模型尚未安装',412,'simulation_unavailable')
        if self.active():raise ConsoleError('请先释放手动控制权',409,'owner_conflict')
        self.driver.supervisor.start('manual-sim',[str(python),str(self.driver.app_root/'console_manual_worker.py'),'--directory',str(self.directory),'--model',str(model),'--profile',str(profile)],self.driver.root)
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            if self.status()['state']=='running':return {'message':'MuJoCo 固定基座物理仿真已启动；尚未取得控制权'}
            if not self.driver.supervisor.running('manual-sim'):break
            time.sleep(.05)
        raise ConsoleError('MuJoCo 启动失败，请查看 manual-sim 日志',412,'simulation_start_failed')

    def command(self,mode,action,payload):
        with self.lock:
            if mode!='sim':return self.initialize(mode)
            if action=='initialize':return self.initialize(mode)
            status=self.status()
            if action=='claim':
                if payload.get('owner')!='manual':raise ConsoleError('当前只开放独立手动调试控制',412,'owner_unsupported')
                if status['state']!='running':raise ConsoleError('请先初始化 MuJoCo 仿真',412,'simulation_unavailable')
                if status['owner']:raise ConsoleError('另一个浏览器已取得手动控制权',409,'owner_conflict')
                self.token=secrets.token_urlsafe(32);self.expires=time.monotonic()+3;self.sequence=-1
                return {'lease_token':self.token,'message':'已取得手动控制权；心跳中断 3 秒自动释放'}
            if action in {'release','stop'}:
                if action=='release':self._lease(payload)
                self.stop();return {'message':'手动控制已释放；MuJoCo 保持当前位置','motion_stop_supported':False}
            self._lease(payload)
            if status['state']!='running':raise ConsoleError('MuJoCo 反馈中断',412,'feedback_stale')
            if action=='heartbeat':
                self.expires=time.monotonic()+3
                row=read_json(self.directory/'command.json')
                if row.get('id'):row['lease_deadline']=self.expires;atomic_json(self.directory/'command.json',row)
                return {'ok':True,'lease_seconds':3}
            if action!='apply_pose':raise ConsoleError('未知手动控制操作')
            sequence=payload.get('sequence')
            if type(sequence)is not int or sequence<=self.sequence:raise ConsoleError('目标序号必须严格递增',409,'target_sequence')
            if payload.get('unit')!='rad':raise ConsoleError('关节单位必须为 rad')
            target=joint_targets(self.profile,payload.get('joints'))
            result=trajectory(self.profile,status['joints'],target,payload.get('transition_seconds',3),payload.get('velocity_limit_rad_s',.5))
            ident=uuid.uuid4().hex;self.sequence=sequence
            atomic_json(self.directory/'command.json',{'id':ident,'positions':[r['position_rad'] for r in target],'duration':result['duration_seconds'],'lease_deadline':self.expires})
            return {'ok':True,'target_id':ident,'target_state':'sent','duration_seconds':result['duration_seconds'],'message':'已发送目标，是否到位以物理仿真反馈为准'}

    def _lease(self,payload):
        token=payload.get('lease_token')
        if not self.token or not isinstance(token,str) or not hmac.compare_digest(token,self.token) or time.monotonic()>=self.expires:
            raise ConsoleError('控制权租约缺失或已过期，请重新接管',409,'lease_expired')

    def stop(self):
        with self.lock:
            self.token=None;self.expires=0;atomic_json(self.directory/'command.json',{})
