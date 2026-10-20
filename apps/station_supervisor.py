"""Long-running workbench supervisor. Boot never initializes or takes over a robot."""
from __future__ import annotations
import argparse
import fcntl
import os
from pathlib import Path
import shutil
import signal
import sys
import time
from console_driver import SystemDriver
from console_support import ProcessSupervisor, atomic_json, now, read_json


def rotate(path,limit=8*1024**2):
    try:
        if path.stat().st_size<=limit:return
        for index in (3,2,1):
            source=Path(str(path)+'.'+str(index));target=Path(str(path)+'.'+str(index+1))
            if source.exists():source.replace(target)
        shutil.copyfile(path,str(path)+'.1')
        with path.open('r+b') as handle:handle.truncate(0)
    except OSError:pass


def main():
    p=argparse.ArgumentParser();p.add_argument('--sonic-root',type=Path,required=True);p.add_argument('--host',default='0.0.0.0');p.add_argument('--port',type=int,default=9999);p.add_argument('--runtime-dir',type=Path);args=p.parse_args()
    app=Path(__file__).resolve().parent;runtime=args.runtime_dir or app/'.runtime';runtime.mkdir(parents=True,exist_ok=True)
    lock=(runtime/'station.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    supervisor=ProcessSupervisor(runtime/'station-processes');driver=SystemDriver(args.sonic_root,runtime/'console',app)
    running=True
    def stop(*_):
        nonlocal running
        running=False
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    next_probe=0;next_web=0;failures=0;last_web_start=0
    try:
        while running:
            stamp=time.monotonic()
            if not supervisor.running('web') and stamp>=next_web:
                supervisor.start('web',[sys.executable,'-u',str(app/'server.py'),'--host',args.host,'--port',str(args.port),'--sonic-root',str(args.sonic_root),'--runtime-dir',str(runtime)],args.sonic_root)
                failures=0 if stamp-last_web_start>60 else min(5,failures+1);last_web_start=stamp;next_web=stamp+min(30,2**failures)
            if stamp>=next_probe:
                if not (driver.directory/'readonly-paused').exists():
                    try:
                        mode=read_json(driver.directory/'readonly-mode.json').get('mode','real')
                        if mode not in {'real','sim'}:mode='real'
                        cameras=not (driver.directory/'camera-paused').exists()
                        if not driver.supervisor.running('probe-'+mode) or (cameras and driver.config(mode)['camera_source']=='ros2' and not driver.supervisor.running('camera-bridge')):driver.start_probe(mode,start_cameras=cameras)
                    except Exception as exc:print('Read-only services waiting:',type(exc).__name__,str(exc)[:240],flush=True)
                next_probe=stamp+20
                for path in runtime.rglob('*.log'):rotate(path)
            atomic_json(runtime/'station-status.json',{'state':'running','observed_at':now(),'web_running':supervisor.running('web'),'autonomous_motion':False})
            time.sleep(.5)
    finally:
        atomic_json(runtime/'station-status.json',{'state':'stopping','observed_at':now()})
        # Prevent new commands and revoke browser leases before stopping data readers.
        errors=[]
        try:supervisor.stop('web',timeout=25)
        except Exception as exc:errors.append(str(exc))
        atomic_json(driver.directory/'manual-sim/command.json',{})
        atomic_json(driver.directory/'real-control/control.json',{})
        # Recording SIGTERM finalizes valid buffered frames and marks the current episode discarded.
        names=[p.stem for p in driver.supervisor.directory.glob('record-*.json')]
        names += ['manual-sim','manual-real','probe-real','probe-sim','camera-bridge']
        for name in names:
            try:driver.supervisor.stop(name,timeout=45 if name.startswith('record-') else 8)
            except Exception as exc:errors.append(name+': '+str(exc))
        # Conversion cancellation markers preserve both original data and partial outputs.
        pending_conversions=[]
        for request in (runtime/'conversions').glob('*/state.json'):
            row=read_json(request)
            if row.get('state') in {'queued','running'}:
                (request.parent/'cancel').touch();pending_conversions.append(request)
        deadline=time.monotonic()+45
        while pending_conversions and time.monotonic()<deadline:
            pending_conversions=[path for path in pending_conversions if read_json(path).get('state') in {'queued','running'}]
            if pending_conversions:time.sleep(.2)
        if pending_conversions:errors.append('转换取消尚未确认；部分输出已保留')
        atomic_json(runtime/'station-status.json',{'state':'stopped' if not errors else 'stop_failed','observed_at':now(),'errors':errors,'autonomous_motion':False})
        if errors:raise RuntimeError('; '.join(errors))

if __name__=='__main__':main()
