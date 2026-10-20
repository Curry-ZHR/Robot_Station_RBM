from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from console_collection import CollectionManager
from console_driver import default_config
from console_support import ConsoleError, atomic_json, now, read_json


class FakeSupervisor:
    def __init__(self):self.alive=set();self.calls=[]
    def running(self,name):return name in self.alive
    def start(self,name,argv,cwd):self.alive.add(name);self.calls.append((name,argv));return {"reused":False}
    def logs(self,name):return "fixture log"


class CollectionManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        python=self.root/"apps/.venv_collection/bin/python";python.parent.mkdir(parents=True);python.touch()
        self.adapter=SimpleNamespace(repo_root=self.root/"sonic",session_running=lambda:False)
        self.supervisor=FakeSupervisor()
        self.driver=SimpleNamespace(app_root=self.root/"apps",directory=self.root/"runtime",supervisor=self.supervisor,config=default_config)
        self.manager=CollectionManager(self.adapter,self.driver,self.root/"runtime")
        self.payload={"dataset":"test_session","task":"fixture","fps":5,"camera_ids":["head","left_wrist","right_wrist"]}

    def prepare(self):
        result=self.manager.prepare("sim",self.payload)
        self.folder=self.manager.directory/result["session_id"]
        return result

    def phase(self,state):
        atomic_json(self.folder/"status.json",{"state":state,"observed_at":now(),"elapsed_seconds":.2})

    def acknowledge(self,command,ok=True):
        atomic_json(self.folder/"commands"/(command+".result.json"),{"id":command,"ok":ok})

    def test_explicit_start_save_ack_and_restart_recovery(self):
        self.prepare();self.phase("ready")
        self.assertTrue(self.manager.snapshot("sim")["prepared"])
        self.manager.command("sim","start",self.payload,"start1")
        self.assertFalse(self.manager.snapshot("sim")["recording"])
        self.assertTrue(self.manager.snapshot("sim")["busy"])
        self.acknowledge("start1");self.phase("recording")
        recovered=CollectionManager(self.adapter,self.driver,self.root/"runtime")
        self.assertTrue(recovered.snapshot("sim")["recording"])
        recovered.command("sim","save",{},"save1")
        with self.assertRaises(ConsoleError):recovered.command("sim","save",{},"save2")
        request=read_json(next((self.folder/"commands").glob('*save1.request.json')))
        self.assertEqual(request["action"],"save")
        self.assertEqual(request["sequence"],2)
        self.acknowledge("save1");self.phase("ready")
        self.assertFalse(recovered.snapshot("sim")["recording"])

    def test_single_task_cross_mode_config_and_existing_output_interlocks(self):
        self.prepare();self.phase("ready")
        self.assertTrue(self.manager.snapshot("real")["mode_conflict"])
        with self.assertRaises(ConsoleError):self.manager.prepare("real",self.payload)
        with self.assertRaises(ConsoleError):self.manager.command("real","start",self.payload,"other-mode")
        with self.assertRaises(ConsoleError):self.manager.command("sim","start",{**self.payload,"fps":6},"changed")
        self.phase("ended")
        output=self.adapter.repo_root/"outputs/test_session";output.mkdir(parents=True)
        marker=output/"keep";marker.write_text("original")
        with self.assertRaises(ConsoleError):self.manager.prepare("sim",self.payload)
        self.assertEqual(marker.read_text(),"original")

    def test_unexpected_process_exit_releases_claim_without_inventing_success(self):
        self.prepare();self.phase("ready")
        self.manager.command('sim','start',self.payload,'unconfirmed-start')
        self.supervisor.alive.clear()
        snapshot=self.manager.snapshot("sim")
        self.assertEqual(snapshot["state"],"failed")
        self.assertFalse(snapshot["prepared"])
        self.assertFalse(snapshot["recording"])
        self.assertFalse(snapshot['busy'])
        self.assertFalse(snapshot['last_command']['ok'])
        self.assertFalse(self.manager.active())

    def test_end_rejects_unsaved_recording_and_stop_bypasses_pending_command(self):
        self.prepare();self.phase("recording")
        with self.assertRaises(ConsoleError):self.manager.command("sim","end",{},"end")
        self.manager.command("sim","save",{},"save")
        result=self.manager.command("sim","stop",{},"stop")
        self.assertEqual(result["state"],"accepted")
        self.assertEqual(read_json(self.manager.pointer)["pending_command"]["id"],"stop")

    def test_validation_and_old_session_conflict(self):
        for change in [{"dataset":"../escape"},{"fps":True},{"camera_ids":["head"]},{"task":""}]:
            with self.assertRaises(ConsoleError):self.manager.prepare("sim",{**self.payload,**change})
        self.adapter.session_running=lambda:True
        with self.assertRaises(ConsoleError):self.manager.prepare("sim",self.payload)


if __name__=="__main__":unittest.main()
