from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import json
import tempfile
import threading
import unittest
from unittest import mock

from collection_workspace import CollectionWorkspace
from server import DataPlatformHandler
from sonic_adapter import AdapterError, CollectionConfig, SonicAdapter


class CollectionWorkspaceFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "sonic_deploy"
        self.dataset = self.repo / "outputs" / "test-scene"
        (self.dataset / "meta").mkdir(parents=True)
        self.info = {
            "fps": 30, "total_episodes": 3, "discarded_episodes": [2],
            "chunks_size": 1000,
            "features": {"observation.images.head": {"dtype": "video"}},
            "video_path": "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
        }
        self.write_info()
        self.metadata = self.dataset / "meta/episodes.jsonl"
        self.metadata.write_text("\n".join(json.dumps({"episode_index": index, "length": (index + 1) * 30, "tasks": ["Pick a cup"]}) for index in range(3)) + "\n", encoding="utf-8")
        self.video_path = self.dataset / "videos/chunk-000/observation.images.head/episode_000000.mp4"
        self.video_path.parent.mkdir(parents=True)
        self.video_path.write_bytes(b"0123456789abcdef")
        publisher_patch = mock.patch("sonic_adapter.KeyboardPublisher")
        self.publisher = publisher_patch.start()
        self.addCleanup(publisher_patch.stop)
        self.publisher.return_value.ready = True
        self.publisher.return_value.endpoint = "tcp://127.0.0.1:5580"
        self.adapter = SonicAdapter(self.repo, self.root / "runtime")
        self.adapter.session_running = mock.Mock(return_value=False)
        self.adapter._port_open = mock.Mock(return_value=False)
        self.workspace = CollectionWorkspace(self.adapter)

    def tearDown(self):
        self.adapter.close()
        self.temp.cleanup()

    def write_info(self):
        (self.dataset / "meta/info.json").write_text(json.dumps(self.info), encoding="utf-8")


class CollectionWorkspaceTests(CollectionWorkspaceFixture):
    def test_metadata_counts_pagination_and_unreviewed_default(self):
        group = self.workspace.groups()[0]
        self.assertEqual(group["episodes"], 3)
        self.assertEqual(group["retained"], 2)
        self.assertEqual(group["counts"], {"A": 0, "B": 0, "F": 0, "unreviewed": 2, "discarded": 1})
        result = self.workspace.episodes("test-scene", offset=1, limit=1)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["episodes"][0]["episode_index"], 1)
        self.assertEqual(result["episodes"][0]["duration_seconds"], 2)
        self.assertIsNone(result["episodes"][0]["grade"])

    def test_demo_records_are_excluded_from_real_totals(self):
        self.info["demo_only"] = True
        self.write_info()
        totals = self.workspace.snapshot()["totals"]
        self.assertEqual(totals["episodes"], 0)
        self.assertEqual(totals["datasets"], 0)
        self.assertEqual(totals["demo_episodes"], 2)

    def test_rating_persists_without_modifying_raw_metadata(self):
        before = self.metadata.read_bytes()
        self.workspace.rate({"dataset": "test-scene", "episode": 0, "grade": "A"})
        reloaded = CollectionWorkspace(self.adapter)
        rows = reloaded.episodes("test-scene")["episodes"]
        self.assertEqual(next(row for row in rows if row["episode_index"] == 0)["grade"], "A")
        self.assertEqual(reloaded.groups()[0]["counts"]["A"], 1)
        self.assertEqual(self.metadata.read_bytes(), before)
        reloaded.rate({"dataset": "test-scene", "episode": 0, "grade": None})
        self.assertEqual(reloaded.groups()[0]["counts"]["unreviewed"], 2)

    def test_rejects_invalid_or_discarded_rating(self):
        for payload in [
            {"dataset": "test-scene", "episode": 0, "grade": "C"},
            {"dataset": "test-scene", "episode": 0, "grade": []},
            {"dataset": "test-scene", "episode": 99, "grade": "A"},
            {"dataset": "test-scene", "episode": 2, "grade": "A"},
            {"dataset": "test-scene", "episode": True, "grade": "A"},
        ]:
            with self.subTest(payload=payload), self.assertRaises(AdapterError):
                self.workspace.rate(payload)

    def test_missing_video_is_an_explicit_empty_list(self):
        review = self.workspace.review("test-scene", 1)
        self.assertEqual(review["videos"], [])
        self.assertEqual(review["episode"]["frames"], 60)

    def test_video_lookup_uses_declared_lerobot_paths(self):
        review = self.workspace.review("test-scene", 0)
        self.assertEqual(len(review["videos"]), 1)
        self.assertEqual(review["videos"][0]["label"], "主视角")
        self.assertEqual(self.workspace.video("test-scene", 0, "observation.images.head"), self.video_path.resolve())

    def test_rejects_directory_traversal_and_symlink_escape(self):
        for name in ("../outside", "/tmp", ".", ""):
            with self.subTest(name=name), self.assertRaises(AdapterError):
                self.workspace.episodes(name)
        outside = self.root / "outside"
        outside.mkdir()
        (self.repo / "outputs/escape").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(AdapterError):
            self.workspace.episodes("escape")
        self.video_path.unlink()
        outside_video = self.root / "outside.mp4"
        outside_video.write_bytes(b"private")
        self.video_path.symlink_to(outside_video)
        self.assertEqual(self.workspace.review("test-scene", 0)["videos"], [])

    def test_incomplete_last_metadata_line_does_not_hide_records(self):
        with self.metadata.open("a", encoding="utf-8") as target:
            target.write('{"episode_index": 3')
        self.assertEqual(self.workspace.episodes("test-scene")["total"], 3)

    def test_pagination_validation(self):
        for offset, limit in [(-1, 30), (0, 0), (0, 101)]:
            with self.subTest(offset=offset, limit=limit), self.assertRaises(AdapterError):
                self.workspace.episodes("test-scene", offset, limit)

    def test_config_save_persists_and_never_launches_collection(self):
        with mock.patch("sonic_adapter.subprocess.Popen") as launch:
            result = self.adapter.save_config({"task_prompt": "Pick a cup", "collection_date": "2026-10-15", "scene_id": 7})
        launch.assert_not_called()
        self.assertEqual(result["config"]["dataset_name"], "20261015_scene7")
        self.assertEqual(result["config"]["scene_id"], 7)
        self.assertEqual(json.loads(self.adapter.state_path.read_text())["config"]["dataset_name"], "20261015_scene7")
        self.adapter.session_running.return_value = True
        with self.assertRaises(AdapterError):
            self.adapter.save_config({"task_prompt": "New task"})

    def test_config_rejects_bad_types_and_dates(self):
        for payload in [{"frequency": "invalid"}, {"frequency": 1.5}, {"frequency": True}, {"scene_id": 0}, {"collection_date": "2026-02-30"}, {"wrist_cameras": "false"}]:
            with self.subTest(payload=payload), self.assertRaises(AdapterError):
                CollectionConfig.from_payload(payload)


class CollectionHTTPTests(CollectionWorkspaceFixture):
    # Reuse the temporary metadata fixture; only these additional methods exercise HTTP.
    def setUp(self):
        super().setUp()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), DataPlatformHandler)
        self.server.adapter = self.adapter
        self.server.workspace = self.workspace
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        super().tearDown()

    def request(self, path, method="GET", payload=None, headers=None):
        return urlopen(Request(self.base + path, data=json.dumps(payload).encode() if payload is not None else None, method=method, headers={"Content-Type": "application/json", **(headers or {})}), timeout=5)

    def test_collection_and_metadata_endpoints(self):
        with self.request("/api/collection") as response:
            result = json.load(response)
        self.assertEqual(result["totals"]["episodes"], 2)
        with self.request("/api/episodes?dataset=test-scene&offset=0&limit=1") as response:
            result = json.load(response)
        self.assertEqual(len(result["episodes"]), 1)
        with self.request("/api/episodes/rate", "POST", {"dataset": "test-scene", "episode": 0, "grade": "B"}) as response:
            self.assertEqual(json.load(response)["grade"], "B")

    def test_video_range_suffix_head_and_invalid_range(self):
        route = "/api/episodes/video?dataset=test-scene&episode=0&camera=observation.images.head"
        with self.request(route, headers={"Range": "bytes=2-5"}) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.headers["Content-Range"], "bytes 2-5/16")
            self.assertEqual(response.read(), b"2345")
        with self.request(route, headers={"Range": "bytes=-4"}) as response:
            self.assertEqual(response.read(), b"cdef")
        with self.request(route, "HEAD") as response:
            self.assertEqual(response.headers["Content-Length"], "16")
            self.assertEqual(response.read(), b"")
        for value in ["bytes=99-", "bytes=5-2", "bytes=0-1,4-5", "bytes=-0"]:
            with self.subTest(value=value), self.assertRaises(HTTPError) as caught:
                self.request(route, headers={"Range": value})
            self.assertEqual(caught.exception.code, 416)
            caught.exception.close()

    def test_unknown_api_and_invalid_requests_have_json_errors(self):
        for route, status in [("/api/missing", 404), ("/api/episodes?dataset=../outside", 400), ("/api/episodes?dataset=test-scene&offset=bad", 400), ("/api/collection?mode=bad", 400), ("/api/episodes/review?dataset=test-scene&episode=99", 404)]:
            with self.subTest(route=route), self.assertRaises(HTTPError) as caught:
                self.request(route)
            self.assertEqual(caught.exception.code, status)
            self.assertFalse(json.load(caught.exception)["ok"])
            caught.exception.close()


if __name__ == "__main__":
    unittest.main()
