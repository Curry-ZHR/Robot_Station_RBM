"""Run explicitly with SONIC teleop Python; physical simulation, never DDS output."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from console_driver import SystemDriver
from console_manual import ManualControl
from console_manual_worker import Physics
from console_support import read_json
APP=Path(__file__).resolve().parents[1];SONIC=APP.parents[1]/'sonic_deploy'
PROFILE=json.loads((APP/'static/assets/g1/profile.json').read_text())
class PhysicsChecks(unittest.TestCase):
 def test_fixed_base_physics_actually_steps_and_tracks(self):
  p=Physics(SONIC/'gear_sonic_deploy/g1/g1_29dof.xml',PROFILE['body_joints'])
  self.assertEqual(p.model.nq,29);goal=p.positions();goal[p.names.index('left_elbow_joint')]=.5
  for _ in range(2500):p.step(goal)
  self.assertGreater(p.data.time,4.9);self.assertLess(float(max(abs(p.positions()-goal))),.03)
 def test_worker_lease_tracking_expiry_and_recovery(self):
  with tempfile.TemporaryDirectory() as folder:
   driver=SystemDriver(SONIC,Path(folder),APP);manual=ManualControl(driver,folder,PROFILE)
   try:
    manual.initialize('sim');claim=manual.command('sim','claim',{'owner':'manual'});token=claim['lease_token']
    rows=[{'name':n,'position_rad':0.} for n in PROFILE['body_joints']];rows[PROFILE['body_joints'].index('left_elbow_joint')]['position_rad']=.4
    result=manual.command('sim','apply_pose',{'lease_token':token,'sequence':1,'unit':'rad','joints':rows,'transition_seconds':1,'velocity_limit_rad_s':1})
    until=time.monotonic()+3
    while time.monotonic()<until:
     manual.command('sim','heartbeat',{'lease_token':token});status=manual.status()
     if status.get('target_state')=='reached':break
     time.sleep(.2)
    self.assertEqual(status['target_id'],result['target_id']);self.assertEqual(status['target_state'],'reached');self.assertLess(status['max_error_rad'],.03)
    time.sleep(3.2);status=manual.status();self.assertIsNone(status['owner']);self.assertFalse(status['lease_active']);self.assertEqual(status['target_state'],'held')
    self.assertGreater(status['steps'],1000)
    manual.command('sim','claim',{'owner':'manual'});ManualControl(driver,folder,PROFILE);time.sleep(.15);self.assertFalse(manual.status()['lease_active'])
   finally:driver.supervisor.stop('manual-sim')
if __name__=='__main__':unittest.main()
