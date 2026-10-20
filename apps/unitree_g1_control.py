"""G1 HG/PR command rules and commissioning gates, independent of DDS IO.

Reference: unitree_sdk2_python 4141c342, example/g1/low_level.
No constructor in this module initializes DDS or sends a command.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import time
import uuid
from console_support import ConsoleError, finite
from console_poses import joint_targets

MOTOR_NAMES=[f'{side}_{part}_joint' for side in ('left','right') for part in ('hip_pitch','hip_roll','hip_yaw','knee','ankle_pitch','ankle_roll')]
MOTOR_NAMES+=['waist_yaw_joint','waist_roll_joint','waist_pitch_joint']
MOTOR_NAMES+=[f'{side}_{part}_joint' for side in ('left','right') for part in ('shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw')]
REFERENCE_KP=[60,60,60,100,40,40]*2+[60,40,40]+[40]*14
REFERENCE_KD=[1,1,1,2,1,1]*2+[1]*17
SDK_FILES=['example/g1/low_level/g1_low_level_example.py','unitree_sdk2py/core/channel.py','unitree_sdk2py/utils/crc.py','unitree_sdk2py/idl/unitree_hg/msg/dds_/_LowCmd_.py','unitree_sdk2py/idl/unitree_hg/msg/dds_/_LowState_.py']

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()
def sdk_fingerprint(root):
    root=Path(root)/'external_dependencies/unitree_sdk2_python'
    return digest({p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in SDK_FILES})
def control_fingerprint():
    folder=Path(__file__).parent
    return digest({name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('unitree_g1_control.py','unitree_g1_transport.py','console_real_worker.py','console_real.py','console_runtime.py','unitree_commission.py','console_support.py','console_poses.py')})
def machine_fingerprint():return hashlib.sha256(Path('/etc/machine-id').read_bytes()).hexdigest()
def boot_id():return Path('/proc/sys/kernel/random/boot_id').read_text().strip()

def template(profile):
    specs={r['name']:r for r in profile['joints']}
    return {'schema_version':1,'approved':False,'hardware_variant':'UNCONFIRMED','profile_id':profile['id'],'model_hash':digest(profile),
        'interface':'eno1','dds_domain':0,'mode_machine':None,'mode_pr':0,'control_period_seconds':.002,
        'feedback_timeout_seconds':.1,'tracking_error_rad':.2,
        'max_motor_temperature_c':60,'max_imu_tilt_rad':.35,'stop_policy':'supported_damping_then_disable','damping_seconds':1.,
        'physical_support_confirmed':False,'hardware_mapping_verified':False,'gains_validated':False,'stop_tested':False,
        'notes':'SDK示例增益仅作参考；下列运动/力矩边界必须现场核定，模板不能启用运动。',
        'joints':[{'name':name,'motor_index':i,'lower':specs[name]['lower'],'upper':specs[name]['upper'],
                   'kp':REFERENCE_KP[i],'kd':REFERENCE_KD[i],'max_velocity_rad_s':.2,'max_acceleration_rad_s2':.5,
                   'max_step_rad':.35,'torque_limit_nm':None} for i,name in enumerate(MOTOR_NAMES)]}

def validate_parameters(document,profile):
    if not isinstance(document,dict) or type(document.get('schema_version'))is not int or document.get('schema_version')!=1:raise ConsoleError('真机标定文件格式无效',412,'commissioning_invalid')
    if document.get('profile_id')!=profile['id'] or document.get('model_hash')!=digest(profile):raise ConsoleError('真机标定模型版本不匹配',412,'commissioning_model')
    if document.get('hardware_variant')!='g1-29-unlocked-waist':raise ConsoleError('须现场确认完整29自由度且腰部未锁定',412,'hardware_unconfirmed')
    if type(document.get('mode_pr'))is not int or document.get('mode_pr')!=0 or type(document.get('mode_machine'))is not int or not 0<=document['mode_machine']<=255:raise ConsoleError('仅支持已核对 mode_machine 的 HG PR 模式',412,'commissioning_mode')
    if document.get('stop_policy')!='supported_damping_then_disable':raise ConsoleError('停止策略须在支撑状态下验证',412,'stop_unvalidated')
    checks=[('control_period_seconds',.002,.002),('feedback_timeout_seconds',.02,.2),('tracking_error_rad',.02,.5),('max_motor_temperature_c',30,75),('max_imu_tilt_rad',.05,.5),('damping_seconds',.25,2)]
    for key,lo,hi in checks:
        if not finite(document.get(key)) or not lo<=document[key]<=hi:raise ConsoleError('真机参数超出允许范围：'+key,412,'commissioning_limits')
    rows=document.get('joints');specs={r['name']:r for r in profile['joints']}
    if not isinstance(rows,list) or len(rows)!=29:raise ConsoleError('需要29个具名电机参数',412,'commissioning_joints')
    values={}
    for row in rows:
        if not isinstance(row,dict):raise ConsoleError('电机参数必须为对象',412,'commissioning_joints')
        name=row.get('name')
        if name not in MOTOR_NAMES or name in values:raise ConsoleError('电机名称重复或不支持',412,'commissioning_joints')
        index=MOTOR_NAMES.index(name);spec=specs[name]
        if type(row.get('motor_index'))is not int or row['motor_index']!=index:raise ConsoleError('电机索引与官方G1顺序不一致',412,'commissioning_mapping')
        if not all(finite(row.get(k)) for k in ('lower','upper')) or not spec['lower']<=row['lower']<row['upper']<=spec['upper']:raise ConsoleError('真机限位必须位于模型范围内',412,'commissioning_limits')
        for key,lo,hi in [('kp',.01,REFERENCE_KP[index]),('kd',.01,REFERENCE_KD[index]),('max_velocity_rad_s',.01,.5),('max_acceleration_rad_s2',.05,2),('max_step_rad',.01,.5),('torque_limit_nm',.1,50)]:
            if not finite(row.get(key)) or not lo<=row[key]<=hi:raise ConsoleError('须核定电机参数：'+name+'/'+key,412,'commissioning_limits')
        values[name]=dict(row)
    return [values[n] for n in MOTOR_NAMES]


def load_commissioning(path,profile,connection,root):
    path=Path(path)
    try:
        info=path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:raise ConsoleError('标定文件必须为本用户拥有的普通文件且权限0600',412,'commissioning_permissions')
        raw=path.read_bytes();doc=json.loads(raw)
    except (OSError,ValueError) as exc:raise ConsoleError('尚未完成现场标定，真机输出保持关闭',412,'onsite_validation_required') from exc
    if doc.get('approved')is not True:raise ConsoleError('标定文件尚未获现场确认，真机输出保持关闭',412,'onsite_validation_required')
    rows=validate_parameters(doc,profile)
    for flag in ('physical_support_confirmed','hardware_mapping_verified','gains_validated','stop_tested'):
        if doc.get(flag)is not True:raise ConsoleError('未完成现场确认：'+flag,412,'onsite_validation_required')
    try:uuid.UUID(doc.get('lowstate_source_guid',''))
    except (ValueError,TypeError,AttributeError):raise ConsoleError('标定记录缺少唯一LowState来源，须现场重新观测',412,'commissioning_source')
    if doc['interface']!=connection['interface'] or doc['dds_domain']!=connection['dds_domain']:raise ConsoleError('连接配置与标定文件不一致',412,'commissioning_connection')
    if doc.get('machine_fingerprint')!=machine_fingerprint() or doc.get('boot_id')!=boot_id():raise ConsoleError('标定授权不属于本机本次开机',412,'commissioning_host')
    if not finite(doc.get('approved_at_unix')) or not finite(doc.get('expires_at_unix')) or not doc['approved_at_unix']<=time.time()<doc['expires_at_unix']<=doc['approved_at_unix']+4*3600:raise ConsoleError('现场授权已过期（最长4小时），请重新确认',412,'commissioning_expired')
    if doc.get('sdk_fingerprint')!=sdk_fingerprint(root) or doc.get('control_fingerprint')!=control_fingerprint():raise ConsoleError('SDK或控制代码已变化，须重新核验',412,'commissioning_version')
    return {**doc,'joints':rows,'file_fingerprint':hashlib.sha256(raw).hexdigest(),'_sdk_root':str(Path(root)/'external_dependencies/unitree_sdk2_python')}


class QuinticPlan:
    """C2 replanning with exact polynomial extrema checks for q/dq/ddq."""
    def __init__(self,positions,velocities,accelerations,target,rows,duration):
        import numpy as np
        self.np=np;self.rows=rows;delta=np.asarray(target)-positions
        # Rest-to-rest analytic bounds avoid repeated eigensolves on first targets.
        if max(abs(v) for v in velocities)<1e-10 and max(abs(a) for a in accelerations)<1e-10:
            duration=max(float(duration),max(1.875*abs(d)/row['max_velocity_rad_s'] for d,row in zip(delta,rows))*1.001,max(math.sqrt(5.773503*abs(d)/row['max_acceleration_rad_s2']) for d,row in zip(delta,rows))*1.001)
        if duration>60:raise ConsoleError('目标过渡超过60秒',412,'trajectory_limits')
        for attempt in range(32):
            self.duration=float(duration);v=np.asarray(velocities)*duration;a=np.asarray(accelerations)*duration**2
            self.coefficients=np.array([positions,v,a/2,10*delta-6*v-1.5*a,-15*delta+8*v+1.5*a,6*delta-3*v-.5*a],dtype=float).T
            if self._valid():return
            duration*=1.2
            if duration>60:break
        raise ConsoleError('目标轨迹无法同时满足限位/限速/加速度，请减小步幅或等待停稳',412,'trajectory_limits')
    def _extrema(self,c):
        np=self.np;d=np.polynomial.polynomial.polyder(c);times=[0.,1.]
        if np.any(abs(d)>1e-12):times += [float(r.real) for r in np.polynomial.polynomial.polyroots(d) if abs(r.imag)<1e-8 and 0<r.real<1]
        return [float(np.polynomial.polynomial.polyval(t,c)) for t in times]
    def _valid(self):
        np=self.np
        for c,row in zip(self.coefficients,self.rows):
            q=self._extrema(c);v=self._extrema(np.polynomial.polynomial.polyder(c)/self.duration);a=self._extrema(np.polynomial.polynomial.polyder(c,2)/self.duration**2)
            if min(q)<row['lower']-1e-8 or max(q)>row['upper']+1e-8 or max(map(abs,v))>row['max_velocity_rad_s']+1e-8 or max(map(abs,a))>row['max_acceleration_rad_s2']+1e-8:return False
        return True
    def sample(self,elapsed):
        np=self.np;u=max(0,min(1,elapsed/self.duration))
        return tuple([float(np.polynomial.polynomial.polyval(u,np.polynomial.polynomial.polyder(c,order))/self.duration**order) for c in self.coefficients] for order in (0,1,2))


def encode_lowcmd(factory,crc,positions,velocities,rows,mode_machine,kind='position',ramp=1.):
    """Create a fresh HG message. Unused slots 29..34 remain disabled every frame."""
    if type(mode_machine)is not int or not 0<=mode_machine<=255 or len(positions)!=29 or len(velocities)!=29:raise ConsoleError('LowCmd维度或 mode_machine 无效')
    if kind not in {'position','damping','disabled'}:raise ConsoleError('未知LowCmd控制类型')
    msg=factory();msg.mode_pr=0;msg.mode_machine=mode_machine
    if len(msg.motor_cmd)!=35:raise ConsoleError('SDK HG LowCmd电机槽位应为35',412,'sdk_incompatible')
    for i,motor in enumerate(msg.motor_cmd):
        motor.mode=0;motor.q=0.;motor.dq=0.;motor.tau=0.;motor.kp=0.;motor.kd=0.;motor.reserve=0
        if i>=29 or kind=='disabled':continue
        row=rows[i];q=positions[i];dq=velocities[i]
        if not finite(q) or not finite(dq) or not 0<=ramp<=1:raise ConsoleError('LowCmd包含非法数值')
        if kind=='position' and (not row['lower']-1e-7<=q<=row['upper']+1e-7 or abs(dq)>row['max_velocity_rad_s']+1e-7):raise ConsoleError('LowCmd目标超限',412,'target_limits')
        motor.mode=1;motor.q=float(q);motor.dq=float(dq) if kind=='position' else 0.
        motor.kp=float(row['kp']*ramp) if kind=='position' else 0.;motor.kd=float(row['kd'])
    msg.reserve=[0]*4;msg.crc=crc.Crc(msg)
    return msg


class Feedback:
    def __init__(self,rows,mode_machine,crc,clock=time.monotonic):
        self.rows,self.mode_machine,self.crc,self.clock=rows,mode_machine,crc,clock
        self.last_tick=None;self.at=-math.inf;self.data=None;self.rejected=0;self.reason='等待有效LowState'
    def accept(self,msg):
        try:
            if msg.crc!=self.crc.Crc(msg):raise ValueError('LowState CRC不一致')
            tick=msg.tick
            if type(tick)is not int or not 0<=tick<=0xffffffff:raise ValueError('LowState tick无效')
            if self.last_tick is not None and not 0<((tick-self.last_tick)&0xffffffff)<0x80000000:raise ValueError('LowState tick重复或回退')
            if msg.mode_pr!=0 or self.mode_machine is not None and msg.mode_machine!=self.mode_machine:raise ValueError('机器控制模式与标定不一致')
            if len(msg.motor_state)!=35:raise ValueError('HG LowState槽位不兼容')
            q=[];dq=[];tau=[];temps=[]
            for motor,row in zip(msg.motor_state,self.rows):
                if not all(finite(v) for v in (motor.q,motor.dq,motor.tau_est)) or not row['lower']-.02<=motor.q<=row['upper']+.02:raise ValueError('关节反馈数值/限位异常')
                if motor.motorstate!=0:raise ValueError('电机报告故障状态')
                if len(motor.temperature)!=2 or not all(finite(v) and -20<=v<=100 for v in motor.temperature):raise ValueError('电机温度反馈无效')
                q.append(float(motor.q));dq.append(float(motor.dq));tau.append(float(motor.tau_est));temps.append(float(max(motor.temperature)))
            rpy=list(msg.imu_state.rpy)
            if len(rpy)!=3 or not all(finite(v) for v in rpy):raise ValueError('IMU反馈无效')
            self.last_tick=tick;self.at=self.clock();self.reason='';self.data={'positions':q,'velocities':dq,'torques':tau,'temperatures':temps,'rpy':rpy,'tick':tick,'mode_machine':msg.mode_machine}
            return True
        except (ValueError,TypeError,AttributeError,IndexError) as exc:
            self.rejected+=1;self.reason=str(exc)[:120];return False
    def view(self,timeout):
        if self.data is None or self.clock()-self.at>timeout:raise ConsoleError('LowState缺失、校验失败或超过反馈时限',412,'feedback_stale')
        return self.data
