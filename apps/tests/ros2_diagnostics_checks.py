"""Real Domain 99 graph discovery, isolated test-only publishers."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from console_support import atomic_json
from ros2_camera_test_support import Ros2CameraFixture
APP=Path(__file__).resolve().parents[1]
class GraphChecks(unittest.TestCase):
 def test_discovers_offered_types_and_qos(self):
  with Ros2CameraFixture(APP) as fixture:
   fixture.wait(lambda:fixture.status().get('state')=='streaming')
   config=fixture.config['ros2_camera'];path=fixture.root/'graph.json';atomic_json(path,config)
   result=subprocess.run(['bash','-c','source /opt/ros/humble/setup.bash; exec "$@"','graph-check',sys.executable,str(APP/'ros2_graph_probe.py'),'--config',str(path)],capture_output=True,text=True,timeout=10)
   self.assertEqual(result.returncode,0,result.stderr)
   data=json.loads(result.stdout.splitlines()[-1]);self.assertEqual(data['domain_id'],99);self.assertEqual(len(data['topics']),3)
   for row in data['topics']:
    self.assertTrue(row['publishers']);self.assertTrue(any(p['compatible'] for p in row['publishers']))
    self.assertIn(row['expected_type'],row['advertised_types'])
   config['topics']['head']['reliability']='reliable';atomic_json(path,config)
   result=subprocess.run(['bash','-c','source /opt/ros/humble/setup.bash; exec "$@"','graph-check',sys.executable,str(APP/'ros2_graph_probe.py'),'--config',str(path)],capture_output=True,text=True,timeout=10)
   data=json.loads(result.stdout.splitlines()[-1]);head=next(r for r in data['topics'] if r['camera']=='head')
   self.assertFalse(any(p['compatible'] for p in head['publishers']))
if __name__=='__main__':unittest.main()
