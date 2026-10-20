from pathlib import Path
import importlib.util
import json
import sys
import tempfile
from types import SimpleNamespace
import unittest

from console_support import ConsoleError
from console_timeseries import read_series, TimeseriesService
from collection_workspace import CollectionWorkspace
from sonic_adapter import SonicAdapter

AVAILABLE = importlib.util.find_spec("pyarrow") is not None
APP = Path(__file__).resolve().parents[1]
PROFILE = APP/"static/assets/g1/profile.json"
if not PROFILE.is_file():PROFILE=APP.parent/"static/assets/g1/profile.json"
NAMES=json.loads(PROFILE.read_text())["body_joints"]+[f"finger_{i}" for i in range(14)]


@unittest.skipUnless(AVAILABLE,"Run with apps/.venv_conversion")
class TimeseriesTests(unittest.TestCase):
    def setUp(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        self.pa,self.pq=pa,pq
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/"outputs/session"
        (self.source/"meta").mkdir(parents=True)
        self.info={"codebase_version":"v2.1","robot_type":"unitree_g1","fps":4,"features":{
            "observation.state":{"names":NAMES,"shape":[43],"dtype":"float64"},"action.wbc":{"names":list(reversed(NAMES)),"shape":[43],"dtype":"float64"}}}
        self.rows={"timestamp":[7.5+i/4 for i in range(8)],"frame_index":list(range(8)),"episode_index":[0]*8,
            "observation.state":[[i+j/100 for j in range(43)] for i in range(8)],
            "action.wbc":[list(reversed([i-j/100 for j in range(43)])) for i in range(8)]}
        self.parquet=self.source/"data/chunk-000/episode_000000.parquet"
        self.parquet.parent.mkdir(parents=True)
        (self.source/"meta/episodes.jsonl").write_text('{"episode_index":0,"length":8}\n')
        self.save()

    def save(self):
        (self.source/"meta/info.json").write_text(json.dumps(self.info))
        self.pq.write_table(self.pa.Table.from_pydict(self.rows),self.parquet)

    def test_all_43_named_values_action_reordering_and_video_zero(self):
        before=self.parquet.read_bytes()
        result=read_series(self.source,0,NAMES[:29])
        self.assertEqual(result["joint_names"],NAMES)
        self.assertEqual(result["frames"][0]["time_s"],0)
        self.assertEqual(result["source_time_origin_s"],7.5)
        self.assertEqual(result["frames"][7]["action"],[7-j/100 for j in range(43)])
        self.assertEqual(result["frames"][3]["state"],[3+j/100 for j in range(43)])
        self.assertEqual(self.parquet.read_bytes(),before)

    def test_bounded_preview_retains_first_and_last_without_altering_time(self):
        result=read_series(self.source,0,NAMES[:29],3)
        self.assertTrue(result["sampled"])
        self.assertEqual(result["original_frames"],8)
        self.assertEqual(len(result["frames"]),3)
        self.assertEqual(result["frames"][0]["frame_index"],0)
        self.assertEqual(result["frames"][-1]["frame_index"],7)
        self.assertEqual(result["frames"][-1]["time_s"],1.75)

    def test_missing_duplicate_incompatible_names_and_wrong_units(self):
        for change in [lambda:self.info["features"]["observation.state"].pop("names"),
            lambda:self.info["features"]["action.wbc"].update(names=["duplicate"]*43),
            lambda:self.info["features"]["action.wbc"].update(unit="deg")]:
            original=json.loads(json.dumps(self.info));change();self.save()
            with self.assertRaises(ConsoleError):read_series(self.source,0,NAMES[:29])
            self.info=original

    def test_corrupt_timestamps_counts_and_values_are_rejected(self):
        for change in [lambda:self.rows["timestamp"].__setitem__(2,7.5),
            lambda:self.rows["observation.state"][0].__setitem__(0,float("nan")),
            lambda:self.rows["frame_index"].__setitem__(0,4)]:
            original=json.loads(json.dumps(self.rows));change();self.save()
            with self.assertRaises(ConsoleError):read_series(self.source,0,NAMES[:29])
            self.rows=original

    def test_service_isolated_process_cache_and_source_changes(self):
        adapter=SimpleNamespace(repo_root=self.root,runtime_dir=self.root/"runtime",
                                _read_json=SonicAdapter._read_json,_read_jsonl=SonicAdapter._read_jsonl)
        service=TimeseriesService(CollectionWorkspace(adapter),self.root/"runtime",python=sys.executable)
        first=service.get("session",0)
        self.assertEqual(service.get("session",0),first)
        self.rows["observation.state"][0][0]=.77;self.save()
        self.assertEqual(service.get("session",0)["frames"][0]["state"][0],.77)
        with self.assertRaises(Exception):service.get("../session",0)
        with self.assertRaises(ConsoleError):service.get("session",0,10001)
        self.info["demo_only"]=True;self.save()
        with self.assertRaises(ConsoleError):service.get("session",0)

    def test_symlink_parquet_escape_is_rejected(self):
        outside=self.root/"outside.parquet"
        self.parquet.rename(outside)
        self.parquet.symlink_to(outside)
        with self.assertRaises(ConsoleError):read_series(self.source,0,NAMES[:29])


if __name__=="__main__":unittest.main()
