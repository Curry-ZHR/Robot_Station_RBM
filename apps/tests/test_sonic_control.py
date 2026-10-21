import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest import mock

from console_driver import default_config
from console_sonic import SonicControl, connection, controller_argv
from console_support import ConsoleError, atomic_json, now
from sonic_container import BINARY, inspect as inspect_controller
from sonic_feedback import SonicFeedback
from sonic_commission import FLAGS, FILES, load_gate, runtime_fingerprint, template
from unitree_g1_control import digest

APP = Path(__file__).resolve().parents[1]
PROFILE_PATH = APP / 'static/assets/g1/profile.json'
if not PROFILE_PATH.exists(): PROFILE_PATH = APP.parent / 'static/assets/g1/profile.json'
PROFILE = json.loads(PROFILE_PATH.read_text())


def message(index=0, **patch):
    return {'control_loop_type': 'cpp', 'index': index, 'ros_timestamp': 0.,
            'body_q': [0.] * 29, 'body_q_measured': [.2] * 29, 'body_dq': [0.] * 29,
            'last_action': [0.] * 29, **patch}


class FeedbackTests(unittest.TestCase):
    def test_actual_cpp_index_with_zero_ros_time_requires_three_advancing_frames(self):
        tracker = SonicFeedback()
        tracker.configuration({'control_frequency': 50})
        self.assertFalse(tracker.status()['valid'])
        for index in range(3):
            self.assertTrue(tracker.feed(message(index)))
            self.assertEqual(tracker.status()['valid'], index == 2)
        self.assertEqual(tracker.values, [.2] * 29)
        self.assertEqual(tracker.status()['control_index'], 2)
        self.assertTrue(tracker.status()['valid'])

    def test_repeated_packet_and_headless_ros_time_never_refresh_validity(self):
        tracker = SonicFeedback(max_age=.05)
        for index in range(3): tracker.feed(message(index))
        stamp = tracker.observed_at
        for _ in range(4): self.assertFalse(tracker.feed(message(2)))
        self.assertEqual(tracker.observed_at, stamp)
        time.sleep(.07)
        self.assertFalse(tracker.status()['valid'])
        self.assertEqual(tracker.status()['duplicates'], 4)

    def test_reorder_regression_malformed_values_and_wrong_source_fail_closed(self):
        for patch in [{'index': True}, {'index': -1}, {'index': 1.1}, {'body_q_measured': [0.] * 28},
                      {'body_q_measured': [float('nan')] * 29}, {'last_action': [float('inf')] * 29},
                      {'control_loop_type': 'fake'}, {'ros_timestamp': time.time() - 10}]:
            tracker = SonicFeedback()
            for index in range(3): tracker.feed(message(index))
            self.assertFalse(tracker.feed({**message(3), **patch}))
            self.assertFalse(tracker.status()['valid'], patch)
        tracker = SonicFeedback()
        for index in (8, 9, 10): tracker.feed(message(index))
        self.assertFalse(tracker.feed(message(0)))
        self.assertFalse(tracker.status()['valid'])
        self.assertEqual(tracker.last_index, 10)

    def test_constant_configuration_heartbeat_does_not_invent_control_feedback(self):
        tracker = SonicFeedback()
        for _ in range(4): tracker.configuration({'control_frequency': 50})
        self.assertFalse(tracker.status()['valid'])
        self.assertIsNone(tracker.status()['control_index'])
        self.assertIsNotNone(tracker.status()['configuration_age_seconds'])


class MemorySupervisor:
    def __init__(self): self.children = {}
    def running(self, name): return name in self.children
    def record(self, name): return self.children.get(name, {})
    def start(self, name, argv, cwd):
        self.children[name] = {'pid': 12345, 'start_ticks': 'fixture', 'argv': argv, 'started_at': now()}
        return self.children[name]
    def logs(self, name): return 'fixture log'


class Driver:
    def __init__(self, root):
        self.root, self.app_root = Path(root), APP
        self.supervisor = MemorySupervisor()
        self.settings = {mode: default_config(mode) for mode in ('sim', 'real')}
    def config(self, mode): return copy.deepcopy(self.settings[mode])


class ControllerManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.driver = Driver(self.temp.name)
        self.directory = self.driver.root / 'runtime'
        self.control = SonicControl(self.driver, self.directory, PROFILE)
    def tearDown(self): self.temp.cleanup()
    def prepare_environment(self):
        python = self.driver.root / '.venv_teleop/bin/python'; python.parent.mkdir(parents=True); python.touch()
        manager = self.driver.root / 'gear_sonic/scripts/pico_manager_thread_server.py'; manager.parent.mkdir(parents=True)
        manager.write_text('# Robot Station: optional private manager uplink.\n')

    def test_simulation_is_hard_bound_to_loopback_and_domain_zero(self):
        config = connection(self.driver, 'sim')
        argv = controller_argv(config, 'sim')
        self.assertEqual(argv[:2], [BINARY, 'lo'])
        self.assertIn('--disable-crc-check', argv)
        self.assertNotIn('--disable-crc-check', controller_argv(self.driver.config('real'), 'real'))
        for patch in [{'interface': 'eno1'}, {'dds_domain': 99}, {'pose_endpoint': 'tcp://192.168.123.164:5556'},
                      {'state_endpoint': 'tcp://127.0.0.1:15556'}]:
            self.driver.settings['sim'] = {**default_config('sim'), **patch}
            with self.assertRaises(ConsoleError): connection(self.driver, 'sim')

    def test_real_start_cannot_be_enabled_by_http_boolean_or_manual_approval(self):
        self.prepare_environment()
        self.assertFalse(self.control.gate('real')['ready'])
        with self.assertRaises(ConsoleError) as error:
            self.control.start('real', {'service_id': 'controller', 'confirmed_real_start': True})
        self.assertEqual(error.exception.code, 'sonic_onsite_required')
        self.assertFalse(self.driver.supervisor.children)

    def test_explicit_start_has_one_durable_session_and_rejects_duplicates_or_unknown_args(self):
        self.prepare_environment()
        result = self.control.start('sim', {'service_id': 'controller'})
        self.assertEqual(result['state'], 'accepted')
        request = json.loads((self.control.directory / 'request.json').read_text())
        self.assertEqual(request['mode'], 'sim')
        self.assertEqual(request['connection']['interface'], 'lo')
        self.assertTrue(self.control.active())
        self.assertEqual(self.control.status('sim')['phase'], 'starting')
        self.assertFalse(self.control.status('sim')['feedback_valid'])
        for mode in ('sim', 'real'):
            with self.assertRaises(ConsoleError): self.control.start(mode, {'service_id': 'controller'})
        other = self.control.status('real')
        self.assertTrue(other['mode_conflict'])
        self.assertFalse(other['stop_allowed'])
        with self.assertRaises(ConsoleError): self.control.stop('real')
        self.driver.supervisor.children.clear()
        atomic_json(self.control.directory / 'status.json', {'run_id': request['run_id'], 'stop_confirmed': True})
        with self.assertRaises(ConsoleError): self.control.start('sim', {'service_id': 'controller', 'argv': ['bad']})

    def test_dead_worker_does_not_claim_container_process_was_stopped(self):
        self.prepare_environment(); self.control.start('sim', {'service_id': 'controller'})
        request = json.loads((self.control.directory / 'request.json').read_text())
        self.driver.supervisor.children.clear()
        atomic_json(self.control.directory / 'status.json', {'run_id': request['run_id'], 'container_id': 'immutable-id', 'phase': 'running', 'stop_confirmed': False})
        status = self.control.status('sim')
        self.assertTrue(self.control.active()); self.assertFalse(status['feedback_valid'])
        self.assertEqual(status['phase'], 'fault'); self.assertFalse(status['stop_confirmed'])
        self.assertFalse(status['start_allowed'])

    def test_log_components_are_allowlisted(self):
        for component in ('../../operation-key', '/etc/passwd', 'request.json'):
            with self.assertRaises(ConsoleError): self.control.logs('sim', component)


class GateTests(unittest.TestCase):
    def test_current_onsite_approval_is_boot_model_source_and_runtime_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); app = root / 'apps'; app.mkdir()
            for name in ('console_sonic.py', 'console_sonic_worker.py', 'sonic_container.py', 'sonic_feedback.py', 'sonic_commission.py'):
                (app / name).write_text('reviewed fixture')
            for name in FILES:
                path = root / 'gear_sonic_deploy' / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'fixture')
            manager = root / 'gear_sonic/scripts/pico_manager_thread_server.py'; manager.parent.mkdir(parents=True); manager.write_text('fixture')
            path = root / 'approval.json'; config = default_config('real'); stamp = time.time()
            document = {**template(config, PROFILE), **{flag: True for flag in FLAGS}, 'approved': True,
                        'mode_machine': 1, 'lowstate_source_guid': '5c4b43bc-3101-410b-b20b-3c3e698b0038',
                        'machine_fingerprint': 'host', 'boot_id': 'boot', 'sdk_fingerprint': 'sdk',
                        'approved_at_unix': stamp - 1, 'expires_at_unix': stamp + 60,
                        'runtime_fingerprint': runtime_fingerprint(root, app)}
            atomic_json(path, document); path.chmod(0o600)
            with mock.patch('sonic_commission.machine_fingerprint', return_value='host'), mock.patch('sonic_commission.boot_id', return_value='boot'), mock.patch('sonic_commission.sdk_fingerprint', return_value='sdk'):
                self.assertTrue(load_gate(path, root, app, config, PROFILE)['approved'])
                path.chmod(0o644)
                with self.assertRaises(ConsoleError): load_gate(path, root, app, config, PROFILE)
                path.chmod(0o600)
                for patch in [{'schema_version': 2}, {'approved': False}, {'expires_at_unix': stamp - .1}, {'boot_id': 'another-boot'}, {'normal_stop_verified': False}, {'model_hash': 'wrong'}]:
                    atomic_json(path, {**document, **patch}); path.chmod(0o600)
                    with self.assertRaises(ConsoleError): load_gate(path, root, app, config, PROFILE)
                atomic_json(path, document); path.chmod(0o600)
                (app / 'console_sonic_worker.py').write_text('changed worker')
                with self.assertRaises(ConsoleError): load_gate(path, root, app, config, PROFILE)


class ContainerInspectorTests(unittest.TestCase):
    def test_invalid_inspector_result_is_not_treated_as_exit_confirmation(self):
        with mock.patch('sonic_container.subprocess.run', return_value=mock.Mock(returncode=0, stdout='{}', stderr='')):
            with self.assertRaises(ConsoleError): inspect_controller('immutable-id')
        with mock.patch('sonic_container.subprocess.run', return_value=mock.Mock(returncode=1, stdout='', stderr='daemon unavailable')):
            with self.assertRaises(ConsoleError): inspect_controller('immutable-id')




class StreamDeadlineTests(unittest.TestCase):
    def session(self):
        from console_sonic_worker import Session
        session = Session.__new__(Session)
        session.manager_started_at = session.last_manager_packet = session.policy_start_at = None
        session.had_feedback = False
        return session

    def test_idle_wait_allowed_but_frozen_input_and_missing_first_feedback_stop(self):
        session = self.session()
        session.check_stream_deadlines()
        session.manager_started_at = time.monotonic() - 31
        with self.assertRaises(ConsoleError) as error: session.check_stream_deadlines()
        self.assertEqual(error.exception.code, 'sonic_input_lost')
        session.last_manager_packet = time.monotonic() - 2
        with self.assertRaises(ConsoleError): session.check_stream_deadlines()
        session.last_manager_packet = time.monotonic()
        session.policy_start_at = time.monotonic() - 6
        with self.assertRaises(ConsoleError) as error: session.check_stream_deadlines()
        self.assertEqual(error.exception.code, 'sonic_feedback_missing')
        session.had_feedback = True
        session.check_stream_deadlines()

    def test_official_command_start_sets_deadline_once(self):
        session = self.session()
        header = {'fields': [{'name': name, 'dtype': 'u8', 'shape': [1]} for name in ('start', 'stop', 'planner')]}
        message = b'command' + json.dumps(header).encode().ljust(1280, b'\0') + bytes([1, 0, 1])
        session.observe_input(message)
        self.assertIsNotNone(session.policy_start_at)
        stamp = session.policy_start_at
        session.observe_input(message)
        self.assertEqual(session.policy_start_at, stamp)

if __name__ == '__main__': unittest.main()
