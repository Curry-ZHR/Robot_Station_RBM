"""Explicit Docker/GPU + loopback MuJoCo integration checks, never physical robot IO.

Run with SONIC teleop Python after normal unit tests. Synthetic IDLE input replaces
PICO only in this test subclass; production HTTP has no fixture/input override.
"""
from pathlib import Path
import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
from console_driver import default_config
from console_sonic import code_fingerprint,controller_argv
from console_sonic_worker import Session
from console_support import ProcessSupervisor,atomic_json,now,process_identity,read_json
from sonic_container import inspect as inspect_controller


def port():
    sock=socket.socket();sock.bind(('127.0.0.1',0));value=sock.getsockname()[1];sock.close();return value


class FixtureSession(Session):
    def __init__(self,root,directory,scenario):
        super().__init__(root,directory)
        assert self.mode=='sim' and self.config['interface']=='lo' and self.config['dds_domain']==0
        self.scenario=scenario;self.policy_started=None
        original=self.driver.telemetry
        def telemetry(mode):
            row=original(mode)
            expired=scenario=='tracking_loss' and self.policy_started is not None and time.monotonic()-self.policy_started>2
            row['pico']={'body_ready':True,'observed_at':'2000-01-01T00:00:00+00:00' if expired else now()}
            return row
        self.driver.telemetry=telemetry

    def start_manager(self):
        import zmq
        upstream=port()
        self.upstream=self.context.socket(zmq.SUB);self.upstream.setsockopt(zmq.LINGER,0);self.upstream.setsockopt(zmq.SUBSCRIBE,b'')
        self.upstream.connect(f'tcp://127.0.0.1:{upstream}')
        self.children.start('manager',[sys.executable,'-u',str(Path(__file__).resolve()),'--sender',str(upstream),'--scenario',self.scenario],self.root)
        self.manager_started=True;self.manager_started_at=time.monotonic()

    def read_feedback(self):
        if self.scenario=='feedback_missing' and self.initialized:return
        if self.scenario=='feedback_freeze' and self.policy_started is not None and time.monotonic()-self.policy_started>2:
            return
        super().read_feedback()
        if self.feedback.status()['valid'] and self.policy_started is None:self.policy_started=time.monotonic()


def sender(number,scenario):
    import zmq
    from gear_sonic.utils.teleop.zmq.zmq_planner_sender import build_command_message,build_planner_message
    context=zmq.Context();pub=context.socket(zmq.PUB);pub.setsockopt(zmq.LINGER,0);pub.bind(f'tcp://127.0.0.1:{number}')
    time.sleep(.6);start=time.monotonic()
    try:
        while time.monotonic()-start<180:
            if scenario=='input_freeze' and time.monotonic()-start>3:
                time.sleep(.02);continue
            pub.send(build_planner_message(mode=0,movement=[0,0,0],facing=[1,0,0],speed=0.))
            if time.monotonic()-start<.4:pub.send(build_command_message(start=True,stop=False,planner=True))
            time.sleep(.02)
    finally:pub.close();context.term()


def harness(root):
    results=[]
    for scenario in ('normal','tracking_loss','feedback_freeze','parent_loss','input_freeze','feedback_missing'):
        work=Path(tempfile.mkdtemp(prefix='station-sonic-'+scenario+'-'));directory=work/'console/sonic-control';directory.mkdir(parents=True)
        config={mode:default_config(mode) for mode in ('sim','real')}
        config['sim'].update(pose_endpoint=f'tcp://127.0.0.1:{port()}',state_endpoint=f'tcp://127.0.0.1:{port()}',pico_calibration_confirmed=True)
        assert config['sim']['pose_endpoint']!=config['sim']['state_endpoint']
        atomic_json(work/'console/runtime-config.json',config)
        parent=subprocess.Popen(['/bin/sleep','180']) if scenario=='parent_loss' else None
        parent_pid=parent.pid if parent else os.getpid()
        run_id=uuid.uuid4().hex
        request={'run_id':run_id,'mode':'sim','connection':config['sim'],'parent_pid':parent_pid,'parent_start_ticks':process_identity(parent_pid),
                 'code_fingerprint':code_fingerprint(APP),'started_at':now(),'confirmed_real_start':False}
        atomic_json(directory/'request.json',request)
        log=(work/'worker.log').open('ab')
        process=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',str(directory),'--scenario',scenario,'--sonic-root',str(root)],stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
        peak_index=0;ready=False;acted=False;last_phase=None
        try:
            deadline=time.monotonic()+180
            while time.monotonic()<deadline:
                state=read_json(directory/'status.json')
                if state.get('phase')!=last_phase:print(scenario,state.get('phase'),state.get('message'),flush=True);last_phase=state.get('phase')
                feedback=state.get('feedback',{})
                if feedback.get('valid'):
                    ready=True;peak_index=max(peak_index,feedback.get('control_index') or 0)
                if ready and peak_index>=80 and not acted:
                    if scenario=='normal':atomic_json(directory/'stop.json',{'run_id':run_id,'reason':'fixture normal stop'})
                    elif scenario=='parent_loss':parent.terminate();parent.wait(timeout=3)
                    acted=True
                if process.poll() is not None:break
                time.sleep(.1)
            else:raise AssertionError('Session deadline exceeded')
            state=read_json(directory/'status.json')
            assert scenario=='feedback_missing' or ready and peak_index>=50,(scenario,state)
            assert state.get('stop_confirmed') and not state.get('controller_running'),(scenario,state)
            assert not any(row['owned'] for row in inspect_controller(state['container_id'],run_id,controller_argv(config['sim'],'sim')))
            cpp_log=(directory/'runs'/run_id/'controller.log').read_text(errors='replace')
            assert 'Program exiting normally' in cpp_log,(scenario,cpp_log[-1500:])
            expected={'tracking_loss':'sonic_tracking_lost','feedback_freeze':'sonic_feedback_lost','input_freeze':'sonic_input_lost','feedback_missing':'sonic_feedback_missing'}.get(scenario)
            assert (state.get('fault') or {}).get('code')==expected,(scenario,state)
            if scenario=='parent_loss':assert state.get('parent_lost') is True,state
            results.append({'scenario':scenario,'pass':True,'peak_control_index':peak_index,'stop_confirmed':True,
                            'cpp_normal_exit':True,'fault':(state.get('fault') or {}).get('code'),'output':str(work)})
        finally:
            atomic_json(directory/'stop.json',{'run_id':run_id,'reason':'fixture cleanup'})
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=20)
                except subprocess.TimeoutExpired:print('Owned fixture worker pending:',str(work),flush=True)
            probes=ProcessSupervisor(work/'console/processes')
            for name in ('probe-sim','probe-real'):
                try:probes.stop(name,timeout=5)
                except Exception as exc:print('Probe cleanup:',str(exc),flush=True)
            if parent and parent.poll() is None:parent.terminate();parent.wait(timeout=3)
            log.close()
    output={'scope':'real SONIC TensorRT/Docker/MuJoCo, synthetic IDLE input, loopback DDS only','robot_motion_executed':False,'pass':True,'results':results}
    print(json.dumps(output,ensure_ascii=False,indent=2),flush=True)
    Path('/tmp/robot-station-sonic-controller-20261020/closed-loop-result.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sonic-root',type=Path,default=Path('/home/harry/workspace/sonic_deploy'))
    parser.add_argument('--worker',type=Path)
    parser.add_argument('--sender',type=int)
    parser.add_argument('--scenario',choices=('normal','tracking_loss','feedback_freeze','parent_loss','input_freeze','feedback_missing'),default='normal')
    args=parser.parse_args()
    if args.sender:sender(args.sender,args.scenario)
    elif args.worker:raise SystemExit(FixtureSession(args.sonic_root,args.worker,args.scenario).run())
    else:harness(args.sonic_root)
