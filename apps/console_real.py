"""Real G1 controller manager; no DDS writer exists at import or application boot."""
from __future__ import annotations
import hmac
import os
from pathlib import Path
import secrets
import threading
import time
import uuid
from console_support import ConsoleError,age,atomic_json,read_json
from console_poses import joint_targets
from unitree_g1_control import MOTOR_NAMES,REFERENCE_KP,REFERENCE_KD,control_fingerprint,load_commissioning,template

class RealManualControl:
    def __init__(self,driver,directory,profile):
        self.driver,self.profile=driver,profile;self.directory=Path(directory)/'real-control';self.directory.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.token=None;self.expires=0;self.sequence=-1;self.session=None
        atomic_json(self.directory/'control.json',{})
    def eligibility(self):
        try:
            config=load_commissioning(self.directory/'commissioning.json',self.profile,self.driver.config('real'),getattr(self.driver,'root',self.directory))
            return {'ready':True,'code':'commissioning_valid','message':'本机本次开机的现场标定授权有效；仍需初始化和显式接管','expires_at_unix':config['expires_at_unix'],'hardware_variant':config['hardware_variant']}
        except (ConsoleError,OSError,ValueError,AttributeError) as exc:return {'ready':False,'code':getattr(exc,'code','onsite_validation_required'),'message':str(exc) or '真机标定尚未完成'}
    def report(self):
        document=read_json(self.directory/'commissioning.json');reference=template(self.profile)
        configured={r.get('name'):r for r in document.get('joints',[]) if isinstance(r,dict)}
        return {'ok':True,'gate':self.eligibility(),'protocol':{'sdk_reference_commit':'4141c34280abb67c82e115342a8720f4a83d750d','command_topic':'rt/lowcmd','state_topic':'rt/lowstate','message_type':'unitree_hg.msg.dds_.LowCmd_','mode_pr':0,'period_seconds':.002,'hardware_motor_slots':35,'controlled_joints':29},
            'hardware_variant':document.get('hardware_variant','UNCONFIRMED'),'hardware_variant_source':document.get('hardware_variant_source'),
            'checks':{key:document.get(key)is True for key in ('physical_support_confirmed','hardware_mapping_verified','gains_validated','stop_tested')},
            'joints':[{'name':name,'motor_index':i,'reference_kp':REFERENCE_KP[i],'reference_kd':REFERENCE_KD[i],**{k:configured.get(name,{}).get(k) for k in ('kp','kd','lower','upper','max_velocity_rad_s','max_acceleration_rad_s2','max_step_rad','torque_limit_nm')}} for i,name in enumerate(MOTOR_NAMES)],
            'notice':'协议适配已实现；SDK示例增益为参考值，实机增益、机械支撑和停止效果尚需现场核验。网页不能批准标定。'}

    def status(self):
        gate=self.eligibility();row=read_json(self.directory/'status.json')
        alive=hasattr(self.driver,'supervisor') and self.driver.supervisor.running('manual-real')
        record=self.driver.supervisor.record('manual-real') if alive else {}
        valid=alive and row.get('pid')==record.get('pid') and age(row.get('heartbeat_at'))<.3 and row.get('worker_fingerprint')==control_fingerprint()
        state=row.get('state','starting') if valid else 'starting' if alive else 'gated' if not gate['ready'] else 'stopped'
        owner='manual' if valid and state=='active' and self.token and time.monotonic()<self.expires else None
        return {**(row if valid else {}),'state':state,'owner':owner,'gate':gate,'initialized':valid and state=='ready' and not row.get('reason'),'lease_seconds':max(0,self.expires-time.monotonic()) if owner else 0,'control_scope':'supported_joint_test_only','motion_stop_supported':False}
    def active(self):return self.status().get('state') in {'active','stopping'}
    def initialize(self):
        config=load_commissioning(self.directory/'commissioning.json',self.profile,self.driver.config('real'),getattr(self.driver,'root',self.directory))
        if self.active():raise ConsoleError('请先释放真机手动控制权',409,'owner_conflict')
        if self.driver.supervisor.running('manual-real'):self.stop()
        atomic_json(self.directory/'control.json',{});atomic_json(self.directory/'connection.json',self.driver.config('real'))
        python=self.driver.root/'.venv_teleop/bin/python';profile=self.driver.app_root/'static/assets/g1/profile.json'
        self.driver.supervisor.start('manual-real',[str(python),'-u',str(self.driver.app_root/'console_real_worker.py'),'--directory',str(self.directory),'--sonic-root',str(self.driver.root),'--profile',str(profile)],self.driver.root)
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            status=self.status()
            if status.get('initialized'):return {'message':'真机只读预检通过；尚未创建LowCmd发布器，请在支撑状态下显式接管'}
            if not self.driver.supervisor.running('manual-real'):break
            time.sleep(.03)
        detail=read_json(self.directory/'status.json').get('reason','等待有效LowState、唯一数据源与空闲Unitree控制服务')
        self.stop();raise ConsoleError('真机初始化未就绪：'+detail,412,'real_not_ready')
    def _lease(self,payload):
        token=payload.get('lease_token')
        if not self.token or not isinstance(token,str) or not hmac.compare_digest(token,self.token) or time.monotonic()>=self.expires:raise ConsoleError('真机租约缺失或已过期，请重新初始化和接管',409,'lease_expired')
    def _send(self,row):
        atomic_json(self.directory/'control.json',row);deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            ack=read_json(self.directory/'ack.json')
            if ack.get('id')==row['id']:
                if not ack.get('ok'):raise ConsoleError(ack.get('message','真机命令被拒绝'),412,'real_command_rejected')
                return ack
            if not self.driver.supervisor.running('manual-real'):break
            time.sleep(.01)
        self.stop();raise ConsoleError('真机控制进程未确认命令，已请求停止',504,'real_command_timeout')
    def command(self,action,payload):
        with self.lock:
            if action in {'stop','release'}:
                if action=='release':self._lease(payload)
                return self.stop()
            load_commissioning(self.directory/'commissioning.json',self.profile,self.driver.config('real'),getattr(self.driver,'root',self.directory))
            if action=='initialize':return self.initialize()
            status=self.status()
            if action=='claim':
                if payload.get('owner')!='manual' or payload.get('supported_operation_confirmed')is not True:raise ConsoleError('须明确确认受支撑的真机关节调试，不能用于自由站立控制',412,'support_confirmation_required')
                if not status.get('initialized') or self.token:raise ConsoleError('真机未初始化、已有控制权或预检条件变化',409,'owner_conflict')
                self.token=secrets.token_urlsafe(32);self.session=uuid.uuid4().hex;self.expires=time.monotonic()+3;self.sequence=-1
                try:
                    self._send({'id':uuid.uuid4().hex,'armed':True,'session':self.session,'sequence':-1,'lease_deadline':self.expires,'updated_monotonic':time.monotonic()})
                    deadline=time.monotonic()+.4
                    while self.status()['state']!='active' and time.monotonic()<deadline:time.sleep(.01)
                    if self.status()['state']!='active':raise ConsoleError('真机接管未进入有效状态',412,'real_not_active')
                except Exception:self.stop();raise
                return {'message':'真机手动接管成功，从当前反馈姿态开始；3秒心跳到期进入停止流程','lease_token':self.token}
            self._lease(payload)
            if status['state']!='active':self.stop();raise ConsoleError('真机控制已退出，请查看原因后重新初始化',412,'real_not_active')
            row=read_json(self.directory/'control.json')
            if action=='heartbeat':
                self.expires=time.monotonic()+3;row.update(lease_deadline=self.expires,updated_monotonic=time.monotonic());atomic_json(self.directory/'control.json',row)
                return {'ok':True,'lease_seconds':3}
            if action!='apply_pose':raise ConsoleError('未知真机控制操作')
            sequence=payload.get('sequence')
            if type(sequence)is not int or sequence<=self.sequence:raise ConsoleError('目标序号必须严格递增',409,'target_sequence')
            if payload.get('unit')!='rad':raise ConsoleError('真机目标单位必须为rad')
            targets={r['name']:r['position_rad'] for r in joint_targets(self.profile,payload.get('joints'))}
            row.update(id=uuid.uuid4().hex,positions=[targets[n] for n in MOTOR_NAMES],sequence=sequence,duration=payload.get('transition_seconds',3),velocity_limit=payload.get('velocity_limit_rad_s',.2),updated_monotonic=time.monotonic())
            ack=self._send(row);self.sequence=sequence
            return {'ok':True,'target_id':row['id'],'target_state':'sent','duration_seconds':ack.get('duration_seconds'),'message':'真机目标已发送，实际到位以新鲜反馈为准'}
    def stop(self):
        with self.lock:
            self.token=None;self.expires=0;self.session=None;atomic_json(self.directory/'control.json',{})
            if hasattr(self.driver,'supervisor'):self.driver.supervisor.stop('manual-real',timeout=5)
            row=read_json(self.directory/'status.json')
            return {'ok':True,'message':'已停止本工作台真机适配器输出；不代表硬件急停或外部控制器已停止','stop_acknowledged':bool(row.get('stop_acknowledged')),'motion_stop_supported':False,'control_scope':'manual_adapter'}
