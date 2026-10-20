"""Real official exporter + HTTP + three MP4s on ephemeral loopback publishers.

All output stays in /tmp; no physical DDS, PICO or production outputs are used.
"""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
import os
from urllib.request import Request,urlopen
from http.server import ThreadingHTTPServer

from collection_workspace import CollectionWorkspace
from console_driver import SystemDriver,default_config
from console_runtime import ConsoleRuntime
from console_support import atomic_json,now,read_json
from console_timeseries import TimeseriesService
from dataset_conversion import ConversionManager
from sonic_adapter import SonicAdapter
from server import DataPlatformHandler

APP=Path(__file__).resolve().parents[1]
PROFILE=APP/"static/assets/g1/profile.json"
AVAILABLE=all(importlib.util.find_spec(k) for k in ["lerobot","zmq","cv2","msgpack","pyarrow","av"])

class QuietHandler(DataPlatformHandler):
    def log_message(self,*args):pass


class ProtocolFixture:
    def __init__(self,probe,camera_endpoint=None):
        self.probe=probe
        self.external_camera_endpoint=camera_endpoint
        self.stop=threading.Event()
        self.emit=True
        self.started=threading.Event()
        self.error=None
        self.thread=threading.Thread(target=self.run,daemon=True)
        self.thread.start()
        if not self.started.wait(10):raise RuntimeError("fixture initialization timeout")
        if self.error:raise self.error

    @staticmethod
    def packed(topic,values):
        header={"v":1,"endian":"le","fields":[{"name":name,"dtype":"i64" if value.dtype.kind=="i" else "f32","shape":list(value.shape)} for name,value in values.items()]}
        text=json.dumps(header).encode()
        assert len(text)<1280
        return topic+text.ljust(1280,b'\0')+b''.join(v.tobytes() for v in values.values())

    def run(self):
        try:
            import cv2,msgpack,numpy as np,zmq
            self.context=zmq.Context()
            pubs=[self.context.socket(zmq.PUB) for _ in range(3)]
            endpoints=[]
            for pub in pubs:
                pub.setsockopt(zmq.LINGER,0)
                endpoints.append('tcp://127.0.0.1:'+str(pub.bind_to_random_port('tcp://127.0.0.1')))
            self.state_endpoint,self.pose_endpoint,self.camera_endpoint=endpoints
            if self.external_camera_endpoint:self.camera_endpoint=self.external_camera_endpoint
            images={}
            for key,channel in [('ego_view',0),('left_wrist',1),('right_wrist',2)]:
                frame=np.zeros((480,640,3),np.uint8)
                frame[:,:,channel]=180
                ok,jpeg=cv2.imencode('.jpg',frame)
                assert ok
                images[key]=jpeg.tobytes()
            self.started.set()
            index=0
            while not self.stop.wait(.02):
                stamp=now()
                atomic_json(self.probe,{"heartbeat_at":stamp,"pico":{"body_ready":True,"observed_at":stamp}})
                if not self.emit:continue
                index+=1
                state={"control_index":index,"ros_timestamp":time.time(),"body_q":[index/10000]*29,"body_dq":[0.]*29,
                    "left_hand_q":[0.]*7,"right_hand_q":[0.]*7,"last_action":[index/20000]*29,
                    "last_left_hand_action":[0.]*7,"last_right_hand_action":[0.]*7,"base_quat":[1.,0.,0.,0.]}
                pubs[0].send(b'robot_config'+msgpack.packb({"test_fixture":True,"control_frequency":50.},use_bin_type=True))
                pubs[0].send(b'g1_debug'+msgpack.packb(state,use_bin_type=True))
                pose={"smpl_joints":np.zeros((1,24,3),np.float32),"smpl_pose":np.zeros((1,21,3),np.float32),
                    "body_quat_w":np.array([[1.,0.,0.,0.]],np.float32),"frame_index":np.array([index],np.int64)}
                pubs[1].send(self.packed(b'pose',pose))
                pubs[1].send(self.packed(b'manager_state',{"stream_mode":np.array([1],np.int64)}))
                message={"timestamps":{k:time.time() for k in ['ego_view','left_wrist','right_wrist']},
                    "images":images}
                if not self.external_camera_endpoint:pubs[2].send(msgpack.packb(message,use_bin_type=True))
            for pub in pubs:pub.close()
            self.context.term()
        except Exception as exc:self.error=exc;self.started.set()

    def close(self):self.stop.set();self.thread.join(timeout=5)


class FixtureDriver(SystemDriver):
    def __init__(self,root,directory,fixture,names):
        super().__init__(root,directory,APP)
        self.fixture,self.names=fixture,names

    def config(self,mode):
        return {**default_config(mode),"pico_calibration_confirmed":True,"state_endpoint":self.fixture.state_endpoint,
                "pose_endpoint":self.fixture.pose_endpoint,"camera_endpoint":self.fixture.camera_endpoint,"source_max_age_seconds":.7}

    def inspect(self,force=False):return {"checks":[],"container":{"state":"ready"},"observed_at":now()}
    def port(self,port):return True
    def telemetry(self,mode):
        stamp=now()
        return {"robot":{"observed_at":stamp,"source":"isolated fixture","joints":[{"name":n,"position_rad":0.} for n in self.names]},
            "controller":{"observed_at":stamp},"pico":{"body_ready":True,"observed_at":stamp},
            "cameras":{k:{"state":"streaming","observed_at":stamp} for k in ['head','left_wrist','right_wrist']}}


@unittest.skipUnless(AVAILABLE and PROFILE.is_file(),"Run with apps/.venv_collection after installation")
class CollectionPipelineTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='robot-station-pipeline-'))
        self.repo=self.root/'sonic';(self.repo/'outputs').mkdir(parents=True)
        self.runtime_dir=self.root/'runtime'
        self.probe=self.runtime_dir/'console/telemetry/sim/status.json'
        self.fixture=ProtocolFixture(self.probe)
        self.addCleanup(self.fixture.close)
        names=json.loads(PROFILE.read_text())["body_joints"]
        adapter=SimpleNamespace(repo_root=self.repo,runtime_dir=self.runtime_dir,session_running=lambda:False,
            _read_json=SonicAdapter._read_json,_read_jsonl=SonicAdapter._read_jsonl)
        self.workspace=CollectionWorkspace(adapter)
        self.driver=FixtureDriver(self.repo,self.runtime_dir/'console',self.fixture,names)
        self.runtime=ConsoleRuntime(adapter,self.workspace,self.driver)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
        self.server.console_runtime=self.runtime
        self.server.workspace=self.workspace
        self.server.timeseries_service=TimeseriesService(self.workspace,self.runtime_dir,python=APP/'.venv_conversion/bin/python')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
        self.sequence=0
        self.restarted_server=None
        self.payload={"dataset":"fixture_session","task":"isolated pipeline validation","fps":5,"camera_ids":["head","left_wrist","right_wrist"]}

    def tearDown(self):
        record=read_json(self.runtime.recorder.pointer)
        if record:
            try:self.driver.supervisor.stop('record-'+record['session_id'])
            except Exception:pass
        if self.restarted_server is not None:
            self.restarted_server.terminate()
            self.restarted_server.wait(timeout=5)
        self.server.shutdown();self.server.server_close();self.thread.join();self.runtime.close()

    def restart_in_new_process(self):
        """Reattach using a new PID, new SystemDriver and an empty Popen registry."""
        self.runtime.close()
        ready=self.root/'replacement-web.json'
        code='''import json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from server import create_server
server=create_server('127.0.0.1',0,Path(sys.argv[2]),Path(sys.argv[3]))
Path(sys.argv[4]).write_text(json.dumps({'port':server.server_port,'pid':os.getpid()}))
server.serve_forever()
'''
        with (self.root/'replacement-web.log').open('ab') as log:
            self.restarted_server=subprocess.Popen([sys.executable,'-u','-c',code,str(APP),str(self.repo),str(self.runtime_dir),str(ready)],stdout=log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and not read_json(ready):
            if self.restarted_server.poll() is not None:self.fail((self.root/'replacement-web.log').read_text())
            time.sleep(.05)
        info=read_json(ready)
        self.assertNotEqual(info['pid'],os.getpid())
        self.base=f"http://127.0.0.1:{info['port']}"

    def snapshot(self):
        with urlopen(self.base+'/api/v1/console/snapshot?mode=sim&profile_id=unitree-g1-29',timeout=5) as r:return json.load(r)['snapshot']

    def command(self,action,payload=None):
        snapshot=self.snapshot();self.sequence+=1
        body={"action":action,"mode":"sim","profile_id":"unitree-g1-29","expected_revision":snapshot['revision'],"payload":payload or {}}
        request=Request(self.base+'/api/v1/console/collection/commands',json.dumps(body).encode(),
            {'Content-Type':'application/json','Idempotency-Key':f'pipeline-{self.sequence}'})
        with urlopen(request,timeout=10) as r:return json.load(r)

    def wait(self,predicate,seconds=40):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            data=self.snapshot()['collection']
            if predicate(data):return data
            if data.get('state')=='failed':self.fail(str(data)+'\n'+self.runtime.recorder.logs())
            time.sleep(.15)
        self.fail('timeout: '+str(data)+'\n'+self.runtime.recorder.logs())

    def test_http_record_save_discard_recovery_playback_and_hdf5(self):
        self.command('prepare',self.payload)
        self.wait(lambda d:d.get('prepared') and not d.get('busy'))
        self.command('start',self.payload)
        self.wait(lambda d:d.get('frames',0)>=5)
        self.command('save')
        self.wait(lambda d:d.get('state')=='ready' and not d.get('busy'))
        self.command('start',self.payload)
        before=self.wait(lambda d:d.get('frames',0)>=3)
        session=before['session_id']
        worker_before=self.driver.supervisor.record('record-'+session)['pid']
        self.restart_in_new_process()
        recovered=self.wait(lambda d:d.get('frames',0)>=before['frames']+2)
        self.assertTrue(recovered['recording'])
        self.assertEqual(recovered['session_id'],session)
        self.assertEqual(self.driver.supervisor.record('record-'+session)['pid'],worker_before)
        self.command('discard')
        self.wait(lambda d:d.get('state')=='ready' and not d.get('busy'))
        self.command('end')
        self.wait(lambda d:d.get('state')=='ended' and not d.get('busy'))
        source=self.repo/'outputs/fixture_session'
        info=read_json(source/'meta/info.json')
        self.assertEqual(info['total_episodes'],2)
        self.assertEqual(info['discarded_episode_indices'],[1])
        self.assertEqual(len(info['features']['observation.state']['names']),43)
        groups=self.workspace.groups()
        self.assertEqual(groups[0]['retained'],1)
        for episode in [0,1]:
            review=self.workspace.review('fixture_session',episode)
            self.assertEqual(len(review['videos']),3)
            for item in review['videos']:
                video=self.workspace.video('fixture_session',episode,item['camera'])
                result=subprocess.run(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','json',str(video)],capture_output=True,text=True,check=True)
                self.assertEqual(int(json.loads(result.stdout)['streams'][0]['nb_read_frames']),review['episode']['frames'])
                rgb=subprocess.run(['ffmpeg','-v','error','-i',str(video),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
                import numpy as np
                mean=np.frombuffer(rgb,dtype=np.uint8).reshape(480,640,3).mean(axis=(0,1))
                expected_channel=1 if 'left' in item['camera'] else 0 if 'right' in item['camera'] else 2
                self.assertEqual(int(mean.argmax()),expected_channel)
                self.assertGreater(float(mean.max()),120)
        with urlopen(self.base+'/api/v1/console/episodes/timeseries?dataset=fixture_session&episode=0',timeout=30) as r:
            series=json.load(r)
        self.assertEqual(len(series['joint_names']),43)
        self.assertEqual(series['frames'][0]['time_s'],0.)
        self.assertEqual(len(series['frames']),self.workspace.review('fixture_session',0)['episode']['frames'])
        manager=ConversionManager(self.repo/'outputs',self.runtime_dir)
        inspection=manager.inspect('fixture_session')['inspection']
        self.assertTrue(inspection['can_convert'],inspection['errors'])
        result=manager.create({'dataset':'fixture_session','format':'hdf5','output_name':'fixture_hdf5','fingerprint':inspection['fingerprint']})
        deadline=time.monotonic()+40
        while time.monotonic()<deadline:
            job=manager.job(result['job']['id'])['job']
            if job['state'] in {'succeeded','failed','cancelled'}:break
            time.sleep(.2)
        self.assertEqual(job['state'],'succeeded',job)
        self.assertTrue((self.repo/'outputs/conversions/fixture_hdf5/episodes/episode_000000.hdf5').is_file())
        print('PIPELINE_FIXTURE',self.root,flush=True)

    def test_source_freeze_preserves_current_episode_as_discarded(self):
        self.command('prepare',self.payload)
        self.wait(lambda d:d.get('prepared') and not d.get('busy'))
        self.command('start',self.payload)
        self.wait(lambda d:d.get('frames',0)>=4)
        self.fixture.emit=False
        result=self.wait(lambda d:d.get('state')=='failed')
        self.assertIn('数据源中断',result['message'])
        info=read_json(self.repo/'outputs/fixture_session/meta/info.json')
        self.assertEqual(info['total_episodes'],1)
        self.assertEqual(info['discarded_episode_indices'],[0])
        self.assertGreater(info['total_frames'],0)
        self.assertTrue((self.repo/'outputs/fixture_session/.incomplete').exists())
        self.assertFalse(self.runtime.recorder.active())

    def test_software_stop_works_across_selected_modes_and_keeps_data(self):
        self.command('prepare',self.payload)
        self.wait(lambda d:d.get('prepared') and not d.get('busy'))
        self.command('start',self.payload)
        self.wait(lambda d:d.get('frames',0)>=3)
        body={'action':'stop','mode':'real','profile_id':'unitree-g1-29','expected_revision':None,'payload':{}}
        request=Request(self.base+'/api/v1/console/safety/stop',json.dumps(body).encode(),
            {'Content-Type':'application/json','Idempotency-Key':'stop-cross-mode'})
        with urlopen(request,timeout=10) as response:result=json.load(response)
        self.assertFalse(result['motion_stop_supported'])
        self.wait(lambda d:d.get('state')=='ended' and not d.get('busy'))
        info=read_json(self.repo/'outputs/fixture_session/meta/info.json')
        self.assertEqual(info['discarded_episode_indices'],[0])
        self.assertEqual(info['total_episodes'],1)
        self.assertFalse(self.runtime.recorder.active())


class Ros2CollectionPipelineTests(unittest.TestCase):
    def test_ros2_to_official_exporter_three_videos_playback_hdf5_and_web_recovery(self):
        # Reuse the verified official-exporter scenario, replacing only its camera source.
        from unittest import mock
        from ros2_camera_test_support import Ros2CameraFixture
        original=ProtocolFixture
        # Mixed raw/compressed encodings are checked by ros2_camera_checks. Use
        # camera-native JPEG here so exporter/FK startup load cannot exhaust the
        # host DDS best-effort fragment buffers for three uncompressed streams.
        with Ros2CameraFixture(APP,compressed=True) as camera:
            camera.wait(lambda:camera.status().get('state')=='streaming')
            factory=lambda probe:original(probe,camera_endpoint=camera.endpoint)
            with mock.patch.object(sys.modules[__name__],'ProtocolFixture',side_effect=factory):
                case=CollectionPipelineTests('test_http_record_save_discard_recovery_playback_and_hdf5')
                try:
                    case.setUp()
                    case.test_http_record_save_discard_recovery_playback_and_hdf5()
                finally:
                    if hasattr(case,'runtime'):case.tearDown()
                    case.doCleanups()


if __name__=='__main__':unittest.main()
