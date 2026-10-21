"""Inspect and signal only the exact SONIC process started in an immutable container."""
from __future__ import annotations
import json
import subprocess
from console_support import ConsoleError

BINARY = '/workspace/g1_deploy/target/release/g1_deploy_onnx_ref'
SESSION_ENV = 'ROBOT_STATION_SONIC_SESSION'

# Executed with structured arguments inside the existing project-owned container.
INSPECT_SCRIPT = r'''
import json,os,signal,sys
from pathlib import Path
request=json.loads(sys.argv[1]); rows=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  exe=os.readlink(proc/'exe')
  if Path(exe).name!='g1_deploy_onnx_ref':continue
  stat=(proc/'stat').read_text().rsplit(')',1)[1].split()
  if stat[0]=='Z':continue
  argv=[s.decode() for s in (proc/'cmdline').read_bytes().split(b'\0') if s]
  env=dict(part.split(b'=',1) for part in (proc/'environ').read_bytes().split(b'\0') if b'=' in part)
  owned=(env.get(b'ROBOT_STATION_SONIC_SESSION',b'').decode()==request.get('session_id') and exe==request.get('binary') and argv==request.get('argv') and proc.stat().st_uid==os.getuid())
  rows.append({'pid':int(proc.name),'start_ticks':stat[19],'owned':owned})
 except (OSError,ValueError,UnicodeError,IndexError):continue
if request.get('signal'):
 matches=[row for row in rows if row['owned'] and row['pid']==request.get('pid') and row['start_ticks']==request.get('start_ticks')]
 if not matches:raise SystemExit('Owned controller identity was not confirmed; no signal sent')
 fd=os.pidfd_open(matches[0]['pid'])
 try:
  current=Path('/proc')/str(matches[0]['pid'])
  stat=(current/'stat').read_text().rsplit(')',1)[1].split()
  if stat[19]!=matches[0]['start_ticks']:raise RuntimeError('PID identity changed')
  signal.pidfd_send_signal(fd,signal.SIGTERM)
 finally:os.close(fd)
print(json.dumps({'processes':rows[:32]}))
'''


def inspect(container_id, session_id='', argv=None, signal_record=None, timeout=5):
    request = {'session_id': session_id, 'binary': BINARY, 'argv': argv or []}
    if signal_record:
        request.update(signal=True, pid=signal_record['pid'], start_ticks=signal_record['start_ticks'])
    result = subprocess.run(['docker', 'exec', container_id, 'python3', '-c', INSPECT_SCRIPT,
                             json.dumps(request)], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise ConsoleError('无法确认容器内控制器归属或退出状态：' + result.stderr[-500:], 503, 'controller_identity_unavailable')
    try:
        data = json.loads(result.stdout)
        if not isinstance(data.get('processes'), list): raise ValueError()
        return data['processes']
    except (ValueError, TypeError):
        raise ConsoleError('控制器进程检查结果无效', 503, 'controller_identity_unavailable')


def start(container_id, session_id, argv, log):
    if not argv or argv[0] != BINARY:
        raise ConsoleError('控制器执行路径无效')
    command = ['docker', 'exec', '--env', SESSION_ENV + '=' + session_id,
               '--workdir', '/workspace/g1_deploy', container_id,
               'bash', '-c', 'source /opt/ros/humble/setup.bash; exec "$@"', 'bash', *argv]
    return subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                            start_new_session=True)
