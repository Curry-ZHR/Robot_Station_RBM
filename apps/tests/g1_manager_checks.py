"""Explicit manager/worker IPC checks; temporary runtime, memory transport, no DDS."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from console_driver import SystemDriver
from console_real import RealManualControl
from console_support import atomic_json,ConsoleError
from test_unitree_g1_control import PROFILE,parameters
APP=Path(__file__).resolve().parents[1];SONIC=APP.parents[1]/'sonic_deploy'
class ManagerChecks(unittest.TestCase):
 def test_gate_prevents_worker_start_without_any_approval(self):
  with tempfile.TemporaryDirectory() as folder:
   driver=SystemDriver(SONIC,folder,APP);manager=RealManualControl(driver,folder,PROFILE)
   with self.assertRaises(ConsoleError) as error:manager.command('initialize',{})
   self.assertEqual(error.exception.code,'onsite_validation_required');self.assertFalse(driver.supervisor.running('manual-real'))
 def test_manager_private_lease_target_sequence_release_and_restart(self):
  with tempfile.TemporaryDirectory() as folder:
   driver=SystemDriver(SONIC,folder,APP);atomic_json(driver.config_path,{'real':{'interface':'lo','dds_domain':231}})
   manager=RealManualControl(driver,folder,PROFILE);config=parameters();atomic_json(manager.directory/'test-parameters.json',config)
   original=driver.supervisor.start
   def launch(name,argv,*args,**kwargs):
    argv=[str(APP/'tests/g1_worker_fixture.py') if str(a).endswith('/console_real_worker.py') else a for a in argv]
    return original(name,argv,*args,**kwargs)
   try:
    with patch('console_real.load_commissioning',return_value={**config,'expires_at_unix':time.time()+60}),patch.object(driver.supervisor,'start',side_effect=launch):
     manager.command('initialize',{})
     with self.assertRaises(ConsoleError):manager.command('claim',{'owner':'manual'})
     claim=manager.command('claim',{'owner':'manual','supported_operation_confirmed':True});token=claim['lease_token']
     until=time.monotonic()+1
     while manager.status()['state']!='active' and time.monotonic()<until:time.sleep(.02)
     self.assertNotIn(token,json.dumps(manager.status()))
     with self.assertRaises(ConsoleError):manager.command('heartbeat',{'lease_token':'wrong'})
     joints=[{'name':n,'position_rad':.1 if n=='left_elbow_joint' else 0.} for n in PROFILE['body_joints']]
     request={'lease_token':token,'sequence':0,'joints':joints,'unit':'rad','transition_seconds':1}
     result=manager.command('apply_pose',request)
     with self.assertRaises(ConsoleError):manager.command('apply_pose',request)
     until=time.monotonic()+4
     while time.monotonic()<until:
      manager.command('heartbeat',{'lease_token':token});status=manager.status()
      if status.get('target_state')=='reached':break
      time.sleep(.1)
     self.assertEqual(status['target_id'],result['target_id']);self.assertEqual(status['target_state'],'reached')
     stopped=manager.command('release',{'lease_token':token});self.assertTrue(stopped['stop_acknowledged']);self.assertFalse(driver.supervisor.running('manual-real'))
     manager.command('initialize',{});claim=manager.command('claim',{'owner':'manual','supported_operation_confirmed':True})
     # A new web instance overwrites the IPC arm record; the independent worker exits.
     restarted=RealManualControl(driver,folder,PROFILE);until=time.monotonic()+3
     while driver.supervisor.running('manual-real') and time.monotonic()<until:time.sleep(.03)
     self.assertFalse(driver.supervisor.running('manual-real'));self.assertIsNone(restarted.status()['owner'])
   finally:driver.supervisor.stop('manual-real',timeout=5)
if __name__=='__main__':unittest.main()
