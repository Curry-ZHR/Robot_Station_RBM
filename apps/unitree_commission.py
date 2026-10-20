"""Local commissioning tools. template/inspect/validate never create a publisher.

approve requires physical attestations, live read-only observations and an explicit
terminal phrase; it does NOT arm the robot. Never run approve unattended.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import time
from console_driver import SystemDriver
from console_support import ConsoleError,atomic_json,read_json
from unitree_g1_control import MOTOR_NAMES,boot_id,control_fingerprint,digest,machine_fingerprint,sdk_fingerprint,template,validate_parameters


def inspect_hardware(connection,profile,seconds=3):
    from unitree_g1_transport import UnitreeTransport
    config=template(profile);transport=UnitreeTransport(connection,config);samples=[];started=time.monotonic()
    try:
        while time.monotonic()-started<seconds:
            with transport.lock:
                data=transport.feedback.data
                if data and (not samples or samples[-1]['tick']!=data['tick']):samples.append(data)
            time.sleep(.01)
        if len(samples)<10:raise ConsoleError('未收到足够有效LowState样本；请先核对接线、DDS网卡和域',412,'feedback_stale')
        latest=samples[-1]
        with transport.lock:
            source=transport.observe(config)
        stable=max(max(row['positions'][i] for row in samples)-min(row['positions'][i] for row in samples) for i in range(29))<.01
        stationary=max(abs(v) for row in samples for v in row['velocities'])<.03
        same_mode=len({row['mode_machine'] for row in samples})==1
        return {'ok':True,'samples':len(samples),'mode_pr':0,'mode_machine':latest['mode_machine'],'stationary':bool(stable and stationary and same_mode),
                'lowstate_source_guid':source['source_guid'],'unique_lowstate_source':True,'unitree_motion_service_empty':True,'foreign_lowcmd_publishers':source['foreign_publishers'],
                'joints':[{'name':name,'motor_index':i,'position_rad':latest['positions'][i],'temperature_c':latest['temperatures'][i],'tau_est_nm':latest['torques'][i]} for i,name in enumerate(MOTOR_NAMES)],'imu_rpy':latest['rpy'],
                'notice':'只读观测不能证明硬件型号、机械支撑、增益或停止效果已验证'}
    finally:transport.close()


def approve_document(document,profile,connection,root,observation):
    validate_parameters(document,profile)
    if document['interface']!=connection['interface'] or document['dds_domain']!=connection['dds_domain']:raise ConsoleError('标定网卡/域与工作台配置不一致')
    for flag in ('physical_support_confirmed','hardware_mapping_verified','gains_validated','stop_tested'):
        if document.get(flag)is not True:raise ConsoleError('须现场确认 '+flag)
    if not observation.get('stationary') or observation.get('mode_machine')!=document['mode_machine']:raise ConsoleError('实际机器模式不一致或机器人未静止')
    if observation.get('foreign_lowcmd_publishers')!=0 or observation.get('unique_lowstate_source')is not True or observation.get('unitree_motion_service_empty')is not True:raise ConsoleError('实际控制源尚未空闲或唯一')
    stamp=time.time()
    return {**document,'approved':True,'approved_at_unix':stamp,'expires_at_unix':stamp+4*3600,'machine_fingerprint':machine_fingerprint(),'boot_id':boot_id(),'sdk_fingerprint':sdk_fingerprint(root),'control_fingerprint':control_fingerprint(),'lowstate_source_guid':observation['lowstate_source_guid']}


def main():
    app=Path(__file__).resolve().parent
    p=argparse.ArgumentParser(description='G1 本地标定/只读核验工具；不会自动接管或运动')
    p.add_argument('action',choices=('template','inspect','validate','approve','revoke'))
    p.add_argument('--sonic-root',type=Path,default=app.parents[1]/'sonic_deploy')
    p.add_argument('--runtime-dir',type=Path,default=app/'.runtime/console')
    p.add_argument('--file',type=Path)
    args=p.parse_args();profile=read_json(app/'static/assets/g1/profile.json');driver=SystemDriver(args.sonic_root,args.runtime_dir,app);connection=driver.config('real');path=args.file or args.runtime_dir/'real-control/commissioning.json'
    os.umask(0o077)
    if args.action=='template':
        if path.exists():raise ConsoleError('目标文件已存在，不覆盖现有标定；请指定新的--file')
        row=template(profile);row.update(interface=connection['interface'],dds_domain=connection['dds_domain']);atomic_json(path,row);path.chmod(0o600)
        print(json.dumps({'ok':True,'file':str(path),'approved':False,'message':'已生成待现场填写的参考模板，未开启运动'},ensure_ascii=False));return
    if args.action=='inspect':print(json.dumps(inspect_hardware(connection,profile),ensure_ascii=False,indent=2));return
    document=read_json(path)
    if not document:raise ConsoleError('标定文件不存在')
    if args.action=='revoke':document['approved']=False;atomic_json(path,document);path.chmod(0o600);print('本地标定授权已撤销；运行中适配器将停止输出。');return
    validate_parameters(document,profile)
    if args.action=='validate':print('软件参数校验通过；此结果不代表实机增益/停止效果已标定，也不会开启运动。');return
    observation=inspect_hardware(connection,profile)
    if input('请在现场确认：完整29自由度且未锁腰、可靠机械支撑、增益与停止方式已验证。输入 G1 SUPPORTED 29 UNLOCKED 才可授权本次开机4小时：\n').strip()!='G1 SUPPORTED 29 UNLOCKED':raise ConsoleError('未授权，未开启真机运动')
    approved=approve_document(document,profile,connection,args.sonic_root,observation);atomic_json(path,approved);path.chmod(0o600)
    print('现场授权已保存，最长4小时且仅本次开机有效；仍需网页初始化并显式手动接管，不会自动运动。')

if __name__=='__main__':
    try:main()
    except ConsoleError as exc:raise SystemExit(str(exc))
