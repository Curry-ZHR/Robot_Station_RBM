"""No robot IO. Protocol, trajectory, ownership gates and watchdog tests."""
import copy
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import zlib
from console_real_worker import RealControlLoop
from console_support import ConsoleError,atomic_json
from unitree_g1_control import Feedback,MOTOR_NAMES,QuinticPlan,digest,encode_lowcmd,load_commissioning,template,validate_parameters
APP=Path(__file__).resolve().parents[1];PROFILE=APP/'static/assets/g1/profile.json'
if not PROFILE.is_file():PROFILE=APP.parent/'static/assets/g1/profile.json'
PROFILE=json.loads(PROFILE.read_text())

def parameters():
    doc=template(PROFILE);doc.update(hardware_variant='g1-29-unlocked-waist',mode_machine=5)
    for row in doc['joints']:row['torque_limit_nm']=5
    doc['joints']=validate_parameters(doc,PROFILE);return doc

def factory():return NS(mode_pr=255,mode_machine=255,motor_cmd=[NS(mode=255,q=999.,dq=999.,tau=999.,kp=999.,kd=999.,reserve=9) for _ in range(35)],reserve=[9]*4,crc=0)
class CRC:
    def Crc(self,msg):
        if hasattr(msg,'motor_cmd'):rows=[[m.mode,m.q,m.dq,m.tau,m.kp,m.kd,m.reserve] for m in msg.motor_cmd];values=[msg.mode_pr,msg.mode_machine,rows,msg.reserve]
        else:values=[msg.mode_pr,msg.mode_machine,msg.tick,[[m.q,m.dq,m.tau_est,m.motorstate,list(m.temperature)] for m in msg.motor_state],msg.imu_state.rpy]
        return zlib.crc32(json.dumps(values).encode())
class Clock:
    def __init__(self):self.value=1.
    def __call__(self):return self.value
    def step(self,dt=.002):self.value+=dt
class Transport:
    def __init__(self,clock):
        self.clock=clock;self.factory=factory;self.crc=CRC();self.published=[];self.arms=0;self.disarmed=0;self.failure=None
        self.data={'positions':[.1]*29,'velocities':[0.]*29,'torques':[0.]*29,'temperatures':[25.]*29,'rpy':[0.]*3,'source_guid':'unique','feedback_age_seconds':0.}
    def observe(self,config):
        if self.failure:raise ConsoleError(self.failure)
        return copy.deepcopy(self.data)
    def arm(self):self.arms+=1
    def disarm(self):self.disarmed+=1
    def write(self,msg):
        self.published.append(msg)
        if msg.motor_cmd[0].kp>0:self.data['positions']=[m.q for m in msg.motor_cmd[:29]];self.data['velocities']=[m.dq for m in msg.motor_cmd[:29]]

class Protocol(unittest.TestCase):
    def test_mapping_is_hardware_order_not_urdf_order(self):
        self.assertEqual(len(set(MOTOR_NAMES)),29);self.assertEqual(MOTOR_NAMES[12:15],['waist_yaw_joint','waist_roll_joint','waist_pitch_joint']);self.assertEqual(MOTOR_NAMES[18],'left_elbow_joint');self.assertEqual(MOTOR_NAMES[28],'right_wrist_yaw_joint')
        self.assertEqual(set(MOTOR_NAMES),set(PROFILE['body_joints']))
    def test_reference_template_cannot_enable_output(self):
        row=template(PROFILE);self.assertFalse(row['approved']);self.assertEqual(row['hardware_variant'],'UNCONFIRMED')
        with self.assertRaises(ConsoleError):validate_parameters(row,PROFILE)
    def test_parameter_mapping_gain_limits_and_missing_torque(self):
        for mutate in [lambda d:d.update(hardware_variant='g1-23'),lambda d:d.update(mode_machine=True),lambda d:d['joints'][0].update(motor_index=1),lambda d:d['joints'][0].update(kp=1e6),lambda d:d['joints'][0].update(torque_limit_nm=None),lambda d:d['joints'][0].update(lower=-999),lambda d:d['joints'][0].update(max_velocity_rad_s=float('nan'))]:
            doc=parameters();mutate(doc)
            with self.assertRaises(ConsoleError):validate_parameters(doc,PROFILE)
    def test_fresh_hg_frames_crc_and_unused_slots(self):
        p=parameters();crc=CRC();q=[i*.001 for i in range(29)]
        msg=encode_lowcmd(factory,crc,q,[0.]*29,p['joints'],5,ramp=.5)
        self.assertEqual((msg.mode_pr,msg.mode_machine),(0,5));self.assertEqual(msg.crc,crc.Crc(msg))
        for i,m in enumerate(msg.motor_cmd):
            self.assertEqual(m.tau,0);self.assertEqual(m.reserve,0)
            if i<29:self.assertEqual(m.mode,1);self.assertEqual(m.q,q[i]);self.assertEqual(m.kp,p['joints'][i]['kp']*.5)
            else:self.assertEqual((m.mode,m.q,m.dq,m.kp,m.kd),(0,0.,0.,0.,0.))
        for kind in ('damping','disabled'):
            msg=encode_lowcmd(factory,crc,q,[0.]*29,p['joints'],5,kind)
            self.assertTrue(all(m.kp==0 for m in msg.motor_cmd));self.assertTrue(all(m.mode==0 for m in msg.motor_cmd) if kind=='disabled' else all(m.kd>0 for m in msg.motor_cmd[:29]))
    def test_encoder_rejects_nan_wrong_dimension_or_unbounded_target(self):
        p=parameters()
        for q in ([0.]*28,[float('nan')]*29,[100.]*29):
            with self.assertRaises(ConsoleError):encode_lowcmd(factory,CRC(),q,[0.]*29,p['joints'],5)
    def test_feedback_crc_tick_wrap_mode_fault_and_stale(self):
        p=parameters();clock=Clock();crc=CRC();feedback=Feedback(p['joints'],5,crc,clock)
        msg=NS(mode_pr=0,mode_machine=5,tick=0xffffffff,imu_state=NS(rpy=[0.]*3),motor_state=[NS(q=0.,dq=0.,tau_est=0.,motorstate=0,temperature=[25,25]) for _ in range(35)],crc=0)
        msg.crc=crc.Crc(msg);self.assertTrue(feedback.accept(msg));self.assertFalse(feedback.accept(msg))
        msg.tick=0;msg.crc=crc.Crc(msg);self.assertTrue(feedback.accept(msg));self.assertEqual(feedback.view(.1)['tick'],0)
        clock.step(.2)
        with self.assertRaises(ConsoleError):feedback.view(.1)
        for change in ('crc','mode','motor'):
            msg.tick+=1;msg.mode_machine=6 if change=='mode' else 5;msg.motor_state[0].motorstate=1 if change=='motor' else 0;msg.crc=crc.Crc(msg)+(1 if change=='crc' else 0)
            self.assertFalse(feedback.accept(msg))

class Plans(unittest.TestCase):
    def test_exact_extrema_velocity_acceleration_and_endpoints(self):
        rows=parameters()['joints'];plan=QuinticPlan([0.]*29,[0.]*29,[0.]*29,[.2]*29,rows,.25)
        self.assertGreater(plan.duration,1.8)
        self.assertEqual(plan.sample(0)[0],[0.]*29)
        self.assertTrue(all(abs(v-.2)<1e-10 for v in plan.sample(plan.duration)[0]))
        for i in range(301):
            q,v,a=plan.sample(plan.duration*i/300)
            self.assertLessEqual(max(map(abs,v)),.2000001);self.assertLessEqual(max(map(abs,a)),.500001)
    def test_live_replan_preserves_position_velocity_and_acceleration(self):
        rows=parameters()['joints'];a=QuinticPlan([0.]*29,[0.]*29,[0.]*29,[.2]*29,rows,3.)
        q,v,acc=a.sample(.8);b=QuinticPlan(q,v,acc,[.25]*29,rows,3.)
        for x,y in zip((q,v,acc),b.sample(0)):
            self.assertTrue(all(abs(i-j)<1e-10 for i,j in zip(x,y)))

class Watchdogs(unittest.TestCase):
    def setUp(self):self.clock=Clock();self.transport=Transport(self.clock);self.config=parameters();self.loop=RealControlLoop(self.transport,self.config,self.clock)
    def step(self,deadline=100):self.clock.step();return self.loop.step(deadline)
    def test_no_publisher_until_explicit_arm_and_no_automatic_zero(self):
        self.assertEqual(self.transport.arms,0);self.assertIsNone(self.loop.step(100));self.loop.arm('session');self.step()
        self.assertEqual(self.transport.arms,1);self.assertEqual([m.q for m in self.transport.published[0].motor_cmd[:29]],[.1]*29)
    def test_sequence_limits_and_real_tracking(self):
        self.loop.arm('session');self.loop.set_target([.2]*29,0,'first',3)
        with self.assertRaises(ConsoleError):self.loop.set_target([.2]*29,0,'duplicate',3)
        with self.assertRaises(ConsoleError):self.loop.set_target([2.]*29,1,'bad',3)
        for _ in range(1700):self.step()
        status=self.loop.status(self.transport.data);self.assertEqual(status['target_id'],'first');self.assertEqual(status['target_state'],'reached')
    def test_lease_expiry_damps_then_disables_and_cannot_rearm(self):
        self.loop.arm('session')
        for _ in range(620):self.step(1.02)
        self.assertEqual(self.loop.state,'stopped');self.assertTrue(self.loop.stop_acknowledged);self.assertTrue(all(m.mode==0 for m in self.transport.published[-1].motor_cmd));self.assertGreater(sum(m.motor_cmd[0].mode==0 for m in self.transport.published),1)
        with self.assertRaises(ConsoleError):self.loop.arm('other')
    def test_feedback_loss_foreign_owner_source_and_mode_conflicts_publish_nothing_further(self):
        for reason in ('feedback_stale','foreign_publisher','controller_conflict'):
            self.setUp();self.loop.arm('s');self.step();count=len(self.transport.published);self.transport.failure=reason;self.step();self.assertEqual(self.loop.state,'fault');self.assertEqual(len(self.transport.published),count)
        self.setUp();self.loop.arm('s');self.transport.data['source_guid']='other';self.step();self.assertEqual(self.loop.state,'fault')
    def test_control_deadline_temperature_tilt_and_torque_trip(self):
        for mutate in [lambda t:t.data['temperatures'].__setitem__(0,80),lambda t:t.data['rpy'].__setitem__(0,1.),lambda t:t.data['torques'].__setitem__(0,100)]:
            self.setUp();self.loop.arm('s');mutate(self.transport);self.step();self.assertEqual(self.loop.state,'fault');self.assertEqual(len(self.transport.published),0)
        self.setUp();self.loop.arm('s');self.clock.step(.05);self.loop.step(100);self.assertEqual(self.loop.state,'fault')
    def test_tracking_error_and_estimated_pd_torque_trip(self):
        self.loop.arm('s');self.transport.data['positions'][0]+=.3;self.step();self.assertEqual(self.loop.state,'fault')
        self.setUp();self.loop.arm('s');self.transport.data['velocities'][0]=10.;self.step();self.assertEqual(self.loop.state,'fault')

class Commissioning(unittest.TestCase):
    def test_approval_requires_attestation_and_observed_mode(self):
        from unitree_commission import approve_document
        doc=parameters()
        with self.assertRaises(ConsoleError):approve_document(doc,PROFILE,{'interface':'eno1','dds_domain':0},Path('/missing'),{'stationary':True,'mode_machine':5})
    def test_host_boot_version_expiry_permissions_and_output_gate(self):
        p=parameters();p.update(approved=True,physical_support_confirmed=True,hardware_mapping_verified=True,gains_validated=True,stop_tested=True,lowstate_source_guid='00112233-4455-6677-8899-aabbccddeeff',machine_fingerprint='host',boot_id='boot',sdk_fingerprint='sdk',control_fingerprint='control',approved_at_unix=time.time()-1,expires_at_unix=time.time()+100)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'commissioning.json';atomic_json(path,p);path.chmod(0o600)
            with patch('unitree_g1_control.machine_fingerprint',return_value='host'),patch('unitree_g1_control.boot_id',return_value='boot'),patch('unitree_g1_control.sdk_fingerprint',return_value='sdk'),patch('unitree_g1_control.control_fingerprint',return_value='control'):
                self.assertTrue(load_commissioning(path,PROFILE,{'interface':'eno1','dds_domain':0},folder)['approved'])
                for key,value in [('approved',False),('boot_id','different'),('sdk_fingerprint','different'),('expires_at_unix',0),('gains_validated',False)]:
                    atomic_json(path,{**p,key:value});path.chmod(0o600)
                    with self.assertRaises(ConsoleError):load_commissioning(path,PROFILE,{'interface':'eno1','dds_domain':0},folder)
                atomic_json(path,p);path.chmod(0o644)
                with self.assertRaises(ConsoleError):load_commissioning(path,PROFILE,{'interface':'eno1','dds_domain':0},folder)

if __name__=='__main__':unittest.main()

class RuntimeGate(unittest.TestCase):
    def test_real_snapshot_reports_gate_and_exposes_no_motion_without_commissioning(self):
        from test_console_runtime import RuntimeFixture
        fixture=RuntimeFixture();fixture.setUp()
        try:
            row=fixture.runtime.snapshot('real')['snapshot']
            self.assertFalse(row['manual']['gate']['ready']);self.assertIsNone(row['robot']['owner']);self.assertNotIn('robot.apply_pose',row['capabilities']['commands']);self.assertFalse(row['interlocks']['can_initialize'])
            report=fixture.runtime.real_manual.report();self.assertEqual(len(report['joints']),29);self.assertFalse(report['checks']['gains_validated']);self.assertEqual(report['protocol']['hardware_motor_slots'],35)
            with self.assertRaises(ConsoleError):fixture.runtime.manual_target({'mode':'real','action':'claim','owner':'manual','supported_operation_confirmed':True})
        finally:fixture.doCleanups()
    def test_no_web_config_can_set_real_approval(self):
        from console_configuration import ConfigurationStore
        from console_driver import SystemDriver
        with tempfile.TemporaryDirectory() as folder:
            driver=SystemDriver(Path(folder),Path(folder)/'runtime',APP);store=ConfigurationStore(driver);doc=store.document();doc['real']['approved']=True
            with self.assertRaises(ConsoleError):store.validate(doc)
