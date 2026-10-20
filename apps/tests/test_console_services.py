"""Infrastructure stop ownership and live-process tests; no robot IO."""
import copy
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
import unittest

from console_driver import SystemDriver
from console_support import ConsoleError, now
from test_console_runtime import APP, RuntimeFixture


class ServiceCommands(RuntimeFixture):
    def test_both_stops_are_available_without_robot_feedback(self):
        snap=self.runtime.snapshot()["snapshot"]
        for service in ("docker","pc_service"):
            self.assertIn("services."+service+".stop",snap["capabilities"]["commands"])
            self.assertTrue(snap["services"][service]["stop_allowed"])
        self.assertFalse(snap["robot"]["connected"])

    def test_success_is_idempotent_and_does_not_stop_other_services(self):
        for service in ("docker","pc_service"):
            result=self.command("services","stop",{"service_id":service},key=service)
            self.assertEqual(result["state"],"stopped")
            repeated=self.command("services","stop",{"service_id":service},key=service,revision=self.runtime.state["revision"]-1)
            self.assertEqual(result,repeated)
        self.assertEqual([c for c in self.driver.calls if c[0]=="stop_service"],[("stop_service","docker"),("stop_service","pc_service")])

    def test_tasks_in_either_mode_block_before_driver_side_effects(self):
        for kind in ("recording","manual","real_manual","preparation"):
            with self.subTest(kind=kind):
                target=self.runtime.recorder if kind=="recording" else self.runtime.manual if kind=="manual" else self.runtime.real_manual
                if kind=="preparation":self.runtime.state["jobs"]["other-mode"]={"state":"running","mode":"real"}
                else:
                    original=target.active;target.active=lambda:True
                try:
                    snap=self.runtime.snapshot()["snapshot"]
                    for service in ("docker","pc_service"):
                        self.assertFalse(snap["services"][service]["stop_allowed"])
                        with self.assertRaises(ConsoleError) as ctx:self.command("services","stop",{"service_id":service},key=kind+service)
                        self.assertEqual(ctx.exception.status,409)
                finally:
                    if kind=="preparation":self.runtime.state["jobs"].pop("other-mode")
                    else:target.active=original
        self.assertFalse(any(c[0]=="stop_service" for c in self.driver.calls))

    def test_fresh_controller_in_other_mode_and_external_users_block(self):
        self.driver.data["real"]={"controller":{"observed_at":now()}}
        with self.assertRaises(ConsoleError):self.command("services","stop",{"service_id":"docker"})
        self.driver.data.clear()
        self.driver.service_stop_blockers=lambda service:["external controller still active"]
        with self.assertRaises(ConsoleError):self.command("services","stop",{"service_id":"pc_service"})
        self.assertFalse(any(c[0]=="stop_service" for c in self.driver.calls))

    def test_foreign_service_failure_never_reports_success(self):
        self.driver.pc_service_status=lambda:{"state":"running","owned":False}
        with self.assertRaises(ConsoleError):self.command("services","stop",{"service_id":"pc_service"})
        self.driver.pc_service_status=lambda:{"state":"running","owned":True}
        self.driver.stop_service=lambda service:(_ for _ in ()).throw(ConsoleError("timeout",503,"service_stop_failed"))
        revision=self.runtime.state["revision"]
        with self.assertRaises(ConsoleError):self.command("services","stop",{"service_id":"pc_service"},key="failed")
        self.assertEqual(self.runtime.state["revision"],revision)
        self.assertNotIn("failed",self.runtime.state["idempotency"])


class DockerOwnership(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.driver=SystemDriver(root,root/'runtime',APP)
        self.driver.service_stop_blockers=lambda service:[]

    def test_stop_uses_immutable_id_and_checks_actual_exit(self):
        identity="a"*64;calls=[]
        self.driver.container=lambda:{"owned":True,"running":True,"container_id":identity}
        def command(args,timeout):
            calls.append(args)
            return (0,"false\n") if args[1]=="inspect" else (0,identity)
        self.driver.command=command
        self.assertEqual(self.driver.stop_service("docker")["state"],"stopped")
        self.assertEqual(calls[0],["docker","stop","--timeout","15",identity])
        self.assertIsNone(self.driver._cache)

    def test_foreign_or_uncertain_identity_is_never_stopped(self):
        for state in ({"owned":False},{"owned":True,"running":True,"container_id":"sonic-4070"}):
            self.driver.container=lambda:state
            with patch.object(self.driver,"command") as call:
                with self.assertRaises(ConsoleError):self.driver.stop_service("docker")
                call.assert_not_called()

    def test_active_build_or_shell_inside_container_blocks(self):
        self.driver.container=lambda:{"owned":True,"running":True,"container_id":"b"*64}
        del self.driver.service_stop_blockers
        with patch("console_driver.Path.iterdir",return_value=[]):
            self.driver.command=lambda args,timeout:(0,"PID COMMAND\n11 docker-init\n12 sleep\n13 bash\n")
            self.assertTrue(self.driver.service_stop_blockers("docker"))
            self.driver.command=lambda args,timeout:(0,"PID COMMAND\n11 docker-init\n12 sleep\n")
            self.assertFalse(self.driver.service_stop_blockers("docker"))
            self.driver.command=lambda args,timeout:(0,"COMMAND\nsleep\n")
            self.assertTrue(self.driver.service_stop_blockers("docker"))


SOURCE=Path(os.environ.get("ROBOT_STATION_XR_RUNTIME_SOURCE",str(APP.parents[1]/'sonic_deploy/gear_sonic/utils/teleop/xrobotoolkit_runtime.py')))

@unittest.skipUnless(SOURCE.is_file(),"shared XR runtime source not available")
class XRShutdown(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location("xr_service_lifecycle_test",SOURCE)
        self.xr=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.xr)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.xr.LOG_DIR=self.root/'logs'
        self.xr.runtime_dir=lambda:self.root/'runtime'
        self.xr._active_users=lambda:[]
        self.xr._grpc_ready=lambda:False

    def test_foreign_installation_and_active_users_are_not_signalled(self):
        self.xr._processes=lambda name:[{"pid":os.getpid(),"executable":"/opt/other/"+name}]
        with self.assertRaises(RuntimeError):self.xr.stop_runtime()
        self.assertFalse((self.xr.LOG_DIR/'service.stopped').exists())
        self.xr._active_users=lambda:[999]
        with self.assertRaises(RuntimeError):self.xr.stop_runtime()

    def test_unknown_grpc_owner_is_not_stopped(self):
        self.xr._processes=lambda name:[];self.xr._grpc_ready=lambda:True
        with self.assertRaises(RuntimeError):self.xr.stop_runtime()

    def test_repeated_stop_is_idempotent_and_blocks_implicit_restart(self):
        self.xr._processes=lambda name:[]
        self.assertTrue(self.xr.stop_runtime()["stopped"])
        self.assertTrue(self.xr.stop_runtime()["stopped"])
        self.xr._validate_files=lambda:None
        with patch.object(self.xr.subprocess,"Popen") as spawn:
            with self.assertRaisesRegex(RuntimeError,"explicitly start"):self.xr.ensure_service()
            spawn.assert_not_called()

    @unittest.skipUnless(sys.platform=="linux" and hasattr(os,"pidfd_open"),"Linux pidfd required")
    def test_real_owned_fixture_processes_exit_without_touching_outsider(self):
        root=self.xr.runtime_dir();unity=root/'SDKDemo/RobotUnityDemo/RobotLinuxDemo.x86_64'
        unity.parent.mkdir(parents=True)
        service=root/'RoboticsServiceProcess'
        for p in (service,unity):shutil.copy2('/bin/sleep',p)
        children=[subprocess.Popen([str(p),'30']) for p in (service,unity)]
        outsider=subprocess.Popen(['/bin/sleep','30'])
        original=self.xr._processes
        self.xr._processes=lambda name:[row for row in original(name) if row['pid'] in {p.pid for p in children}]
        try:
            result=self.xr.stop_runtime()
            self.assertEqual(set(result['pids']),{p.pid for p in children})
            for p in children:self.assertIsNotNone(p.wait(timeout=2))
            self.assertIsNone(outsider.poll())
        finally:
            for p in children+[outsider]:
                if p.poll() is None:p.terminate()
                p.wait(timeout=3)


if __name__=='__main__':unittest.main()
