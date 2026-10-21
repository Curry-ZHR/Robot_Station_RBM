"""Console tests use isolated state and fake devices; never publish robot commands."""
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
import copy
import json
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from console_driver import default_config
from console_runtime import ConsoleRuntime
from console_support import ConsoleError, now
from server import DataPlatformHandler
from console_access import ConsoleAccess
import importlib.util

APP = Path(__file__).resolve().parents[1]
PROFILE = APP / "static/assets/g1/profile.json"
if not PROFILE.is_file():
    PROFILE = APP.parent / "static/assets/g1/profile.json"
NAMES = json.loads(PROFILE.read_text())["body_joints"]


class FakeDriver:
    app_root = APP
    def __init__(self):
        self.data = {}
        self.calls = []
        self.settings = {"real": default_config("real"), "sim": default_config("sim")}

    def inspect(self, force=False):
        self.calls.append(("inspect", force))
        return {"checks": [{"id": "gpu", "label": "测试 GPU", "status": "passed", "scope": "环境", "detail": "fixture", "source": "fixture"}],
                "container": {"state": "ready", "owned": True, "running": True}, "observed_at": now()}

    def config(self, mode):
        return copy.deepcopy(self.settings[mode])

    def telemetry(self, mode):
        return copy.deepcopy(self.data.get(mode, {}))

    def port(self, port):
        return True

    def collection_available(self):
        return True

    def pc_service_status(self):
        return {"state":"running","owned":True,"observed_at":now(),"detail":"fixture"}

    def container(self):
        return {"state":"ready","owned":True,"running":True}

    def stop_service(self, service):
        self.calls.append(("stop_service",service))
        return {"message":"fixture stopped","service_id":service,"state":"stopped"}

    def start_probe(self, mode):
        self.calls.append(("start_probe", mode))
        return {"reused": False}

    def run_recipe(self, recipe, cancelled, log):
        self.calls.append(("recipe", recipe))
        log.write((recipe+" fixture OK\n").encode())
        if cancelled.is_set():raise ConsoleError("cancelled",409,"cancelled")


class RuntimeFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.adapter = SimpleNamespace(runtime_dir=self.root/"runtime", repo_root=self.root/"sonic")
        self.driver = FakeDriver()
        self.runtime = ConsoleRuntime(self.adapter, SimpleNamespace(groups=lambda: []), self.driver)
        self.addCleanup(self.runtime.close)

    def command(self, scope, action, payload=None, mode="sim", key="test-command", revision=None):
        return self.runtime.command(scope, {"action": action, "payload": payload or {}, "mode": mode,
            "profile_id": "unitree-g1-29", "expected_revision": self.runtime.state["revision"] if revision is None else revision}, key)

    def ready(self, mode="sim"):
        stamp = now()
        self.driver.settings[mode]["pico_calibration_confirmed"] = True
        self.driver.data[mode] = {"robot": {"observed_at": stamp, "joints": [{"name": n, "position_rad": i/100} for i,n in enumerate(reversed(NAMES))]},
            "battery": {"percent": 0, "observed_at": stamp, "source": "fixture"}, "controller": {"observed_at": stamp,"valid":True,"control_index":12},
            "pico": {"body_ready": True, "observed_at": stamp},
            "cameras": {n: {"state": "streaming", "observed_at": stamp} for n in ["head", "left_wrist", "right_wrist"]}}


class SnapshotTests(RuntimeFixture):
    def test_no_fake_robot_battery_or_camera_from_open_ports(self):
        snapshot = self.runtime.snapshot()["snapshot"]
        self.assertFalse(snapshot["robot"]["connected"])
        self.assertIsNone(snapshot["battery"]["percent"])
        self.assertTrue(all(c["state"] == "offline" for c in snapshot["cameras"]))
        self.assertEqual(snapshot["services"]["docker"]["state"], "ready")
        self.assertFalse(snapshot["interlocks"]["can_collect"])
        self.assertNotIn("inference.start", snapshot["capabilities"]["commands"])
        self.assertEqual([c for c in self.driver.calls if c[0] == "start_probe"], [])

    def test_named_feedback_battery_boundaries_and_expiry(self):
        self.ready()
        for percent in [0, 100]:
            self.driver.data["sim"]["battery"]["percent"] = percent
            snapshot = self.runtime.snapshot()["snapshot"]
            self.assertTrue(snapshot["robot"]["connected"])
            self.assertEqual(snapshot["battery"]["percent"], percent)
        self.driver.data["sim"]["battery"]["observed_at"] = (datetime.now(timezone.utc)-timedelta(seconds=16)).isoformat()
        self.assertIsNone(self.runtime.snapshot()["snapshot"]["battery"]["percent"])
        self.driver.data["sim"]["robot"]["observed_at"] = (datetime.now(timezone.utc)-timedelta(seconds=6)).isoformat()
        snapshot = self.runtime.snapshot()["snapshot"]
        self.assertFalse(snapshot["robot"]["connected"])
        self.assertEqual(snapshot["robot"]["joints"], [])

    def test_missing_duplicate_and_nonfinite_joints_rejected(self):
        for mutation in [lambda a: a.pop(), lambda a: a.__setitem__(0,a[1]), lambda a: a[0].update(position_rad=float('nan'))]:
            self.ready()
            mutation(self.driver.data["sim"]["robot"]["joints"])
            self.assertFalse(self.runtime.snapshot()["snapshot"]["robot"]["connected"])

    def test_modes_are_isolated_and_tracking_requires_calibration(self):
        self.ready("real")
        self.assertTrue(self.runtime.snapshot("real")["snapshot"]["interlocks"]["can_collect"])
        self.assertFalse(self.runtime.snapshot("sim")["snapshot"]["robot"]["connected"])
        self.driver.settings["real"]["pico_calibration_confirmed"] = False
        self.assertFalse(self.runtime.snapshot("real")["snapshot"]["interlocks"]["can_collect"])

    def test_explicit_readonly_connection_and_idempotency(self):
        body = {"action":"connect", "mode":"sim", "profile_id":"unitree-g1-29", "expected_revision":0, "payload":{}}
        a = self.runtime.command("robot", body, "same")
        self.assertEqual(a, self.runtime.command("robot", body, "same"))
        self.assertEqual(len([c for c in self.driver.calls if c[0] == "start_probe"]), 1)
        with self.assertRaises(ConsoleError) as ctx:
            self.runtime.command("robot", {**body, "mode":"real"}, "same")
        self.assertEqual(ctx.exception.status, 409)

    def test_request_validation_revision_conflict_and_unimplemented_scopes(self):
        with self.assertRaises(ConsoleError):self.command("self_check", "run", {"read_only":False})
        self.command("self_check", "run", {"read_only":True})
        with self.assertRaises(ConsoleError) as ctx:self.command("robot", "connect", key="next", revision=0)
        self.assertEqual(ctx.exception.code, "revision_conflict")
        for scope, action in [("inference","start"),("workflows","run")]:
            with self.assertRaises(ConsoleError) as ctx:self.command(scope, action, key=scope)
            self.assertEqual(ctx.exception.status, 501)
        with self.assertRaises(ConsoleError) as ctx:self.command("robot","apply_pose",mode="real",key="gated-real")
        self.assertEqual(ctx.exception.code,"onsite_validation_required")


class ConsoleHTTPTests(RuntimeFixture):
    def test_snapshot_and_command_use_v1_response_contract(self):
        server = ThreadingHTTPServer(("127.0.0.1",0), DataPlatformHandler)
        server.console_runtime = self.runtime
        server.console_access=ConsoleAccess(self.root/'access','127.0.0.1')
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}/api/v1/console"
            with urlopen(base+"/snapshot?mode=sim&profile_id=unitree-g1-29") as r:
                data = json.load(r)
            self.assertTrue(data["ok"])
            self.assertEqual(data["snapshot"]["revision"],0)
            self.assertTrue(data['snapshot']['access']['authorized'])
            body={"action":"run","mode":"sim","profile_id":"unitree-g1-29","expected_revision":0,"payload":{"read_only":True}}
            forbidden=Request(base+"/self-check",json.dumps(body).encode(),{"Content-Type":"application/json","Idempotency-Key":"csrf-negative","Origin":base.removesuffix('/api/v1/console')})
            with self.assertRaises(HTTPError) as error:urlopen(forbidden)
            self.assertEqual(error.exception.code,403)
            self.assertEqual(self.runtime.state['revision'],0)
            request=Request(base+"/self-check",json.dumps(body).encode(),{"Content-Type":"application/json","Idempotency-Key":"http-test"})
            with urlopen(request) as r:self.assertTrue(json.load(r)["ok"])
            with self.assertRaises(HTTPError) as error:urlopen(Request(base+"/self-check",b'{}',{"Content-Type":"application/json"}))
            self.assertEqual(error.exception.code,400)
            self.assertIsInstance(json.load(error.exception)["error"],dict)
        finally:
            server.shutdown();server.server_close();thread.join()

    @unittest.skipUnless(importlib.util.find_spec('jsonschema'),'Install requirements-console-test.txt')
    def test_snapshot_and_acknowledgement_conform_to_openapi(self):
        import jsonschema
        contract_path=APP/'contracts/console-v1.openapi.json'
        if not contract_path.is_file():contract_path=APP.parent/'contracts/console-v1.openapi.json'
        document=json.loads(contract_path.read_text())
        resolver=jsonschema.RefResolver.from_schema(document)
        snapshot=self.runtime.snapshot()['snapshot']
        for name,value in [('Snapshot',snapshot),('Accepted',self.command('self_check','run',{'read_only':True}))]:
            validator=jsonschema.Draft202012Validator(document['components']['schemas'][name],resolver=resolver)
            errors=[('/'.join(map(str,e.absolute_path)),e.validator) for e in validator.iter_errors(value)]
            self.assertEqual(errors,[])


class DeploymentTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.driver.settings["sim"]["prepare_timeout_seconds"] = .01
        binary = self.adapter.repo_root/"gear_sonic_deploy/target/release/g1_deploy_onnx_ref"
        binary.parent.mkdir(parents=True)
        binary.touch()

    def wait(self, job_id):
        deadline = time.monotonic()+5
        while time.monotonic()<deadline:
            result = self.runtime.job(job_id)["job"]
            if result["state"] not in {"pending","running"}:return result
            time.sleep(.02)
        self.fail("preparation did not finish")

    def test_actual_readiness_not_command_acceptance(self):
        result=self.command("deployment","prepare",{"allow_motion":False})
        self.assertEqual(result["state"],"accepted")
        job=self.wait(result["job_id"])
        self.assertEqual(job["state"],"waiting")
        self.assertEqual([s["state"] for s in job["steps"]],["succeeded","succeeded","blocked","blocked","blocked"])
        self.assertIn("docker_check",job["log"])
        self.assertEqual([c[1] for c in self.driver.calls if c[0]=="recipe"],["docker_start","docker_check","pc_service_start"])
        self.ready()
        result=self.command("deployment","prepare",{"allow_motion":False},key="again")
        self.assertEqual(self.wait(result["job_id"])["state"],"ready")

    def test_cancel_does_not_stop_reused_services(self):
        entered=threading.Event()
        def wait_recipe(recipe,flag,log):
            entered.set();flag.wait(3)
            raise ConsoleError("cancelled",409,"cancelled")
        self.driver.run_recipe=wait_recipe
        result=self.command("deployment","prepare",{"allow_motion":False})
        self.assertTrue(entered.wait(2))
        self.command("deployment","cancel",{"job_id":result["job_id"]},key="cancel",revision=0)
        self.assertEqual(self.wait(result["job_id"])["state"],"cancelled")
        self.assertEqual([c for c in self.driver.calls if c[0]=="stop"],[])

    def test_failure_single_job_and_motion_rejection(self):
        with self.assertRaises(ConsoleError):self.command("deployment","prepare",{"allow_motion":True})
        def failed_recipe(*args):raise ConsoleError("fixture failure",412,"recipe_failed")
        self.driver.run_recipe=failed_recipe
        result=self.command("deployment","prepare",{"allow_motion":False})
        job=self.wait(result["job_id"])
        self.assertEqual(job["state"],"failed")
        self.assertIn("fixture failure",job["message"])

    def test_service_start_runs_only_its_fixed_recipe(self):
        result=self.command("services","start",{"service_id":"pc_service"})
        self.assertEqual(self.wait(result["job_id"])["state"],"succeeded")
        self.assertEqual([c[1] for c in self.driver.calls if c[0]=="recipe"],["pc_service_start"])


if __name__ == "__main__":
    unittest.main()
