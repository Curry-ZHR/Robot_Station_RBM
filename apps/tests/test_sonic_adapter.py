from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from sonic_adapter import AdapterError, CollectionConfig, SonicAdapter


class CollectionConfigTests(unittest.TestCase):
    def test_valid_payload(self):
        config = CollectionConfig.from_payload(
            {
                "mode": "sim",
                "task_prompt": "pick up cup",
                "dataset_name": "cup-demo_01",
                "camera_host": "192.168.123.164",
                "camera_port": 5555,
                "frequency": 30,
            }
        )
        self.assertEqual(config.mode, "sim")
        self.assertEqual(config.frequency, 30)

    def test_rejects_unsafe_dataset_name(self):
        with self.assertRaises(AdapterError):
            CollectionConfig.from_payload({"dataset_name": "../outside", "task_prompt": "demo"})

    def test_rejects_bad_frequency(self):
        with self.assertRaises(AdapterError):
            CollectionConfig.from_payload({"frequency": 0, "task_prompt": "demo"})


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "sonic_deploy"
        dataset = self.repo / "outputs" / "demo-01"
        (dataset / "meta").mkdir(parents=True)
        (dataset / "meta" / "info.json").write_text(
            json.dumps({"fps": 50, "total_frames": 100, "total_episodes": 1}), encoding="utf-8"
        )
        (dataset / "meta" / "episodes.jsonl").write_text('{"episode_index": 0}\n', encoding="utf-8")
        (dataset / "data.bin").write_bytes(b"x" * 24)

    def tearDown(self):
        self.temp.cleanup()

    @mock.patch("sonic_adapter.KeyboardPublisher")
    def test_scans_lerobot_dataset(self, publisher):
        publisher.return_value.ready = True
        adapter = SonicAdapter(self.repo, self.root / "runtime")
        datasets = adapter.datasets()
        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0]["name"], "demo-01")
        self.assertEqual(datasets[0]["episodes"], 1)
        self.assertEqual(datasets[0]["frames"], 100)
        self.assertGreater(datasets[0]["size_bytes"], 24)
        self.assertEqual(datasets[0]["version"], "v2.1")
        self.assertIn(datasets[0]["quality_status"], {"qualified", "warning"})
        self.assertGreaterEqual(datasets[0]["quality_score"], 94)

    @mock.patch("sonic_adapter.KeyboardPublisher")
    def test_overview_exposes_monitoring_quality_and_report(self, publisher):
        publisher.return_value.ready = True
        adapter = SonicAdapter(self.repo, self.root / "runtime")
        with mock.patch.object(adapter, "session_running", return_value=False):
            overview = adapter.overview()
        self.assertTrue(overview["ok"])
        self.assertEqual(overview["source"], "demo_telemetry")
        self.assertEqual(len(overview["joints"]), 14)
        self.assertEqual(len(overview["cameras"]), 3)
        self.assertEqual(overview["quality"]["recommendation"], "合格，可保存")
        self.assertEqual(overview["report"]["datasets"], 1)


if __name__ == "__main__":
    unittest.main()
