"""One explicit SONIC session, loopback input proxy and independent lifecycle monitor."""
from __future__ import annotations
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import threading
import time
import uuid
from console_driver import SystemDriver
from console_sonic import code_fingerprint, connection, controller_argv, endpoint
from console_support import ConsoleError, ProcessSupervisor, age, atomic_json, now, process_identity, read_json
from sonic_container import inspect as inspect_controller, start as start_controller
from sonic_feedback import SonicFeedback
from sonic_commission import load_gate


class Session:
    def __init__(self, root, directory, recover=False):
        self.root, self.directory, self.recover = Path(root), Path(directory), recover
        self.app = Path(__file__).resolve().parent
        self.request = read_json(self.directory / 'request.json')
        self.run_id = self.request['run_id']
        if uuid.UUID(self.run_id).hex != self.run_id: raise ValueError('Invalid session identity')
        self.mode = self.request['mode']
        self.driver = SystemDriver(self.root, self.directory.parent, self.app)
        self.config = self.request['connection']
        self.run_dir = self.directory / 'runs' / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.children = ProcessSupervisor(self.run_dir / 'children')
        previous = read_json(self.directory / 'status.json') if recover else {}
        self.state = {**previous, 'run_id': self.run_id, 'pid': os.getpid(), 'mode': self.mode,
                      'phase': 'stopping' if recover else 'starting', 'stop_confirmed': False,
                      'components': {}, 'controller_running': False, 'initialized': False, 'input_ready': False}
        self.lock = threading.RLock()
        self.stop_event, self.done = threading.Event(), threading.Event()
        self.container_id = previous.get('container_id')
        self.argv = controller_argv(self.config, self.mode)
        self.child = None
        self.cpp_record = previous.get('controller_identity')
        self.context = self.publisher = self.upstream = self.feedback_socket = None
        self.feedback = SonicFeedback(max_age=.5)
        self.manager_started = False
        self.had_input = self.had_feedback = False
        self.fault = None
        self.reason = '显式停止'
        self.initialized = False
        self.started_monotonic = time.monotonic()
        self.last_gate_check = 0
        self.manager_started_at = self.last_manager_packet = self.policy_start_at = None

    def update(self, **values):
        with self.lock: self.state.update(values)

    def save(self):
        with self.lock:
            self.state['heartbeat_at'] = now()
            atomic_json(self.directory / 'status.json', self.state)

    def heartbeat(self):
        while not self.done.is_set():
            self.save()
            self.done.wait(.2)

    def requested_stop(self):
        request = read_json(self.directory / 'stop.json')
        if request.get('run_id') == self.run_id:
            self.reason = request.get('reason', '显式停止')
            return True
        if process_identity(self.request.get('parent_pid')) != self.request.get('parent_start_ticks'):
            self.reason = '网页后端退出；不会自动重新接管'
            self.update(parent_lost=True)
            return True
        return self.stop_event.is_set()

    def is_set(self): return self.requested_stop()
    def wait(self, seconds): return self.stop_event.wait(seconds)

    def stage(self, phase, message):
        self.update(phase=phase, message=message)
        print(phase + ': ' + message, flush=True)
        if self.requested_stop(): raise ConsoleError('SONIC启动已取消', 409, 'cancelled')

    def check_real(self, observe=False):
        profile = read_json(self.app / 'static/assets/g1/profile.json')
        document = load_gate(self.directory / 'commissioning.json', self.root, self.app, self.config, profile)
        if observe:
            from unitree_commission import inspect_hardware
            observation = inspect_hardware(self.config, profile, seconds=1)
            if not observation.get('stationary') or observation.get('lowstate_source_guid') != document.get('lowstate_source_guid') or observation.get('mode_machine') != document['mode_machine']:
                raise ConsoleError('SONIC启动前唯一来源/模式/静止预检不符', 412, 'sonic_real_preflight')
        return document

    def reject_foreign_host(self):
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit(): continue
            try:
                parts = [p.decode() for p in (proc / 'cmdline').read_bytes().split(b'\0') if p]
                names = {Path(p).name for p in parts[:4]}
                if names & {'g1_deploy_onnx_ref', 'run_sim_loop.py', 'pico_manager_thread_server.py'}:
                    raise ConsoleError('发现已有外部SONIC控制器/仿真/Manager，请先按其入口退出', 409, 'sonic_foreign_process')
            except (OSError, UnicodeError): continue

    @staticmethod
    def require_free_port(port):
        check = socket.socket()
        try: check.bind(('0.0.0.0', port))
        except OSError: raise ConsoleError('端口已被其他服务占用：' + str(port), 409, 'sonic_port_conflict')
        finally: check.close()

    def open_proxy(self):
        import zmq
        host, port = endpoint(self.config['pose_endpoint'])
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.setsockopt(zmq.LINGER, 0)
        self.publisher.setsockopt(zmq.SNDHWM, 10)
        self.publisher.bind(f'tcp://{host}:{port}')
        self.feedback_socket = self.context.socket(zmq.SUB)
        self.feedback_socket.setsockopt(zmq.LINGER, 0)
        self.feedback_socket.setsockopt(zmq.RCVHWM, 20)
        self.feedback_socket.setsockopt(zmq.SUBSCRIBE, b'g1_debug')
        self.feedback_socket.setsockopt(zmq.SUBSCRIBE, b'robot_config')
        self.feedback_socket.connect(self.config['state_endpoint'])

    def prepare(self):
        if self.request.get('code_fingerprint') != code_fingerprint(self.app):
            raise ConsoleError('控制代码已变化，请刷新后重新启动', 409, 'sonic_code_changed')
        if connection(self.driver, self.mode) != self.config:
            raise ConsoleError('连接配置在启动前已变化', 409, 'sonic_config_changed')
        self.reject_foreign_host()
        self.stage('starting', '准备本项目SONIC容器和XR服务')
        with (self.run_dir / 'preparation.log').open('ab') as log:
            for recipe in ('docker_start', 'docker_check', 'pc_service_start'):
                self.driver.run_recipe(recipe, self, log)
        container = self.driver.container()
        if not container.get('owned') or not container.get('running'): raise ConsoleError('SONIC项目容器未就绪', 412)
        self.container_id = container['container_id']
        self.update(container_id=self.container_id)
        if inspect_controller(self.container_id): raise ConsoleError('容器中已有外部控制器，拒绝接管', 409, 'sonic_foreign_process')
        for key in ('pose_endpoint', 'state_endpoint'): self.require_free_port(endpoint(self.config[key])[1])
        self.open_proxy()
        self.driver.start_probe(self.mode, start_cameras=False)
        if self.mode == 'sim':
            self.stage('initializing', '启动MuJoCo（无窗口，DDS仅lo）')
            env = {**os.environ, 'MUJOCO_GL': 'egl', 'OPENBLAS_NUM_THREADS': '1'}
            self.children.start('simulator', [str(self.root / '.venv_teleop/bin/python'), '-u',
                str(self.root / 'gear_sonic/scripts/run_sim_loop.py'), '--interface', 'sim',
                '--no-enable-onscreen', '--no-enable-offscreen'], self.root, env=env)
        else:
            self.stage('initializing', '核对SONIC专项现场授权和真实LowState来源；启动会进入默认站姿')
            if self.request.get('confirmed_real_start') is not True: raise ConsoleError('缺少真机启动确认')
            if (Path('/sys/class/net') / self.config['interface'] / 'carrier').read_text().strip() != '1':
                raise ConsoleError('机器人有线网卡未接通', 412, 'sonic_network')
            self.check_real(observe=True)
        self.stage('initializing', '加载SONIC模型并等待初始化；此阶段不转发PICO开始指令')
        self.controller_log = (self.run_dir / 'controller.log').open('ab')
        self.child = start_controller(self.container_id, self.run_id, self.argv, self.controller_log)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if self.requested_stop(): return
            records = inspect_controller(self.container_id, self.run_id, self.argv)
            own = [row for row in records if row['owned']]
            if any(not row['owned'] for row in records) or len(own) > 1: raise ConsoleError('控制器归属冲突', 409)
            if own:
                self.cpp_record = own[0]
                self.update(controller_identity=own[0], controller_running=True)
                return
            if self.child.poll() is not None: raise ConsoleError('SONIC控制器提前退出，请查看controller日志', 503)
            time.sleep(.15)
        raise ConsoleError('控制器进程身份确认超时', 503)

    def start_manager(self):
        import zmq
        allocator = socket.socket(); allocator.bind(('127.0.0.1', 0)); port = allocator.getsockname()[1]; allocator.close()
        self.upstream = self.context.socket(zmq.SUB)
        self.upstream.setsockopt(zmq.LINGER, 0)
        self.upstream.setsockopt(zmq.RCVHWM, 20)
        self.upstream.setsockopt(zmq.SUBSCRIBE, b'')
        self.upstream.connect('tcp://127.0.0.1:' + str(port))
        host, feedback_port = endpoint(self.config['state_endpoint'])
        env = {**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'PYTHONUNBUFFERED': '1'}
        self.children.start('manager', [str(self.root / '.venv_teleop/bin/python'), '-u',
            str(self.root / 'gear_sonic/scripts/pico_manager_thread_server.py'), '--input-source', 'xrt', '--manager',
            '--bind-host', '127.0.0.1', '--port', str(port), '--zmq_feedback_host', host,
            '--zmq_feedback_port', str(feedback_port)], self.root, env=env)
        self.manager_started = True
        self.manager_started_at = time.monotonic()
        print('PICO Manager started; motion still requires original PICO start/mode operation.', flush=True)

    def observe_input(self, message):
        mono = time.monotonic()
        self.last_manager_packet = mono
        if message.startswith(b'command') and len(message) >= 7 + 1280 + 3:
            try:
                header = json.loads(message[7:7+1280].rstrip(b'\0'))
                fields = header.get('fields', [])
                expected = [{'name': name, 'dtype': 'u8', 'shape': [1]} for name in ('start', 'stop', 'planner')]
                if fields[:3] == expected and message[7+1280] == 1 and message[7+1280+1] == 0 and self.policy_start_at is None:
                    self.policy_start_at = mono
            except (ValueError, TypeError, AttributeError):
                pass

    def check_stream_deadlines(self):
        mono = time.monotonic()
        if self.manager_started_at is not None:
            if self.last_manager_packet is None and mono - self.manager_started_at > 30 or self.last_manager_packet is not None and mono - self.last_manager_packet > 1:
                raise ConsoleError('PICO Manager输入流停止更新，正在请求SONIC停止', 503, 'sonic_input_lost')
        if self.policy_start_at is not None and not self.had_feedback and mono - self.policy_start_at > 5:
            raise ConsoleError('PICO开始指令后未收到有效控制反馈，正在请求SONIC停止', 503, 'sonic_feedback_missing')

    def read_feedback(self):
        import msgpack
        if not self.feedback_socket: return
        for _ in range(30):
            if not self.feedback_socket.poll(0): break
            raw = self.feedback_socket.recv()
            if len(raw) > 2 * 1024 * 1024: continue
            try:
                if raw.startswith(b'robot_config'):
                    self.feedback.configuration(msgpack.unpackb(raw[len(b'robot_config'):], raw=False))
                elif raw.startswith(b'g1_debug'):
                    self.feedback.feed(msgpack.unpackb(raw[len(b'g1_debug'):], raw=False))
            except (ValueError, TypeError) as exc: self.update(feedback_error=str(exc))
        status = self.feedback.status()
        self.update(feedback=status, configuration_heartbeat_at=status['configuration_observed_at'])

    def loop(self):
        import zmq
        while not self.requested_stop():
            self.read_feedback()
            if self.mode == 'real' and time.monotonic() - self.last_gate_check > 1:
                self.check_real(); self.last_gate_check = time.monotonic()
            if self.child and self.child.poll() is not None:
                self.reason = 'SONIC控制器已退出（含PICO正常停止）'
                return
            if self.mode == 'sim' and not self.children.running('simulator'):
                raise ConsoleError('MuJoCo进程退出，正在停止SONIC', 503, 'sonic_simulator_lost')
            if not self.initialized:
                text = (self.run_dir / 'controller.log').read_bytes()[-16000:].decode('utf-8', errors='replace')
                self.initialized = 'Init Done' in text and self.feedback.status()['configuration_age_seconds'] is not None
                if not self.initialized:
                    if time.monotonic() - self.started_monotonic > 180: raise ConsoleError('SONIC初始化超时', 504, 'sonic_initialization_timeout')
                    time.sleep(.02); continue
                self.update(initialized=True)
            telemetry = self.driver.telemetry(self.mode)
            pico = telemetry.get('pico', {})
            input_ready = bool(pico.get('body_ready') and age(pico.get('observed_at')) <= .5 and self.config.get('pico_calibration_confirmed') is True)
            self.update(input_ready=input_ready)
            if input_ready and not self.manager_started: self.start_manager()
            if self.manager_started and not self.children.running('manager'):
                raise ConsoleError('PICO Manager退出，正在停止SONIC', 503, 'sonic_manager_lost')
            if self.had_input and not input_ready:
                raise ConsoleError('PICO身体追踪过期或标定未就绪，已阻断输入并请求SONIC停止', 503, 'sonic_tracking_lost')
            self.had_input = self.had_input or input_ready
            if self.upstream and input_ready:
                for _ in range(30):
                    if not self.upstream.poll(0): break
                    message = self.upstream.recv()
                    if len(message) <= 2 * 1024 * 1024 and message.startswith((b'command', b'planner', b'pose', b'manager_state')):
                        self.observe_input(message)
                        self.publisher.send(message, flags=zmq.DONTWAIT)
            feedback = self.feedback.status()
            if feedback['valid']: self.had_feedback = True
            self.check_stream_deadlines()
            if self.had_feedback and (feedback['feedback_age_seconds'] is None or feedback['feedback_age_seconds'] > 1 or feedback['error']):
                raise ConsoleError('控制序号停止前进或反馈无效，正在请求SONIC停止', 503, 'sonic_feedback_lost')
            phase = 'running' if feedback['valid'] else 'ready' if input_ready else 'waiting_input'
            detail = '控制序号持续前进，测量关节反馈有效' if feedback['valid'] else 'PICO已就绪，等待PICO手柄开始/模式操作' if input_ready else 'SONIC已初始化，等待PICO身体追踪与现场标定确认'
            self.update(phase=phase, message=detail, components={'controller': True, 'manager': self.manager_started,
                        'simulator': self.mode == 'sim', 'input_proxy': True})
            time.sleep(.02)

    def stop_controller(self):
        from gear_sonic.utils.teleop.zmq.zmq_planner_sender import build_command_message
        import zmq
        self.update(phase='stopping', message='停止转发输入，发送SONIC正常停止指令并确认进程退出', input_ready=False)
        if not self.container_id: return True
        records = inspect_controller(self.container_id, self.run_id, self.argv)
        own = [row for row in records if row['owned']]
        if not own and self.child and self.child.poll() is None:
            deadline = time.monotonic() + 3
            while not own and self.child.poll() is None and time.monotonic() < deadline:
                time.sleep(.05)
                own = [row for row in inspect_controller(self.container_id, self.run_id, self.argv) if row['owned']]
            if not own and self.child.poll() is None: return False
        if not own: return True
        if len(own) != 1: raise ConsoleError('控制器归属不唯一，拒绝信号操作', 409)
        self.cpp_record = own[0]
        if not self.publisher: self.open_proxy()
        started = time.monotonic()
        while time.monotonic() - started < 8:
            self.publisher.send(build_command_message(start=False, stop=True, planner=False), flags=zmq.DONTWAIT)
            if self.child and self.child.poll() is not None:
                if not any(row['owned'] for row in inspect_controller(self.container_id, self.run_id, self.argv)): return True
            elif self.recover and not any(row['owned'] for row in inspect_controller(self.container_id, self.run_id, self.argv)):
                return True
            time.sleep(.05)
        if self.mode == 'sim':
            # Simulation only: an exact owned process may be terminated after protocol timeout.
            inspect_controller(self.container_id, self.run_id, self.argv, signal_record=self.cpp_record)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                if not any(row['owned'] for row in inspect_controller(self.container_id, self.run_id, self.argv)): return True
                time.sleep(.1)
        return False

    def cleanup(self):
        for name in ('manager', 'simulator'):
            self.children.stop(name, timeout=5)
        if self.child:
            try: self.child.wait(timeout=3)
            except subprocess.TimeoutExpired: pass
        if hasattr(self, 'controller_log'): self.controller_log.close()
        if self.context:
            for sock in (self.upstream, self.feedback_socket, self.publisher):
                if sock is not None: sock.close(linger=0)
            self.context.term()

    def run(self):
        lock = (self.directory / 'worker.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pulse = threading.Thread(target=self.heartbeat, daemon=True); pulse.start()
        for signum in (signal.SIGTERM, signal.SIGINT): signal.signal(signum, lambda *_: self.stop_event.set())
        try:
            if not self.recover:
                self.prepare()
                self.loop()
        except Exception as exc:
            self.fault = {'code': getattr(exc, 'code', type(exc).__name__), 'message': str(exc)[:600]}
            print('SONIC session error:', str(exc), flush=True)
        finally:
            confirmed = False
            try: confirmed = self.stop_controller()
            except Exception as exc:
                self.fault = {'code': 'sonic_stop_unconfirmed', 'message': str(exc)[:600]}
            controller_exited = confirmed
            if confirmed:
                try: self.cleanup()
                except Exception as exc:
                    confirmed = False
                    self.fault = {'code': 'sonic_cleanup_failed', 'message': str(exc)[:600]}
            self.update(phase=('failed' if self.fault else 'stopped') if confirmed else 'fault',
                        fault=self.fault, stop_confirmed=confirmed, controller_running=bool(self.cpp_record and not controller_exited), controller_exit_confirmed=controller_exited,
                        initialized=False, input_ready=False, message=(self.fault or {}).get('message') or self.reason)
            self.done.set(); pulse.join(timeout=2); self.save()
            lock.close()
        return 0 if confirmed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sonic-root', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--recover-stop', action='store_true')
    args = parser.parse_args()
    raise SystemExit(Session(args.sonic_root, args.directory, args.recover_stop).run())


if __name__ == '__main__': main()
