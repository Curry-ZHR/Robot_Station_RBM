"""Run explicitly in the isolated ROS venv, after sourcing Humble."""
import json
from pathlib import Path
import time
import unittest

from console_probe_worker import PassiveProbe
from console_driver import default_config
from ros2_camera_test_support import Ros2CameraFixture

APP = Path(__file__).resolve().parents[1]


class Ros2WireTests(unittest.TestCase):
    def test_real_ros_raw_compressed_color_freeze_recovery_and_passive_preview(self):
        import cv2,numpy as np,msgpack,zmq,threading
        with Ros2CameraFixture(APP) as fixture:
            context=zmq.Context();sub=context.socket(zmq.SUB);sub.setsockopt(zmq.SUBSCRIBE,b'');sub.setsockopt(zmq.LINGER,0);sub.connect(fixture.endpoint)
            try:
                fixture.wait(lambda: fixture.status().get('state')=='streaming' and fixture.status().get('packets',0)>2)
                packet=None;deadline=time.monotonic()+8
                while time.monotonic()<deadline:
                    if sub.poll(100):
                        packet=msgpack.unpackb(sub.recv(),raw=False)
                        if len(packet['images'])==3:break
                self.assertEqual(set(packet['images']),{'ego_view','left_wrist','right_wrist'})
                for key,value in packet['images'].items():
                    frame=cv2.imdecode(np.frombuffer(value,np.uint8),cv2.IMREAD_COLOR)
                    self.assertEqual(frame.shape,(480,640,3));self.assertEqual(int(frame.mean(axis=(0,1)).argmax()),{'ego_view':0,'left_wrist':1,'right_wrist':2}[key])
                (fixture.root/'preview').mkdir()
                probe=PassiveProbe(APP,fixture.root/'preview',{**default_config('sim'),'camera_endpoint':fixture.endpoint},'sim')
                thread=threading.Thread(target=probe.run_cameras,daemon=True);thread.start()
                try:
                    fixture.wait(lambda:len(probe.data['cameras'])==3)
                    self.assertTrue(all((fixture.root/'preview'/(name+'.jpg')).exists() for name in ['head','left_wrist','right_wrist']))
                    fixture.control(frozen=['left_wrist'])
                    fixture.wait(lambda:not fixture.status()['views']['left_wrist']['live'])
                    self.assertTrue(fixture.status()['views']['head']['live'])
                    self.assertGreater(fixture.status()['views']['left_wrist']['rejected'],0)
                    fixture.control()
                    fixture.wait(lambda:fixture.status()['state']=='streaming')
                    fixture.control(disable=True)
                    fixture.wait(lambda:not any(v['live'] for v in fixture.status()['views'].values()))
                    fixture.control()
                    fixture.wait(lambda:fixture.status()['state']=='streaming')
                finally:probe.stop.set();thread.join(timeout=3)
            finally:sub.close();context.term()

    def test_domain_100_publisher_is_invisible_to_domain_99_bridge(self):
        with Ros2CameraFixture(APP,publisher_domain=100) as fixture:
            time.sleep(1.2)
            self.assertEqual(fixture.status()['packets'],0)
            fixture.start_publisher(99)
            fixture.wait(lambda:fixture.status()['state']=='streaming')
            self.assertEqual(fixture.status()['domain_id'],99)

    def test_managed_start_port_conflict_reuse_stop_and_restart(self):
        import tempfile
        from console_driver import SystemDriver
        from console_support import ConsoleError, atomic_json
        with Ros2CameraFixture(APP) as fixture, tempfile.TemporaryDirectory() as tmp:
            driver=SystemDriver(Path(tmp)/'sonic',Path(tmp)/'runtime',APP)
            patch={'camera_source':'ros2','ros2_camera':fixture.config['ros2_camera'],'camera_endpoint':fixture.endpoint}
            atomic_json(driver.config_path,{'real':patch,'sim':patch})
            try:
                with self.assertRaises(ConsoleError):driver.start_camera_source('sim')
                fixture.bridge.terminate();fixture.bridge.wait(timeout=5)
                started=driver.start_camera_source('sim')
                again=driver.start_camera_source('real')
                self.assertTrue(again['reused']);self.assertEqual(started['pid'],again['pid'])
                driver.stop_camera_source()
                self.assertEqual(driver.camera_source_status('sim')['state'],'stopped')
                replacement=driver.start_camera_source('sim')
                self.assertNotEqual(started['pid'],replacement['pid'])
            finally:driver.stop_camera_source()


if __name__=='__main__':unittest.main()
