"""Headless fixed-base MuJoCo PD simulation. Never imports or publishes Unitree DDS."""
from __future__ import annotations
import argparse
import math
import os
from pathlib import Path
import signal
import time
import xml.etree.ElementTree as ET
from console_support import atomic_json, now, read_json


class Physics:
    def __init__(self, xml_path, names):
        import mujoco
        import numpy as np
        self.mj,self.np=mujoco,np
        xml_path=Path(xml_path);tree=ET.parse(xml_path);root=tree.getroot()
        root.find('compiler').set('meshdir',str(xml_path.parent/'meshes'))
        for body in root.iter('body'):
            for joint in list(body.findall('joint')):
                if joint.get('type')=='free':body.remove(joint)
        self.model=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'))
        self.data=mujoco.MjData(self.model);self.names=names
        ids=[mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_JOINT,n) for n in names]
        self.a=[mujoco.mj_name2id(self.model,mujoco.mjtObj.mjOBJ_ACTUATOR,n) for n in names]
        if min(ids+self.a)<0:raise ValueError('MuJoCo 模型缺少具名关节或 actuator')
        self.q=self.model.jnt_qposadr[ids];self.v=self.model.jnt_dofadr[ids]
        self.limits=self.model.jnt_range[ids];self.model.opt.timestep=.002
        self.model.opt.integrator=mujoco.mjtIntegrator.mjINT_IMPLICITFAST
        self.model.dof_damping[self.v]=8.
        self.torque=np.array([10. if "wrist" in n else 40. for n in names])
        for i,a in enumerate(self.a):
            if self.model.actuator_ctrllimited[a]:self.torque[i]=min(self.torque[i],abs(self.model.actuator_ctrlrange[a,1]))
        # Wrist actuators in this model use narrower hardware torque ranges.
        mujoco.mj_forward(self.model,self.data)

    def positions(self):return self.data.qpos[self.q].copy()

    def step(self,target):
        np=self.np;m=self.model;d=self.data
        command=100*(np.asarray(target)-d.qpos[self.q])+d.qfrc_bias[self.v]
        d.ctrl[self.a]=np.clip(command,-self.torque,self.torque)
        self.mj.mj_step(m,d)
        if not np.isfinite(d.qpos).all():raise ValueError('MuJoCo 状态无效')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--model',type=Path,required=True);parser.add_argument('--profile',type=Path,required=True)
    args=parser.parse_args();profile=read_json(args.profile);physics=Physics(args.model,profile['body_joints'])
    running=True
    def stop(*_):
        nonlocal running
        running=False
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    target=physics.positions();start=target.copy();goal=target.copy();began=time.monotonic();duration=1.;last_id=None;lease=False;steps=0;next_status=0;deadline=time.monotonic()
    try:
        while running:
            stamp=time.monotonic();command=read_json(args.directory/'command.json')
            active=bool(command.get('lease_deadline',0)>stamp)
            if active and command.get('id')!=last_id:
                last_id=command.get('id');start=physics.positions();goal=physics.np.asarray(command['positions']);began=stamp;duration=command['duration'];lease=True
            if not active and lease:
                target=physics.positions();goal=target.copy();start=target.copy();lease=False
            if active:
                u=min(1.,max(0.,(stamp-began)/duration));s=u**3*(10-15*u+6*u*u);target=start+s*(goal-start)
            physics.step(target);steps+=1
            if stamp>=next_status:
                positions=physics.positions();error=float(max(abs(positions-goal)));moving=bool(active and stamp-began<duration)
                atomic_json(args.directory/'status.json',{'pid':os.getpid(),'heartbeat_at':now(),'observed_at':now(),'steps':steps,
                    'provider':'mujoco-fixed-base','source':'MuJoCo 固定基座物理仿真（不验证站立平衡）','state':'running','lease_active':active,
                    'target_id':last_id,'target_state':'moving' if moving else 'reached' if active and error<.03 else 'tracking' if active else 'held',
                    'max_error_rad':error,'joints':[{'name':n,'position_rad':float(p)} for n,p in zip(physics.names,positions)]})
                next_status=stamp+.05
            deadline+=.002;delay=deadline-time.monotonic()
            if delay>0:time.sleep(delay)
            elif delay<-.05:deadline=time.monotonic()
    except Exception as exc:
        atomic_json(args.directory/'status.json',{'pid':os.getpid(),'heartbeat_at':now(),'state':'failed','error':str(exc)[:300]})
        raise
    finally:
        row=read_json(args.directory/'status.json');row.update(state='stopped',heartbeat_at=now(),lease_active=False);atomic_json(args.directory/'status.json',row)

if __name__=='__main__':main()
