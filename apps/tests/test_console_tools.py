"""Configuration/pose invariants and manual ownership; no real device IO."""
import copy
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from types import SimpleNamespace
import zipfile
from console_configuration import ConfigurationStore
from console_driver import SystemDriver
from console_manual import ManualControl
from console_poses import PoseStore, joint_targets, trajectory
from console_support import ConsoleError, atomic_json, now
APP=Path(__file__).resolve().parents[1]
PROFILE=APP/'static/assets/g1/profile.json'
if not PROFILE.is_file():PROFILE=APP.parent/'static/assets/g1/profile.json'
PROFILE=json.loads(PROFILE.read_text())

def zero():return [{'name':n,'position_rad':0.} for n in PROFILE['body_joints']]

class Stores(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.dir=Path(self.temp.name)
  self.driver=SystemDriver(self.dir,self.dir/'runtime',APP);self.store=ConfigurationStore(self.driver)
 def test_config_validation_conflict_and_restore(self):
  view=self.store.view();doc=view['document'];doc['real']['ros2_camera']['domain_id']=99
  first=self.store.write({'document':doc,'expected_revision':view['config_revision']})
  changed=copy.deepcopy(doc);changed['real']['ros2_camera']['domain_id']=100
  second=self.store.write({'document':changed,'expected_revision':first['config_revision']})
  self.assertEqual(self.driver.config('real')['ros2_camera']['domain_id'],100)
  with self.assertRaises(ConsoleError):self.store.write({'document':doc,'expected_revision':first['config_revision']})
  backup=next(p for p in second['backups'] if json.loads((self.store.directory/'backups'/(p['id']+'.json')).read_text())['document']==doc)
  self.store.write({'action':'restore','id':backup['id'],'expected_revision':second['config_revision']})
  self.assertEqual(self.driver.config('real')['ros2_camera']['domain_id'],99)
 def test_profiles_do_not_apply_and_busy_rejects_writes(self):
  view=self.store.view();doc=view['document'];doc['real']['dds_domain']=2
  self.store.write({'action':'save_profile','name':'Lab','document':doc,'expected_revision':view['config_revision']})
  self.assertEqual(self.driver.config('real')['dds_domain'],0)
  with self.assertRaises(ConsoleError):self.store.write({'document':doc,'expected_revision':view['config_revision']},busy=True)
  doc['real']['enable_real_motion']=True
  with self.assertRaises(ConsoleError):self.store.validate(doc)
 def test_invalid_endpoint_topic_qos_and_domain(self):
  for mutate in [lambda d:d['real'].update(camera_endpoint='tcp://8.8.8.8:5555'),lambda d:d['real']['ros2_camera'].update(domain_id=True),lambda d:d['real']['ros2_camera']['topics']['head'].update(reliability='any'),lambda d:d['real']['ros2_camera']['topics']['head'].update(topic='/bad;command')]:
   doc=self.store.document();mutate(doc)
   with self.assertRaises(ConsoleError):self.store.validate(doc)
 def test_pose_model_names_units_limits_and_roundtrip(self):
  poses=PoseStore(self.dir,PROFILE);saved=poses.save({'name':'Ready','joints':zero()})['pose']
  self.assertEqual(PoseStore(self.dir,PROFILE).list()['poses'][0],saved)
  for change in [{'model_hash':'other'},{'unit':'degree'},{'joints':zero()[:-1]},{'joints':[zero()[0]]*29}]:
   with self.assertRaises(ConsoleError):poses.save({'name':'invalid','joints':zero(),**change})
  invalid=zero();invalid[0]['position_rad']=100
  with self.assertRaises(ConsoleError):joint_targets(PROFILE,invalid)
  with self.assertRaises(ConsoleError):poses.save({**saved,'expected_revision':0})
  poses.save({'action':'archive','id':saved['id'],'expected_revision':1});self.assertEqual(poses.list()['poses'],[])
  self.assertTrue((poses.directory/(saved['id']+'.json')).exists())
 def test_trajectory_named_order_endpoints_and_speed(self):
  start=zero();target=zero();target[PROFILE['body_joints'].index('left_elbow_joint')]['position_rad']=1
  t=trajectory(PROFILE,start,list(reversed(target)),.25,.2)
  self.assertGreater(t['duration_seconds'],9)
  self.assertEqual(t['frames'][0]['positions_rad'],[0.]*29)
  self.assertEqual(t['frames'][-1]['positions_rad'],[r['position_rad'] for r in target])
  for a,b in zip(t['frames'],t['frames'][1:]):self.assertLessEqual(max(abs(x-y)/(b['time_s']-a['time_s']) for x,y in zip(a['positions_rad'],b['positions_rad'])),.20001)
 def test_manual_real_output_always_gated_and_server_restart_revokes(self):
  manual=ManualControl(self.driver,self.dir,PROFILE)
  with self.assertRaises(ConsoleError) as ctx:manual.command('real','initialize',{})
  self.assertEqual(ctx.exception.code,'onsite_validation_required')
  atomic_json(manual.directory/'command.json',{'lease_deadline':time.monotonic()+100})
  ManualControl(self.driver,self.dir,PROFILE)
  self.assertEqual(json.loads((manual.directory/'command.json').read_text()),{})
 def test_manual_lease_ownership_sequence_and_unit(self):
  manual=ManualControl(self.driver,self.dir,PROFILE)
  manual.status=lambda:{'state':'running','owner':'manual' if manual.token and time.monotonic()<manual.expires else None,'joints':zero()}
  claim=manual.command('sim','claim',{'owner':'manual'});token=claim['lease_token']
  with self.assertRaises(ConsoleError):manual.command('sim','claim',{'owner':'manual'})
  with self.assertRaises(ConsoleError):manual.command('sim','heartbeat',{'lease_token':'wrong'})
  request={'lease_token':token,'sequence':1,'unit':'rad','joints':zero()}
  self.assertEqual(manual.command('sim','apply_pose',request)['target_state'],'sent')
  with self.assertRaises(ConsoleError):manual.command('sim','apply_pose',request)
  with self.assertRaises(ConsoleError):manual.command('sim','apply_pose',{**request,'sequence':2,'unit':'degree'})
  manual.expires=time.monotonic()-1
  with self.assertRaises(ConsoleError):manual.command('sim','heartbeat',{'lease_token':token})
  self.assertIsNone(manual.status()['owner'])
 def test_diagnostic_bundle_has_no_access_secrets_or_logs(self):
  from console_diagnostics import Diagnostics
  snap={'robot':{'connected':False,'secret':'DO_NOT_EXPORT'},'battery':{},'camera_source':{},'cameras':[],'checks':[],'access':{'csrf_token':'DO_NOT_EXPORT'},'manual':{'lease_token':'DO_NOT_EXPORT'}}
  runtime=SimpleNamespace(driver=self.driver,directory=self.dir,snapshot=lambda mode:{'snapshot':snap})
  bundle=Diagnostics(runtime).bundle('real')
  with zipfile.ZipFile(io.BytesIO(bundle)) as z:
   content=z.read('diagnostics.json').decode();self.assertNotIn('DO_NOT_EXPORT',content);self.assertEqual(len(z.namelist()),2)

if __name__=='__main__':unittest.main()
