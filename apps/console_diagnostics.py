"""Read-only diagnostics and allowlisted support bundles without credentials or logs."""
from __future__ import annotations
import io
import json
import os
import sys
from importlib.metadata import version,PackageNotFoundError
from pathlib import Path
import subprocess
import threading
import zipfile
from console_support import atomic_json, now

class Diagnostics:
    def __init__(self,runtime):self.runtime=runtime;self.lock=threading.Lock()
    def collect(self,mode):
        with self.lock:
            driver=self.runtime.driver;config=driver.config(mode)
            graph={'ok':False,'message':'当前来源为外部 ZMQ，不扫描 ROS 图'}
            if config['camera_source']=='ros2':
                path=self.runtime.directory/'diagnostics-ros-config.json';atomic_json(path,config['ros2_camera'])
                python=driver.app_root/'.venv_ros2_camera/bin/python';script=driver.app_root/'ros2_graph_probe.py'
                env=os.environ.copy();env.update(ROS_DOMAIN_ID=str(config['ros2_camera']['domain_id']),ROS_LOCALHOST_ONLY='1' if config['ros2_camera']['localhost_only'] else '0',RMW_IMPLEMENTATION=config['ros2_camera']['rmw'])
                # Shell source only fixed ROS distribution path, never user-provided shell text.
                try:
                    result=subprocess.run(['bash','-c','set +u; source /opt/ros/humble/setup.bash; exec "$@"','ros-graph',str(python),str(script),'--config',str(path)],env=env,capture_output=True,text=True,timeout=7)
                    graph=json.loads(result.stdout.splitlines()[-1]) if result.returncode==0 else {'ok':False,'message':'ROS 图扫描失败，请检查独立 ROS 环境'}
                except (OSError,subprocess.TimeoutExpired,ValueError,IndexError):graph={'ok':False,'message':'ROS 图扫描超时或环境不可用'}
            snapshot=self.runtime.snapshot(mode)['snapshot']
            net=[]
            for iface in sorted(Path('/sys/class/net').iterdir()):
                def read(name):
                    try:return (iface/name).read_text().strip()
                    except OSError:return None
                net.append({'name':iface.name,'state':read('operstate'),'carrier':read('carrier'),'selected':iface.name==config['interface']})
            timestamps=[row.get('source_timestamp') for row in snapshot['camera_source'].get('views',{}).values() if isinstance(row.get('source_timestamp'),(int,float))]
            import time
            timing={'max_skew_seconds':max(timestamps)-min(timestamps) if len(timestamps)==3 else None,'views':{name:{'source_age_seconds':time.time()-row['source_timestamp'] if isinstance(row.get('source_timestamp'),(int,float)) else None,'frames':row.get('frames'),'rejected':row.get('rejected')} for name,row in snapshot['camera_source'].get('views',{}).items()}}
            packages={}
            for name in ('mujoco','pyzmq','msgpack','numpy','opencv-python'):
                try:packages[name]=version(name)
                except PackageNotFoundError:packages[name]=None
            # Explicit field allowlist: never include process environment, session/key, raw logs or dataset content.
            return {'ok':True,'generated_at':now(),'mode':mode,'configuration':config,'network':net,'ros_graph':graph,'timing':timing,'versions':{'python':sys.version.split()[0],**packages},
                'camera_source':snapshot['camera_source'],'cameras':[{k:r.get(k) for k in ('id','state','fps','latency_ms','source_timestamp','observed_at','stale')} for r in snapshot['cameras']],
                'robot':{k:snapshot['robot'].get(k) for k in ('connected','stale','observed_at','source','mode','owner')},
                'battery':{k:snapshot['battery'].get(k) for k in ('percent','stale','observed_at','source')},
                'checks':[{k:r.get(k) for k in ('id','label','status','detail','source')} for r in snapshot['checks']],
                'manual':{k:snapshot.get('manual',{}).get(k) for k in ('state','owner','target_state','max_error_rad','steps','source')},
                'bundle_policy':'仅包含明确列出的诊断字段；不含操作密钥、会话、环境变量、原始日志或采集内容'}

    def bundle(self,mode):
        data=self.collect(mode);buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('diagnostics.json',json.dumps(data,ensure_ascii=False,indent=2))
            z.writestr('README.txt','Robot Station diagnostic bundle. Allowlisted status and configuration only. No credentials, cookies, environment or dataset files.\n')
        return buffer.getvalue()
