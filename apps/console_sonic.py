"""Managed SONIC sessions. Start is explicit; real startup requires onsite approval."""
from __future__ import annotations
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import threading
import time
import uuid
from console_support import ConsoleError, age, atomic_json, now, process_identity, read_json
from sonic_container import BINARY
from sonic_commission import load_gate

TERMINAL = {'stopped', 'failed'}


def endpoint(value):
    match = re.fullmatch(r'tcp://(127\.[0-9.]+):([0-9]+)', value or '')
    if not match or not ipaddress.ip_address(match[1]).is_loopback or not 1024 <= int(match[2]) <= 65535:
        raise ConsoleError('托管SONIC输入/反馈地址须为本机回环端口1024～65535', 412, 'sonic_endpoint')
    return match[1], int(match[2])


def connection(driver, mode):
    value = driver.config(mode)
    if mode not in {'sim', 'real'}: raise ConsoleError('SONIC模式无效')
    if value['dds_domain'] != 0:
        raise ConsoleError('当前SONIC C++固定DDS Domain 0；不能静默忽略其他域配置', 412, 'sonic_domain')
    if mode == 'sim' and value['interface'] != 'lo':
        raise ConsoleError('SONIC仿真必须明确绑定lo，禁止使用物理网卡', 412, 'sonic_sim_interface')
    if mode == 'real' and value['interface'] == 'lo':
        raise ConsoleError('SONIC真机必须配置专用物理网卡', 412, 'sonic_real_interface')
    endpoint(value['pose_endpoint']); endpoint(value['state_endpoint'])
    if endpoint(value['pose_endpoint'])[1] == endpoint(value['state_endpoint'])[1]:
        raise ConsoleError('SONIC输入端口与反馈端口必须不同', 412, 'sonic_endpoint')
    return value


def controller_argv(config, mode):
    _, input_port = endpoint(config['pose_endpoint'])
    _, output_port = endpoint(config['state_endpoint'])
    args = [BINARY, 'lo' if mode == 'sim' else config['interface'],
            'policy/release/model_decoder.onnx', 'reference/example/',
            '--obs-config', 'policy/release/observation_config.yaml',
            '--encoder-file', 'policy/release/model_encoder.onnx',
            '--planner-file', 'planner/target_vel/V2/planner_sonic.onnx',
            '--input-type', 'zmq_manager', '--output-type', 'zmq',
            '--zmq-host', endpoint(config['pose_endpoint'])[0], '--zmq-port', str(input_port), '--zmq-out-port', str(output_port)]
    if mode == 'sim': args.append('--disable-crc-check')
    return args


def code_fingerprint(app):
    return hashlib.sha256(b''.join((Path(app) / name).read_bytes() for name in
        ('console_sonic.py', 'console_sonic_worker.py', 'sonic_container.py', 'sonic_feedback.py', 'sonic_commission.py'))).hexdigest()


def request_stop(directory, reason='explicit stop'):
    directory = Path(directory) / 'sonic-control'
    request = read_json(directory / 'request.json')
    if request.get('run_id'):
        atomic_json(directory / 'stop.json', {'run_id': request['run_id'], 'reason': reason, 'at': now()})


class SonicControl:
    def __init__(self, driver, directory, profile):
        self.driver, self.profile = driver, profile
        self.directory = Path(directory) / 'sonic-control'
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        if hasattr(driver, 'supervisor') and driver.supervisor.running('sonic-session'):
            request_stop(self.directory.parent, 'web backend restarted; explicit restart required')

    def active(self):
        request = read_json(self.directory / 'request.json')
        if not request: return False
        row = read_json(self.directory / 'status.json')
        alive = hasattr(self.driver, 'supervisor') and self.driver.supervisor.running('sonic-session')
        return bool(alive or (row.get('run_id') == request.get('run_id') and not row.get('stop_confirmed') and row.get('container_id')))

    def gate(self, mode):
        if mode == 'sim': return {'ready': True, 'message': '隔离仿真：仅loopback DDS，不连接物理G1'}
        try:
            document = load_gate(self.directory / 'commissioning.json', self.driver.root, self.driver.app_root,
                                 connection(self.driver, mode), self.profile)
            return {'ready': True, 'message': 'SONIC专项现场授权有效；启动仍需明确确认', 'expires_at_unix': document['expires_at_unix']}
        except (ConsoleError, OSError, ValueError, AttributeError) as exc:
            return {'ready': False, 'code': getattr(exc, 'code', 'sonic_onsite_required'), 'message': str(exc)}

    def status(self, mode):
        request = read_json(self.directory / 'request.json')
        raw = read_json(self.directory / 'status.json')
        alive = hasattr(self.driver, 'supervisor') and self.driver.supervisor.running('sonic-session')
        record = self.driver.supervisor.record('sonic-session') if hasattr(self.driver, 'supervisor') else {}
        current = bool(alive and raw.get('pid') == record.get('pid') and raw.get('run_id') == request.get('run_id') and age(raw.get('heartbeat_at')) < 2)
        active = self.active()
        other = active and request.get('mode') != mode
        bootstrapping = bool(alive and not current and raw.get('phase') == 'starting' and raw.get('run_id') == request.get('run_id') and age(record.get('started_at')) < 10)
        phase = raw.get('phase', 'starting') if current else 'starting' if bootstrapping else 'fault' if active else 'failed' if request and raw.get('phase') == 'starting' else raw.get('phase', 'stopped')
        detail = '正在启动托管进程，等待首个心跳' if bootstrapping else raw.get('message', '') if current or not active else '托管进程反馈丢失或控制器退出尚未确认；请停止并核对日志'
        feedback = raw.get('feedback', {}) if current else {}
        feedback_valid = bool(current and not other and feedback.get('valid') and age(feedback.get('observed_at')) <= .5)
        feedback = {**feedback, 'valid': feedback_valid}
        gate = self.gate(mode)
        start_reason = '另一个SONIC会话仍在运行或等待退出确认' if active else '' if gate['ready'] else gate['message']
        try: connection(self.driver, mode)
        except ConsoleError as exc: start_reason = str(exc)
        if other:
            detail = f"{request['mode']} 环境存在SONIC会话；切回对应环境管理"
        state = 'running' if feedback_valid else 'ready' if phase in {'waiting_input', 'ready'} else 'failed' if phase in {'fault', 'failed'} else 'stopped' if not active else 'starting'
        return {'state': state, 'phase': phase, 'mode': request.get('mode', mode), 'owned': bool(request),
                'run_id': request.get('run_id'), 'observed_at': feedback.get('observed_at'), 'detail': detail or '控制器尚未启动',
                'process_running': bool(current and raw.get('controller_running')), 'initialized': bool(current and raw.get('initialized')),
                'feedback_valid': feedback_valid, 'feedback': feedback, 'components': raw.get('components', {}) if current else {},
                'gate': gate, 'mode_conflict': bool(other), 'start_allowed': not start_reason, 'start_reason': start_reason,
                'stop_allowed': bool(active and not other), 'stop_reason': '请切回运行会话的环境' if other else '' if active else '当前没有托管SONIC会话',
                'stop_confirmed': bool(raw.get('stop_confirmed') and not alive), 'motion_stop_supported': False,
                'message': detail, 'parent_lost': raw.get('parent_lost', False), 'fault': raw.get('fault'),
                'input_ready': bool(current and raw.get('input_ready')), 'configuration_heartbeat_at': raw.get('configuration_heartbeat_at') if current else None}

    def start(self, mode, payload):
        with self.lock:
            if set(payload) - {'service_id', 'confirmed_real_start'}: raise ConsoleError('控制器启动包含未知参数')
            if self.active(): raise ConsoleError('已有SONIC会话或未确认退出的控制器，禁止重复启动', 409, 'sonic_session_conflict')
            config = connection(self.driver, mode)
            gate = self.gate(mode)
            if not gate['ready']: raise ConsoleError(gate['message'], 412, gate.get('code', 'sonic_onsite_required'))
            if mode == 'real' and payload.get('confirmed_real_start') is not True:
                raise ConsoleError('须明确确认SONIC会进入默认站姿并动作手部，且现场停止条件已就绪', 412, 'sonic_start_confirmation')
            if not (self.driver.root / '.venv_teleop/bin/python').is_file():
                raise ConsoleError('SONIC teleop Python环境缺失', 412, 'sonic_environment')
            manager = self.driver.root / 'gear_sonic/scripts/pico_manager_thread_server.py'
            if not manager.is_file() or '# Robot Station: optional private manager uplink.' not in manager.read_text():
                raise ConsoleError('请先安装随仓库提供的PICO Manager回环绑定扩展', 412, 'sonic_manager_integration')
            request = {'run_id': uuid.uuid4().hex, 'mode': mode, 'connection': config,
                       'parent_pid': os.getpid(), 'parent_start_ticks': process_identity(os.getpid()),
                       'code_fingerprint': code_fingerprint(self.driver.app_root), 'started_at': now(),
                       'confirmed_real_start': payload.get('confirmed_real_start') is True}
            atomic_json(self.directory / 'request.json', request)
            atomic_json(self.directory / 'status.json', {'run_id': request['run_id'], 'phase': 'starting', 'message': '已接收启动任务', 'stop_confirmed': False})
            self.driver.supervisor.start('sonic-session', [str(self.driver.root / '.venv_teleop/bin/python'), '-u',
                str(self.driver.app_root / 'console_sonic_worker.py'), '--sonic-root', str(self.driver.root),
                '--directory', str(self.directory)], self.driver.root)
            return {'state': 'accepted', 'controller_run_id': request['run_id'], 'message': '开始准备SONIC会话；以实际初始化和反馈判断是否就绪'}

    def stop(self, mode=None, reason='explicit console stop', timeout=16):
        with self.lock:
            request = read_json(self.directory / 'request.json')
            if mode and self.active() and request.get('mode') != mode:
                raise ConsoleError('请切回运行SONIC的环境后停止', 409, 'sonic_mode_conflict')
            if not self.active(): return {'state': 'stopped', 'message': '没有运行中的托管SONIC会话', 'stop_confirmed': True, 'motion_stop_supported': False}
            request_stop(self.directory.parent, reason)
            if not self.driver.supervisor.running('sonic-session'):
                self.driver.supervisor.start('sonic-session', [str(self.driver.root / '.venv_teleop/bin/python'), '-u',
                    str(self.driver.app_root / 'console_sonic_worker.py'), '--sonic-root', str(self.driver.root),
                    '--directory', str(self.directory), '--recover-stop'], self.driver.root)
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                row = read_json(self.directory / 'status.json')
                if row.get('run_id') == request.get('run_id') and row.get('stop_confirmed') and not self.driver.supervisor.running('sonic-session'):
                    return {'state': 'stopped', 'message': 'SONIC控制器退出已确认，托管输入和仿真已关闭；不代表硬件急停', 'stop_confirmed': True, 'motion_stop_supported': False}
                time.sleep(.1)
            raise ConsoleError('SONIC退出尚未确认；保留进程归属与日志，请核对实际状态', 503, 'sonic_stop_unconfirmed')

    def logs(self, mode, component='supervisor'):
        if component not in {'supervisor', 'controller', 'manager', 'simulator', 'preparation'}: raise ConsoleError('日志组件无效')
        request = read_json(self.directory / 'request.json')
        if request.get('mode') not in {None, mode}: raise ConsoleError('请切回运行会话的环境读取日志', 409, 'sonic_mode_conflict')
        if component == 'supervisor': return self.driver.supervisor.logs('sonic-session')
        run_id = request.get('run_id', '')
        if not re.fullmatch(r'[0-9a-f]{32}', run_id): return ''
        path = self.directory / 'runs' / run_id / (component + '.log' if component in {'controller', 'preparation'} else 'children/' + component + '.log')
        try:
            with path.open('rb') as handle:
                handle.seek(max(0, path.stat().st_size - 12000))
                return handle.read(12000).decode('utf-8', errors='replace')
        except OSError: return ''
