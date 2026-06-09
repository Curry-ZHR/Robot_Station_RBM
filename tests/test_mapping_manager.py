import json
import struct
import sys
import time
from pathlib import Path

from modules.map.manager import MappingManager, mapping_result_status


def wait_for_idle(manager, timeout_sec=2.0):
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        status = manager.status()
        if not status["busy"]:
            return status
        time.sleep(0.02)
    raise AssertionError("mapping manager did not become idle")


def write_binary_pcd(path, points):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = "\n".join(
        [
            "# .PCD v0.7 - Point Cloud Data file format",
            "VERSION 0.7",
            "FIELDS x y z intensity",
            "SIZE 4 4 4 4",
            "TYPE F F F F",
            "COUNT 1 1 1 1",
            f"WIDTH {len(points)}",
            "HEIGHT 1",
            "VIEWPOINT 0 0 0 1 0 0 0",
            f"POINTS {len(points)}",
            "DATA binary",
            "",
        ]
    ).encode("ascii")
    payload = b"".join(struct.pack("<ffff", *point) for point in points)
    path.write_bytes(header + payload)


def make_fake_mapper(tmp_path, exit_code=0, sleep_sec=0.0):
    script = tmp_path / "fake_mapper.py"
    script.write_text(
        f"""
import argparse
import json
import pathlib
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("--session-dir", required=True)
parser.add_argument("--frames")
parser.add_argument("--cloud-topic")
parser.add_argument("--odom-topic")
parser.add_argument("--base-frame")
parser.add_argument("--capture-timeout-sec")
parser.add_argument("--progress-path")
parser.add_argument("--voxel-leaf")
parser.add_argument("--ndt-resolution")
parser.add_argument("--gicp-max-correspondence")
args = parser.parse_args()
session = pathlib.Path(args.session_dir)
if args.progress_path:
    pathlib.Path(args.progress_path).write_text(json.dumps({{
        "phase": "registering",
        "capturedFrames": int(args.frames),
        "targetFrames": int(args.frames),
    }}), encoding="utf-8")
if {sleep_sec!r}:
    time.sleep({sleep_sec!r})
(session / "keyframes").mkdir(parents=True, exist_ok=True)
(session / "map_tmp.pcd").write_text("pcd\\n", encoding="utf-8")
(session / "last_result.json").write_text(json.dumps({{
	    "ok": {exit_code == 0},
    "detail": "fake mapper result",
    "keyframe": {{
        "index": 0,
        "path": str(session / "keyframes" / "keyframe_000.pcd"),
        "frames": int(args.frames),
        "cloudTopic": args.cloud_topic,
    }},
    "registration": {{
        "stage": "initial_map",
        "fitness": 0.0,
    }},
}}), encoding="utf-8")
sys.exit({exit_code})
""",
        encoding="utf-8",
    )
    return (sys.executable, str(script))


def make_polluting_fake_mapper(tmp_path):
    script = tmp_path / "polluting_fake_mapper.py"
    script.write_text(
        """
import argparse
import json
import pathlib
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--session-dir", required=True)
parser.add_argument("--frames")
parser.add_argument("--cloud-topic")
parser.add_argument("--odom-topic")
parser.add_argument("--base-frame")
parser.add_argument("--capture-timeout-sec")
parser.add_argument("--progress-path")
parser.add_argument("--voxel-leaf")
parser.add_argument("--ndt-resolution")
parser.add_argument("--gicp-max-correspondence")
args = parser.parse_args()
session = pathlib.Path(args.session_dir)
keyframe_dir = session / "keyframes"
keyframe_dir.mkdir(parents=True, exist_ok=True)
(session / "map_tmp.pcd").write_text("polluted map\\n", encoding="utf-8")
(session / "state.txt").write_text("polluted state\\n", encoding="utf-8")
(keyframe_dir / "keyframe_001.pcd").write_text("polluted keyframe\\n", encoding="utf-8")
(session / "last_result.json").write_text(json.dumps({
    "ok": False,
    "detail": "polluted mapper failed after writing files",
    "keyframe": {
        "index": 1,
        "path": str(keyframe_dir / "keyframe_001.pcd"),
        "frames": int(args.frames or 0),
    },
    "registration": {
        "stage": "ndt_gicp",
        "fitness": 0.01,
        "finalTransform": [1, 0, 0, 9, 0, 1, 0, 8, 0, 0, 1, 7, 0, 0, 0, 1],
    },
}), encoding="utf-8")
sys.exit(3)
""",
        encoding="utf-8",
    )
    return (sys.executable, str(script))


def test_mapping_session_capture_and_save(tmp_path):
    manager = MappingManager(
        tmp_root=tmp_path / "tmp",
        output_root=tmp_path / "out",
        mapper_command=make_fake_mapper(tmp_path),
    )

    started = manager.start({"frameCount": 7, "cloudTopic": "/rslidar_points"})
    assert started["ok"]
    assert started["session"]["settings"]["frameCount"] == 7

    capture = manager.capture({})
    assert capture["ok"]
    status = wait_for_idle(manager)
    session = status["session"]
    assert session["status"] == "ready"
    assert session["keyframes"][0]["frames"] == 7

    saved = manager.save({"name": "test_map"})
    assert saved["ok"]
    assert saved["path"].endswith("test_map.pcd")


def test_mapping_start_clears_previous_tmp_entries(tmp_path):
    tmp_root = tmp_path / "tmp"
    old_session = tmp_root / "old_session"
    old_session.mkdir(parents=True)
    (old_session / "mapper.log").write_text("old\n", encoding="utf-8")
    (tmp_root / "stray.tmp").write_text("stray\n", encoding="utf-8")
    manager = MappingManager(
        tmp_root=tmp_root,
        output_root=tmp_path / "out",
        mapper_command=make_fake_mapper(tmp_path),
    )

    started = manager.start({"sessionId": "new_session"})

    assert started["ok"]
    assert started["tempCleanup"]["removed"] == 2
    assert not old_session.exists()
    assert not (tmp_root / "stray.tmp").exists()
    assert Path(started["session"]["sessionDir"]).name == "new_session"
    assert Path(started["session"]["sessionDir"]).exists()


def test_mapping_reset_clears_all_tmp_entries(tmp_path):
    tmp_root = tmp_path / "tmp"
    manager = MappingManager(
        tmp_root=tmp_root,
        output_root=tmp_path / "out",
        mapper_command=make_fake_mapper(tmp_path),
    )

    started = manager.start({"sessionId": "active"})
    session_dir = Path(started["session"]["sessionDir"])
    old_session = tmp_root / "old_session"
    old_session.mkdir(parents=True)
    (old_session / "mapper.log").write_text("old\n", encoding="utf-8")
    (session_dir / "map_tmp.pcd").write_text("pcd\n", encoding="utf-8")

    reset = manager.reset({})

    assert reset["ok"]
    assert reset["tempCleanup"]["removed"] == 2
    assert list(tmp_root.iterdir()) == []
    assert manager.status()["session"] is None


def test_mapping_capture_failure_status(tmp_path):
    manager = MappingManager(
        tmp_root=tmp_path / "tmp",
        output_root=tmp_path / "out",
        mapper_command=make_fake_mapper(tmp_path, exit_code=3),
    )

    manager.start({})
    result = manager.capture({})
    assert result["ok"]
    status = wait_for_idle(manager)
    assert status["session"]["status"] == "failed"
    assert status["session"]["lastError"]
    assert mapping_result_status({"ok": False, "code": "MAP-BUSY"}) == 409


def test_mapping_capture_failure_restores_previous_map_files(tmp_path):
    manager = MappingManager(
        tmp_root=tmp_path / "tmp",
        output_root=tmp_path / "out",
        mapper_command=make_polluting_fake_mapper(tmp_path),
    )
    started = manager.start({"sessionId": "active"})
    session_dir = Path(started["session"]["sessionDir"])
    keyframe_dir = session_dir / "keyframes"
    previous_keyframe = keyframe_dir / "keyframe_000.pcd"
    previous_result = {
        "ok": True,
        "detail": "previous accepted frame",
        "mapPath": str(session_dir / "map_tmp.pcd"),
        "keyframe": {
            "index": 0,
            "path": str(previous_keyframe),
            "frames": 10,
        },
        "registration": {
            "stage": "initial_map",
            "fitness": 0.0,
            "finalTransform": [1, 0, 0, 0.5, 0, 1, 0, 0.25, 0, 0, 1, 0, 0, 0, 0, 1],
        },
    }
    write_binary_pcd(session_dir / "map_tmp.pcd", [(1.0, 2.0, 3.0, 4.0)])
    write_binary_pcd(previous_keyframe, [(1.0, 2.0, 3.0, 4.0)])
    previous_map_body = (session_dir / "map_tmp.pcd").read_bytes()
    previous_state = "previous state\n"
    (session_dir / "state.txt").write_text(previous_state, encoding="utf-8")
    (session_dir / "last_result.json").write_text(json.dumps(previous_result), encoding="utf-8")
    with manager._lock:
        manager._session["captureCount"] = 1
        manager._session["keyframes"] = [previous_result["keyframe"]]
        manager._session["lastResult"] = previous_result

    result = manager.capture({})
    assert result["ok"]
    status = wait_for_idle(manager)
    session = status["session"]

    assert session["status"] == "failed"
    assert session["captureCount"] == 1
    assert session["keyframes"] == [previous_result["keyframe"]]
    assert session["lastResult"] == previous_result
    assert (session_dir / "map_tmp.pcd").read_bytes() == previous_map_body
    assert (session_dir / "state.txt").read_text(encoding="utf-8") == previous_state
    assert not (keyframe_dir / "keyframe_001.pcd").exists()
    assert not (session_dir / ".rollback").exists()


def test_mapping_capture_progress_status(tmp_path):
    manager = MappingManager(
        tmp_root=tmp_path / "tmp",
        output_root=tmp_path / "out",
        mapper_command=make_fake_mapper(tmp_path, sleep_sec=0.2),
    )

    manager.start({})
    result = manager.capture({})
    assert result["ok"]

    deadline = time.monotonic() + 1.0
    progress = None
    while time.monotonic() < deadline:
        session = manager.status()["session"]
        progress = session.get("progress") or {}
        if progress.get("phase") == "registering":
            break
        time.sleep(0.02)

    assert progress["phase"] == "registering"
    assert progress["label"] == "配准中"
    assert "NDT/GICP" in progress["detail"]
    assert wait_for_idle(manager)["session"]["status"] == "ready"


def test_mapping_read_map_frame_requires_session(tmp_path):
    manager = MappingManager(
        tmp_root=tmp_path / "tmp",
        output_root=tmp_path / "out",
        mapper_command=make_fake_mapper(tmp_path),
    )

    result = manager.read_map_frame()

    assert not result["ok"]
    assert result["code"] == "MAP-NOSESSION"


def test_mapping_read_map_frame_returns_full_binary_map(tmp_path):
    manager = MappingManager(
        tmp_root=tmp_path / "tmp",
        output_root=tmp_path / "out",
        mapper_command=make_fake_mapper(tmp_path),
    )
    started = manager.start({"sessionId": "active"})
    session_dir = Path(started["session"]["sessionDir"])
    write_binary_pcd(
        session_dir / "map_tmp.pcd",
        [
            (1.0, 2.0, 3.0, 4.0),
            (-1.5, 0.25, 2.5, 8.0),
        ],
    )

    result = manager.read_map_frame()

    assert result["ok"]
    assert result["contentType"] == "application/octet-stream"
    assert result["pointCount"] == 2
    assert result["sourcePointCount"] == 2
    assert result["strideFloats"] == 4
    assert result["fields"] == ["x", "y", "z", "intensity"]
    assert result["body"] == struct.pack("<ffffffff", 1.0, 2.0, 3.0, 4.0, -1.5, 0.25, 2.5, 8.0)


def test_mapping_read_map_frame_rejects_missing_or_invalid_map(tmp_path):
    manager = MappingManager(
        tmp_root=tmp_path / "tmp",
        output_root=tmp_path / "out",
        mapper_command=make_fake_mapper(tmp_path),
    )
    started = manager.start({"sessionId": "active"})
    session_dir = Path(started["session"]["sessionDir"])

    missing = manager.read_map_frame()
    assert not missing["ok"]
    assert missing["code"] == "MAP-NOTFOUND"

    (session_dir / "map_tmp.pcd").write_text("pcd\n", encoding="utf-8")
    invalid = manager.read_map_frame()
    assert not invalid["ok"]
    assert invalid["code"] == "MAP-PCD"


def test_mapping_read_map_frame_rejects_path_escape(tmp_path):
    manager = MappingManager(
        tmp_root=tmp_path / "tmp",
        output_root=tmp_path / "out",
        mapper_command=make_fake_mapper(tmp_path),
    )
    manager.start({"sessionId": "active"})
    outside = tmp_path / "outside.pcd"
    write_binary_pcd(outside, [(0.0, 0.0, 0.0, 1.0)])
    with manager._lock:
        manager._session["tmpMapPath"] = str(outside)

    result = manager.read_map_frame()

    assert not result["ok"]
    assert result["code"] == "MAP-NOTFOUND"
