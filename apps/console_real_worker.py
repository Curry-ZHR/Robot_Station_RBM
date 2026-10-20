"""Explicitly armed G1 HG/PR writer with independent feedback/lease watchdogs."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import math
import os
from pathlib import Path
import signal
import time
from console_support import ConsoleError,atomic_json,now,read_json
from unitree_g1_control import MOTOR_NAMES,QuinticPlan,encode_lowcmd,load_commissioning

class RealControlLoop:
    def __init__(self,transport,commissioning,clock=time.monotonic):
        # Warm numerical imports while no writer exists, before any motion lease.
        import numpy
        self.transport,self.config,self.clock=transport,commissioning,clock;self.rows=commissioning['joints'];self.state='ready';self.reason='';self.plan=None;self.q=None;self.dq=[0.]*29;self.ddq=[0.]*29;self.target=None;self.target_id=None;self.session=None;self.sequence=-1;self.started=0;self.plan_at=0;self.stop_at=None;self.last_step=None;self.source=None;self.writes=0;self.stop_acknowledged=False
    def _observe(self):
        data=self.transport.observe(self.config)
        if self.source and data['source_guid']!=self.source:raise ConsoleError('LowState来源已变化',412,'state_source_changed')
        if max(data['temperatures'])>self.config['max_motor_temperature_c']:raise ConsoleError('电机温度超过标定上限',412,'motor_temperature')
        if max(abs(v) for v in data['rpy'][:2])>self.config['max_imu_tilt_rad']:raise ConsoleError('IMU倾角超出受支撑调试范围',412,'imu_tilt')
        for row,tau in zip(self.rows,data['torques']):
            if abs(tau)>row['torque_limit_nm']:raise ConsoleError('反馈力矩超过标定上限',412,'motor_torque')
        return data
    def arm(self,session):
        if self.state!='ready':raise ConsoleError('控制器不处于可接管状态',409,'controller_state')
        self._observe();self.transport.arm()
        try:
            data=self._observe();self.q=list(data['positions'])
            for q,row in zip(self.q,self.rows):
                if not row['lower']<=q<=row['upper']:raise ConsoleError('接管姿态超出标定范围',412,'target_limits')
            self.target=list(self.q);self.dq=[0.]*29;self.ddq=[0.]*29;self.started=self.clock();self.last_step=self.started;self.source=data['source_guid'];self.session=session;self.sequence=-1;self.state='active';self.stop_acknowledged=False
        except Exception:self.transport.disarm();raise
    def set_target(self,positions,sequence,target_id,duration,velocity_limit=.2):
        if self.state!='active' or type(sequence)is not int or sequence<=self.sequence:raise ConsoleError('目标序号或控制状态无效',409,'target_sequence')
        if not isinstance(positions,list) or len(positions)!=29 or not finite_number(duration) or not .25<=duration<=60:raise ConsoleError('目标轨迹参数无效')
        data=self._observe();stamp=self.clock()
        start=self.plan.sample(stamp-self.plan_at) if self.plan else (self.q,self.dq,self.ddq)
        for q,feedback,row in zip(positions,data['positions'],self.rows):
            if not finite_number(q) or not row['lower']<=q<=row['upper'] or abs(q-feedback)>row['max_step_rad']:raise ConsoleError('目标超出标定限位或单次步幅，请分步调试',412,'target_limits')
        if not finite_number(velocity_limit) or not .01<=velocity_limit<=.5:raise ConsoleError('目标速度上限无效')
        plan_rows=[{**row,'max_velocity_rad_s':min(velocity_limit,row['max_velocity_rad_s'])} for row in self.rows]
        plan=QuinticPlan(*start,positions,plan_rows,duration)
        self.plan=plan;self.plan_at=stamp;self.target=list(positions);self.target_id=target_id;self.sequence=sequence
        return plan.duration
    def stop(self,reason='已释放手动控制'):
        if self.state=='active':self.state='stopping';self.reason=reason;self.stop_at=self.clock()
        elif self.state=='ready':self.stop_acknowledged=True
    def fault(self,reason):
        # Invalid/missing state or foreign controller: do not send an extra command
        # against unknown state/another owner. Hardware support/stop remains essential.
        self.reason=reason;self.state='fault';self.transport.disarm();self.session=None;self.stop_acknowledged=False
    def step(self,lease_deadline):
        if self.state not in {'active','stopping'}:return None
        try:
            stamp=self.clock()
            if self.last_step is not None and stamp-self.last_step>.02:raise ConsoleError('控制循环调度超过20ms，停止输出',412,'control_deadline')
            self.last_step=stamp;data=self._observe()
            if self.state=='active' and stamp>=lease_deadline:self.stop('浏览器心跳过期')
            if self.state=='stopping':
                kind='damping' if stamp-self.stop_at<self.config['damping_seconds'] else 'disabled'
                msg=encode_lowcmd(self.transport.factory,self.transport.crc,data['positions'],[0.]*29,self.rows,self.config['mode_machine'],kind)
                self.transport.write(msg);self.writes+=1
                if kind=='disabled' and stamp-self.stop_at>=self.config['damping_seconds']+.1:self.transport.disarm();self.state='stopped';self.session=None;self.stop_acknowledged=True
                return data
            if self.plan:self.q,self.dq,self.ddq=self.plan.sample(stamp-self.plan_at)
            if max(abs(q-real) for q,real in zip(self.q,data['positions']))>self.config['tracking_error_rad']:raise ConsoleError('目标与实际姿态偏差过大',412,'tracking_error')
            ramp=min(1.,(stamp-self.started)/1.)
            for q,dq,real,speed,row in zip(self.q,self.dq,data['positions'],data['velocities'],self.rows):
                predicted=row['kp']*ramp*(q-real)+row['kd']*(dq-speed)
                if abs(predicted)>row['torque_limit_nm']:raise ConsoleError('估算PD力矩超限，停止输出',412,'command_torque')
            msg=encode_lowcmd(self.transport.factory,self.transport.crc,self.q,self.dq,self.rows,self.config['mode_machine'],ramp=ramp)
            self.transport.write(msg);self.writes+=1;return data
        except Exception as exc:self.fault(str(exc));return None
    def status(self,data=None):
        error=max(abs(q-real) for q,real in zip(self.target,data['positions'])) if self.target is not None and data else None
        reached=bool(self.plan and self.clock()-self.plan_at>=self.plan.duration and error is not None and error<.03)
        return {'state':self.state,'reason':self.reason,'writes':self.writes,'mode_machine':self.config['mode_machine'],'source':'Unitree SDK2 HG/PR 真机反馈','provider':'unitree-sdk2-hg-pr','target_id':self.target_id,'target_state':'reached' if reached else 'moving' if self.plan and self.state=='active' else 'held','max_error_rad':error,'stop_acknowledged':self.stop_acknowledged,'sequence':self.sequence,'joints':[{'name':name,'position_rad':q} for name,q in zip(MOTOR_NAMES,data['positions'])] if data else [],'feedback_age_seconds':data.get('feedback_age_seconds') if data else None}

def finite_number(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True);p.add_argument('--sonic-root',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);args=p.parse_args()
    directory=args.directory;profile=read_json(args.profile);connection=read_json(directory/'connection.json');config=load_commissioning(directory/'commissioning.json',profile,connection,args.sonic_root)
    from unitree_g1_transport import UnitreeTransport
    lock_dir=Path('/run/user')/str(os.getuid());lock_dir.mkdir(exist_ok=True)
    owner=(lock_dir/f"robot-station-g1-{connection['dds_domain']}-{connection['interface']}.lock").open('a');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    transport=UnitreeTransport(connection,config);loop=RealControlLoop(transport,config);running=True;last_command=None;ack={};next_status=0;next_gate=0;deadline=time.monotonic();last_data=None
    def shutdown(*_):
        nonlocal running
        running=False;loop.stop('工作台退出')
    signal.signal(signal.SIGTERM,shutdown);signal.signal(signal.SIGINT,shutdown)
    try:
        while running or loop.state=='stopping':
            stamp=time.monotonic();command=read_json(directory/'control.json')
            if stamp>=next_gate:
                try:
                    current=load_commissioning(directory/'commissioning.json',profile,connection,args.sonic_root)
                    if current['file_fingerprint']!=config['file_fingerprint']:raise ConsoleError('标定参数已变化')
                except Exception as exc:loop.fault(str(exc))
                next_gate=stamp+.25
            armed=command.get('armed')is True and command.get('lease_deadline',0)>stamp and stamp-command.get('updated_monotonic',0)<3
            if not armed and loop.state=='active':loop.stop('控制权已释放或心跳过期')
            if armed and command.get('id')!=last_command and running:
                last_command=command.get('id')
                try:
                    if loop.state=='ready':loop.arm(command['session'])
                    if loop.state!='active' or command.get('session')!=loop.session:raise ConsoleError('本次控制会话已终止，请重新初始化',409,'controller_state')
                    duration=None
                    if command.get('sequence',-1)>loop.sequence:duration=loop.set_target(command['positions'],command['sequence'],command['id'],command.get('duration',3),command.get('velocity_limit',.2))
                    ack={'id':last_command,'ok':True,'duration_seconds':duration}
                except Exception as exc:ack={'id':last_command,'ok':False,'message':str(exc)}
                atomic_json(directory/'ack.json',ack);deadline=time.monotonic()
            data=loop.step(command.get('lease_deadline',0))
            if data:last_data=data
            if loop.state=='ready':
                try:last_data=loop._observe();loop.reason=''
                except Exception as exc:last_data=None;loop.reason=str(exc)
            if stamp>=next_status:
                atomic_json(directory/'status.json',{'pid':os.getpid(),'heartbeat_at':now(),'observed_at':now() if last_data else None,'worker_fingerprint':config['control_fingerprint'],**loop.status(last_data)})
                next_status=stamp+.02
            deadline+=.002;delay=deadline-time.monotonic()
            if delay>0:time.sleep(delay)
            elif delay<-.02 and loop.state=='active':loop.fault('控制循环超时')
            elif delay<0:deadline=time.monotonic()
            if loop.state in {'fault','stopped'}:break
    finally:
        transport.close();atomic_json(directory/'status.json',{'pid':os.getpid(),'heartbeat_at':now(),'observed_at':None,**loop.status(None)})

if __name__=='__main__':main()
