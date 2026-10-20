"""Meaningful conversion tests using tiny synthetic fixtures, never robot channels."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset_conversion import ConversionManager, ConversionError, inspect_source

AVAILABLE = all(importlib.util.find_spec(name) for name in ["numpy", "pyarrow", "h5py"])
if AVAILABLE:
    import numpy as np
    import h5py
    import pyarrow as pa
    import pyarrow.parquet as pq


@unittest.skipUnless(AVAILABLE and shutil.which("ffmpeg") and shutil.which("ffprobe"), "Use apps/.venv_conversion with ffmpeg")
class ConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_root = Path(tempfile.mkdtemp(prefix="robot-station-conversion-fixture-"))
        source = cls.fixture_root / "session"
        (source / "meta").mkdir(parents=True)
        features = {
            "observation.state": {"dtype": "float32", "shape": [43]},
            "action.wbc": {"dtype": "float32", "shape": [43]},
            "teleop.test_matrix": {"dtype": "float64", "shape": [2, 3]},
            "annotation.text": {"dtype": "string", "shape": [1]},
            **{key: {"dtype": "int64", "shape": [1]} for key in ["index", "frame_index", "episode_index", "task_index"]},
            "timestamp": {"dtype": "float32", "shape": [1]},
            **{"observation.images." + key: {"dtype": "video", "shape": [16, 16, 3]} for key in ["head", "left_wrist", "right_wrist"]},
        }
        info = {"codebase_version": "v2.1", "robot_type": "unitree_g1", "fps": 4,
                "total_episodes": 2, "total_frames": 16, "chunks_size": 1000,
                "data_path": "data/chunk-{episode_chunk:03d}/episode_{episode_index:06d}.parquet",
                "video_path": "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
                "features": features, "script_config": {"test_fixture": True},
                "discarded_episode_indices": [1]}
        (source / "meta/info.json").write_text(json.dumps(info))
        (source / "meta/episodes.jsonl").write_text("\n".join(json.dumps({"episode_index": i, "length": 8, "tasks": ["合成验证"]}, ensure_ascii=False) for i in range(2)))
        (source / "meta/tasks.jsonl").write_text('{"task_index":0,"task":"合成验证"}\n', encoding="utf-8")
        (source / "meta/modality.json").write_text('{"state":{},"action":{},"video":{},"annotation":{}}')
        clip = cls.fixture_root / "synthetic.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:size=16x16:rate=4", "-frames:v", "8",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip)], check=True)
        cls.expected = np.arange(8 * 43, dtype=np.float32).reshape(8, 43) / 100
        for i in range(2):
            values = {"observation.state": cls.expected.tolist(), "action.wbc": (cls.expected * .5).tolist(),
                      "teleop.test_matrix": np.arange(8 * 6, dtype=np.float64).reshape(8, 2, 3).tolist(),
                      "annotation.text": ["测试"] * 8, "timestamp": np.arange(8, dtype=np.float32) / 4,
                      "frame_index": np.arange(8), "index": np.arange(8) + i * 8,
                      "episode_index": np.full(8, i), "task_index": np.zeros(8, dtype=np.int64)}
            data = source / f"data/chunk-000/episode_{i:06d}.parquet"
            data.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(pa.Table.from_pydict(values), data)
            for camera in ["head", "left_wrist", "right_wrist"]:
                target = source / f"videos/chunk-000/observation.images.{camera}/episode_{i:06d}.mp4"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(clip, target)
        cls.template = source

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="robot-station-conversion-test-"))
        (self.root / "outputs").mkdir()
        self.source = self.root / "outputs/session"
        shutil.copytree(self.template, self.source)
        self.manager = ConversionManager(self.root / "outputs", self.root / "runtime", python=sys.executable)

    def test_active_or_incomplete_recording_cannot_be_converted(self):
        (self.source/".incomplete").write_text("recording")
        inspection=self.manager.inspect("session")["inspection"]
        self.assertFalse(inspection["can_convert"])
        self.assertTrue(any("采集任务" in message for message in inspection["errors"]))

    def payload(self, name="export", format="hdf5", mode="embedded_mp4"):
        inspection = self.manager.inspect("session")["inspection"]
        self.assertTrue(inspection["can_convert"], inspection["errors"])
        return {"dataset": "session", "format": format, "video_mode": mode, "output_name": name,
                "fingerprint": inspection["fingerprint"]}

    def wait(self, job):
        deadline = time.time() + 25
        while time.time() < deadline:
            current = self.manager.job(job["id"])["job"]
            if current["state"] in {"succeeded", "failed", "cancelled"}:
                return current
            time.sleep(.05)
        self.fail("Worker timeout")

    def hashes(self, root):
        return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}

    def test_hdf5_roundtrip_preserves_43d_fields_types_timestamps_tasks_and_original_video_bytes(self):
        before = self.hashes(self.source)
        job = self.wait(self.manager.create(self.payload())["job"])
        self.assertEqual(job["state"], "succeeded", job["message"])
        output = Path(job["output"])
        self.assertEqual(self.hashes(self.source), before)
        self.assertFalse((output / ".incomplete").exists())
        with h5py.File(output / "episodes/episode_000000.hdf5") as data:
            self.assertEqual(data.attrs["schema"], "sonic-hdf5-v1")
            self.assertEqual(data["frames/observation.state"].shape, (8, 43))
            self.assertEqual(data["frames/observation.state"].dtype, np.dtype("float32"))
            np.testing.assert_array_equal(data["frames/observation.state"][:], self.expected)
            np.testing.assert_array_equal(data["frames/timestamp"][:], np.arange(8) / 4)
            self.assertEqual(data["frames/teleop.test_matrix"].shape, (8, 2, 3))
            self.assertEqual(data["frames/annotation.text"].asstr()[0], "测试")
            self.assertIn("合成验证", data["meta/tasks_jsonl"].asstr()[()])
            for camera in ["head", "left_wrist", "right_wrist"]:
                key = "observation.images." + camera
                raw = data[f"videos/{key}/encoded_mp4"][:].tobytes()
                self.assertEqual(raw, (self.source / f"videos/chunk-000/{key}/episode_000000.mp4").read_bytes())
        manifest = json.loads((output / "conversion.json").read_text())
        self.assertTrue(manifest["preserve_all_episodes"])
        self.assertFalse(manifest["resampled"])
        self.assertEqual(json.loads((output / "meta/info.json").read_text())["discarded_episode_indices"], [1])

    def test_rgb_hdf5_decodes_three_complete_camera_streams(self):
        job = self.wait(self.manager.create(self.payload(mode="rgb"))["job"])
        self.assertEqual(job["state"], "succeeded", job["message"])
        with h5py.File(Path(job["output"]) / "episodes/episode_000000.hdf5") as data:
            for camera in ["head", "left_wrist", "right_wrist"]:
                images = data[f"videos/observation.images.{camera}/rgb"][:]
                self.assertEqual(images.shape, (8, 16, 16, 3))
                self.assertGreater(images[0, 0, 0, 2], 200)
                self.assertLess(images[0, 0, 0, 0], 10)

    def test_lerobot_exports_byte_identical_data_video_metadata_and_discard_flags(self):
        before = self.hashes(self.source)
        job = self.wait(self.manager.create(self.payload(format="lerobot_v21", mode="rgb"))["job"])
        self.assertEqual(job["state"], "succeeded", job["message"])
        self.assertEqual(self.hashes(self.source), before)
        self.assertEqual(json.loads((Path(job["output"])/"conversion.json").read_text())["video_mode"], "embedded_mp4")
        after = self.hashes(Path(job["output"]))
        self.assertEqual({key: after[key] for key in before}, before)

    def test_missing_numeric_data_blocks_conversion(self):
        path = self.source / "data/chunk-000/episode_000000.parquet"
        path.rename(path.with_suffix(".unavailable"))
        inspection = self.manager.inspect("session")["inspection"]
        self.assertFalse(inspection["can_convert"])
        self.assertIn("缺少", inspection["errors"][0])

    def test_demo_metadata_is_never_promoted_to_a_real_conversion(self):
        (self.source / "DEMO_ONLY.md").write_text("synthetic")
        inspection = self.manager.inspect("session")["inspection"]
        self.assertFalse(inspection["can_convert"])

    def test_version_three_is_rejected_instead_of_guessing_a_layout(self):
        path = self.source / "meta/info.json"
        info = json.loads(path.read_text());info["codebase_version"] = "v3.0";path.write_text(json.dumps(info))
        self.assertFalse(self.manager.inspect("session")["inspection"]["can_convert"])

    def test_path_traversal_and_symlink_sources_are_rejected(self):
        for name in ["../session", "/etc", "conversions"]:
            with self.assertRaises(ConversionError):
                self.manager.source(name)
        (self.root / "outputs/link").symlink_to(self.source)
        with self.assertRaises(ConversionError):
            self.manager.source("link")
        path = self.source / "meta/info.json"
        info = json.loads(path.read_text());info["data_path"] = "../../escape.parquet";path.write_text(json.dumps(info))
        self.assertFalse(self.manager.inspect("session")["inspection"]["can_convert"])

    def test_existing_output_is_not_overwritten(self):
        (self.root / "outputs/conversions/export").mkdir(parents=True)
        sentinel = self.root / "outputs/conversions/export/keep"
        sentinel.write_text("original")
        with self.assertRaises(ConversionError):
            self.manager.create(self.payload())
        self.assertEqual(sentinel.read_text(), "original")

    def test_changed_source_fingerprint_blocks_submission(self):
        payload = self.payload()
        path = self.source / "meta/info.json";path.write_text(path.read_text() + "\n")
        with self.assertRaises(ConversionError) as caught:
            self.manager.create(payload)
        self.assertEqual(caught.exception.status, 409)

    def test_invalid_numeric_shape_fails_without_changing_the_source(self):
        path = self.source / "data/chunk-000/episode_000000.parquet"
        table = pq.read_table(path).to_pydict()
        table["observation.state"][0] = table["observation.state"][0][:-1]
        pq.write_table(pa.Table.from_pydict(table), path)
        before = self.hashes(self.source)
        job = self.wait(self.manager.create(self.payload())["job"])
        self.assertEqual(job["state"], "failed")
        self.assertEqual(self.hashes(self.source), before)
        self.assertTrue((Path(job["output"]) / ".incomplete").exists())

    def test_video_frame_mismatch_fails_validation(self):
        path = self.source / "videos/chunk-000/observation.images.head/episode_000000.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=size=16x16:rate=4",
                        "-frames:v", "2", "-c:v", "libx264", str(path)], check=True)
        job = self.wait(self.manager.create(self.payload())["job"])
        self.assertEqual(job["state"], "failed")
        self.assertIn("帧数", job["message"])

    def test_video_fps_mismatch_is_not_silently_resampled(self):
        path = self.source / "videos/chunk-000/observation.images.head/episode_000000.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=size=16x16:rate=8",
                        "-frames:v", "8", "-c:v", "libx264", str(path)], check=True)
        job = self.wait(self.manager.create(self.payload())["job"])
        self.assertEqual(job["state"], "failed")
        self.assertIn("帧率", job["message"])

    def test_cancellation_and_single_job_ownership(self):
        payload = self.payload()
        job = self.manager.create(payload)["job"]
        with self.assertRaises(ConversionError) as caught:
            self.manager.create({**payload, "output_name": "another"})
        self.assertEqual(caught.exception.status, 409)
        self.manager.cancel(job["id"])
        result = self.wait(job)
        self.assertEqual(result["state"], "cancelled")

    def test_http_routes_create_poll_and_range_download_without_robot_adapter(self):
        from http.server import ThreadingHTTPServer
        from server import DataPlatformHandler
        import threading
        import urllib.request
        import urllib.error
        server = ThreadingHTTPServer(("127.0.0.1", 0), DataPlatformHandler)
        server.conversion_manager = self.manager
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(base + "/api/conversions/sources") as response:
                catalog = json.load(response)
            self.assertTrue(catalog["environment"]["ready"])
            request = urllib.request.Request(base + "/api/conversions/jobs", data=json.dumps(self.payload()).encode(), headers={"Content-Type":"application/json"})
            with opener.open(request) as response:
                self.assertEqual(response.status, 202)
                job = json.load(response)["job"]
            result = self.wait(job)
            self.assertEqual(result["state"], "succeeded", result["message"])
            url = base + "/api/conversions/jobs/" + job["id"] + "/download?path=episodes/episode_000000.hdf5"
            with opener.open(urllib.request.Request(url, headers={"Range":"bytes=0-7"})) as response:
                self.assertEqual(response.status, 206)
                self.assertEqual(response.read(), b"\x89HDF\r\n\x1a\n")
                self.assertNotEqual(response.headers["Content-Type"], "video/mp4")
            with self.assertRaises(urllib.error.HTTPError) as caught:
                opener.open(base + "/api/conversions/jobs/" + job["id"] + "/download?path=../../outside")
            self.assertEqual(caught.exception.code, 400)
            self.assertIn("message", json.load(caught.exception)["error"])
        finally:
            server.shutdown()
            server.server_close()

    def test_download_confined_to_successful_output(self):
        job = self.wait(self.manager.create(self.payload())["job"])
        self.assertEqual(job["state"], "succeeded")
        self.assertTrue(self.manager.download(job["id"], "episodes/episode_000000.hdf5").is_file())
        with self.assertRaises(ConversionError):
            self.manager.download(job["id"], "../../meta/info.json")


if __name__ == "__main__":
    unittest.main()
