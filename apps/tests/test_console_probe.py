import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest import mock

from console_driver import SystemDriver,default_config
from console_probe_worker import PassiveProbe,MOTOR_NAMES
from console_support import ConsoleError,ProcessSupervisor,atomic_json


class ProcessAndConfigTests(unittest.TestCase):
    def test_supervisor_reuses_owned_child_and_refuses_reused_pid_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            supervisor=ProcessSupervisor(Path(tmp))
            child=supervisor.start('owned',[sys.executable,'-c','import time;time.sleep(20)'],tmp)
            try:
                again=supervisor.start('owned',[sys.executable,'-c','raise RuntimeError()'],tmp)
                self.assertTrue(again['reused'])
                self.assertEqual(child['pid'],again['pid'])
                bad={**supervisor.record('owned'),'start_ticks':'wrong'}
                atomic_json(Path(tmp)/'foreign.json',bad)
                self.assertFalse(supervisor.stop('foreign'))
                self.assertTrue(supervisor.running('owned'))
                supervisor.stop('owned')
                self.assertFalse(supervisor.running('owned'))
            finally:
                if supervisor.running('owned'):supervisor.stop('owned')

    def test_config_requires_local_endpoints_distinct_camera_keys_and_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            driver=SystemDriver(Path(tmp),Path(tmp)/'runtime')
            for patch in [{'state_endpoint':'tcp://remote:5557'},{'pico_calibration_confirmed':'yes'},
                {'camera_keys':{'head':'same','left_wrist':'same','right_wrist':'same'}},{'source_max_age_seconds':float('nan')}]:
                # Plain json.dump permits NaN so configuration validation gets the invalid number.
                import json
                driver.config_path.write_text(json.dumps({'sim':patch}))
                with self.assertRaises(ConsoleError):driver.config('sim')


@unittest.skipUnless(all(importlib.util.find_spec(k) for k in ['zmq','cv2','msgpack_numpy']),'Use SONIC teleop environment')
class CameraProbeTests(unittest.TestCase):
    def test_body_clock_freeze_is_not_hidden_by_live_headset_clock(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as tmp:
            probe=PassiveProbe(Path(tmp),Path(tmp),default_config('sim'),'sim')
            poses=np.zeros((24,7));poses[:,6]=1
            counter=[0]
            def body_stamp():counter[0]+=1;return min(counter[0],3)
            sdk=SimpleNamespace(init=lambda:None,is_body_data_available=lambda:True,get_body_timestamp_ns=body_stamp,
                get_time_stamp_ns=lambda:time.time_ns(),get_body_joints_pose=lambda:poses)
            connection=mock.MagicMock()
            with mock.patch.dict(sys.modules,{'xrobotoolkit_sdk':sdk}),mock.patch('console_probe_worker.socket.create_connection',return_value=connection):
                thread=threading.Thread(target=probe.run_pico,daemon=True);thread.start()
                try:
                    deadline=time.monotonic()+3
                    while probe.data['pico'].get('body_timestamp_ns')!=3 and time.monotonic()<deadline:time.sleep(.05)
                    self.assertTrue(probe.data['pico'].get('body_ready'),probe.data['errors'])
                    observed=probe.data['pico']['observed_at']
                    time.sleep(.35)
                    self.assertEqual(probe.data['pico']['observed_at'],observed)
                    self.assertGreater(counter[0],3)
                finally:probe.stop.set();thread.join(timeout=2)

    def test_real_zmq_jpeg_decode_all_three_views_and_frozen_timestamp(self):
        import cv2,msgpack,numpy as np,zmq
        with tempfile.TemporaryDirectory() as tmp:
            context=zmq.Context();publisher=context.socket(zmq.PUB);publisher.setsockopt(zmq.LINGER,0)
            port=publisher.bind_to_random_port('tcp://127.0.0.1')
            config={**default_config('sim'),'camera_endpoint':f'tcp://127.0.0.1:{port}'}
            probe=PassiveProbe(Path(tmp),Path(tmp),config,'sim')
            thread=threading.Thread(target=probe.run_cameras,daemon=True);thread.start()
            ok,jpeg=cv2.imencode('.jpg',np.ones((16,16,3),np.uint8)*120);self.assertTrue(ok)
            def send(stamp):publisher.send(msgpack.packb({'timestamps':{key:stamp for key in config['camera_keys'].values()},'images':{key:jpeg.tobytes() for key in config['camera_keys'].values()}},use_bin_type=True))
            try:
                deadline=time.monotonic()+8
                stamp=time.time()
                while len(probe.data['cameras'])<3 and time.monotonic()<deadline:
                    stamp=time.time();send(stamp);time.sleep(.05)
                self.assertEqual(set(probe.data['cameras']),{'head','left_wrist','right_wrist'},probe.data['errors'])
                before=probe.data['cameras']['head']['observed_at']
                for _ in range(5):send(stamp);time.sleep(.05)
                self.assertEqual(probe.data['cameras']['head']['observed_at'],before)
                for camera in config['camera_keys']:
                    image=cv2.imread(str(Path(tmp)/(camera+'.jpg')))
                    self.assertEqual(image.shape,(16,16,3))
            finally:
                probe.stop.set();thread.join(timeout=3);publisher.close();context.term()


if __name__=='__main__':unittest.main()
