"""Read-only ROS 2 camera subscriptions -> SONIC ImageMessageSchema over ZMQ.

ROS imports are deliberately lazy: the web/Unitree SDK process never joins the
camera domain or loads ROS libraries. No robot command publishers are created.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import time

from console_support import atomic_json, now, read_json

CAMERAS = ("head", "left_wrist", "right_wrist")


def default_ros2_config():
    return {"domain_id": 99, "rmw": "rmw_fastrtps_cpp", "localhost_only": False,
            "fps": 30, "width": 640, "height": 480, "resize_mode": "letterbox",
            "jpeg_quality": 85, "max_age_seconds": .5, "max_skew_seconds": .1,
            "topics": {name: {"topic": f"/camera/{name}/image_raw",
                              "message_type": "sensor_msgs/msg/Image",
                              "reliability": "best_effort", "depth": 5} for name in CAMERAS}}


def validate_ros2_config(value):
    if not isinstance(value, dict):
        raise ValueError("ros2_camera 必须是对象")
    result = default_ros2_config()
    if set(value)-set(result):
        raise ValueError("未知 ROS 2 相机配置项："+", ".join(sorted(set(value)-set(result))))
    result.update(copy.deepcopy(value))
    for key, lo, hi in [("domain_id", 0, 232), ("fps", 1, 60), ("width", 16, 1920),
                        ("height", 16, 1080), ("jpeg_quality", 20, 100)]:
        if type(result[key]) is not int or not lo <= result[key] <= hi:
            raise ValueError(f"ROS 2 {key} 配置无效")
    for key, lo, hi in [("max_age_seconds", .1, 2), ("max_skew_seconds", .005, .5)]:
        v = result[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not lo <= v <= hi:
            raise ValueError(f"ROS 2 {key} 配置无效")
    if result["max_skew_seconds"] > result["max_age_seconds"]:
        raise ValueError("三路时间差不能大于源帧有效期")
    if result["rmw"] not in {"rmw_fastrtps_cpp", "rmw_cyclonedds_cpp"}:
        raise ValueError("不支持的相机 ROS RMW")
    if type(result["localhost_only"]) is not bool or result["resize_mode"] not in {"reject", "letterbox", "stretch"}:
        raise ValueError("相机网络或图像缩放配置无效")
    if not isinstance(result["topics"], dict) or set(result["topics"]) != set(CAMERAS):
        raise ValueError("必须配置 head / left_wrist / right_wrist 三路 ROS 2 话题")
    topic_names = []
    for name, row in result["topics"].items():
        if not isinstance(row, dict) or set(row) != {"topic", "message_type", "reliability", "depth"}:
            raise ValueError(f"{name} 话题需包含 topic/message_type/reliability/depth")
        if not isinstance(row["topic"], str) or not re.fullmatch(r"/(?:[A-Za-z_][A-Za-z_0-9]*/)*[A-Za-z_][A-Za-z_0-9]*", row["topic"]) or len(row["topic"]) > 200:
            raise ValueError("相机话题必须是合法的绝对 ROS 2 名称")
        if row["message_type"] not in {"sensor_msgs/msg/Image", "sensor_msgs/msg/CompressedImage"}:
            raise ValueError("仅支持 ROS 2 Image / CompressedImage")
        if row["reliability"] not in {"best_effort", "reliable"} or type(row["depth"]) is not int or not 1 <= row["depth"] <= 10:
            raise ValueError("相机 QoS 配置无效")
        topic_names.append(row["topic"])
    if len(set(topic_names)) != 3:
        raise ValueError("三个视角必须映射到不同的 ROS 2 话题")
    return result


class CameraFrames:
    """Bounded latest frames, source clock checks and synchronized packet assembly."""
    def __init__(self, config, keys):
        self.config = validate_ros2_config(config)
        self.keys = keys
        self.frames = {}
        self.last_sent = {}
        self.errors = {}
        self.counts = {name: 0 for name in CAMERAS}
        self.rejected = {name: 0 for name in CAMERAS}
        self.packets = 0

    def reject(self, name, error):
        self.errors[name] = str(error)[:300]
        self.rejected[name] += 1

    def accept(self, name, stamp, image, metadata=None, wall=None):
        import cv2
        import numpy as np
        wall = time.time() if wall is None else wall
        try:
            if not isinstance(stamp, (int, float)) or not math.isfinite(stamp) or stamp <= 0:
                raise ValueError("源 header.stamp 必须是有效的 Unix 时间，不能为零")
            if not -.5 <= wall-stamp <= self.config["max_age_seconds"]:
                raise ValueError("源时间戳过期或与工作站时钟未同步")
            if stamp <= self.frames.get(name, {}).get("stamp", 0):
                raise ValueError("源 header.stamp 重复或回退，未刷新帧状态")
            if image is None or image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
                raise ValueError("图像必须能够解码为 8 位三通道彩色图")
            h, w = image.shape[:2]
            if h < 1 or w < 1 or h*w > 16*1024*1024:
                raise ValueError("图像尺寸超限")
            target_w, target_h = self.config["width"], self.config["height"]
            if (w, h) != (target_w, target_h):
                policy = self.config["resize_mode"]
                if policy == "reject":
                    raise ValueError(f"图像尺寸应为 {target_w}×{target_h}，实际 {w}×{h}")
                if policy == "stretch":
                    image = cv2.resize(image, (target_w, target_h))
                else:
                    ratio = min(target_w/w, target_h/h)
                    rw, rh = max(1, round(w*ratio)), max(1, round(h*ratio))
                    resized = cv2.resize(image, (rw, rh))
                    image = np.zeros((target_h, target_w, 3), np.uint8)
                    x, y = (target_w-rw)//2, (target_h-rh)//2
                    image[y:y+rh, x:x+rw] = resized
            ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, self.config["jpeg_quality"]])
            if not ok:
                raise ValueError("JPEG 编码失败")
            self.frames[name] = {"stamp": stamp, "jpeg": encoded.tobytes(), "received_at": now(),
                                 "input_width": w, "input_height": h, **(metadata or {})}
            self.counts[name] += 1
            self.errors.pop(name, None)
            return True
        except Exception as exc:
            self.reject(name, exc)
            return False

    def packet(self, wall=None):
        wall = time.time() if wall is None else wall
        live = {name: row for name, row in self.frames.items()
                if -.5 <= wall-row["stamp"] <= self.config["max_age_seconds"]}
        changed = {name: row for name, row in live.items() if row["stamp"] > self.last_sent.get(name, 0)}
        complete = len(live) == 3
        if complete:
            # Do not label three independently received but skewed frames synchronized.
            if len(changed) != 3:
                return None
            if max(r["stamp"] for r in live.values())-min(r["stamp"] for r in live.values()) > self.config["max_skew_seconds"]:
                self.errors["synchronization"] = "三路源时间戳之差超过配置上限"
                return None
            selected = live
            self.errors.pop("synchronization", None)
        else:
            # Keep remaining live views visible; missing views are absent, never fabricated.
            selected = changed
        if not selected:
            return None
        self.last_sent.update({name: row["stamp"] for name, row in selected.items()})
        self.packets += 1
        return {"timestamps": {self.keys[name]: row["stamp"] for name, row in selected.items()},
                "images": {self.keys[name]: row["jpeg"] for name, row in selected.items()},
                "source": {"transport": "ros2", "domain_id": self.config["domain_id"],
                           "synchronized": complete, "views": {name: {k: v for k, v in row.items() if k != "jpeg"} for name, row in selected.items()}}}

    def status(self):
        wall = time.time()
        views = {}
        for name in CAMERAS:
            row = self.frames.get(name, {})
            live = bool(row and -.5 <= wall-row["stamp"] <= self.config["max_age_seconds"])
            views[name] = {"topic": self.config["topics"][name]["topic"], "live": live,
                           "frames": self.counts[name], "rejected": self.rejected[name],
                           "source_timestamp": row.get("stamp"), "received_at": row.get("received_at")}
        return {"views": views, "errors": dict(self.errors), "packets": self.packets}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    config = read_json(args.config)
    settings = validate_ros2_config(config["ros2_camera"])
    os.environ["ROS_DOMAIN_ID"] = str(settings["domain_id"])
    os.environ["RMW_IMPLEMENTATION"] = settings["rmw"]
    os.environ["ROS_LOCALHOST_ONLY"] = "1" if settings["localhost_only"] else "0"
    import cv2
    import msgpack
    import numpy as np
    import rclpy
    from cv_bridge import CvBridge
    from rclpy.context import Context
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
    from sensor_msgs.msg import Image, CompressedImage
    import zmq

    frames = CameraFrames(settings, config["camera_keys"])
    bridge = CvBridge()
    args.directory.mkdir(parents=True, exist_ok=True)
    zmq_context = zmq.Context()
    pub = zmq_context.socket(zmq.PUB)
    pub.setsockopt(zmq.LINGER, 0)
    pub.setsockopt(zmq.SNDHWM, 2)
    context = Context()
    node = None
    executor = None
    stopping = False

    def write_status(state, error=None):
        row = {**frames.status(), "state": state, "domain_id": settings["domain_id"],
               "endpoint": config["camera_endpoint"], "worker_version": config["_worker_version"],
               "heartbeat_at": now(), "pid": os.getpid()}
        if error:
            row["error"] = str(error)[:400]
        atomic_json(args.directory/"status.json", row)

    def callback(name, msg):
        try:
            stamp = msg.header.stamp.sec+msg.header.stamp.nanosec/1e9
            if isinstance(msg, Image):
                if len(msg.data) > 64*1024*1024 or msg.width*msg.height > 16*1024*1024:
                    raise ValueError("ROS 图像消息过大")
                image = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
                encoding = msg.encoding
            else:
                if len(msg.data) > 32*1024*1024 or "compressedDepth" in msg.format:
                    raise ValueError("仅支持大小受限的彩色压缩图像")
                image = cv2.imdecode(np.frombuffer(msg.data, dtype=np.uint8), cv2.IMREAD_COLOR)
                encoding = msg.format
            frames.accept(name, stamp, image, {"encoding": encoding, "frame_id": msg.header.frame_id})
        except Exception as exc:
            frames.reject(name, exc)

    def publish():
        packet = frames.packet()
        if packet:
            try:
                pub.send(msgpack.packb(packet, use_bin_type=True), flags=zmq.NOBLOCK)
            except zmq.Again:
                pass

    def stop(*_):
        nonlocal stopping
        stopping = True

    try:
        pub.bind(config["camera_endpoint"])
        rclpy.init(context=context, domain_id=settings["domain_id"])
        node = Node("robot_station_camera_bridge", context=context,
                    parameter_overrides=[], automatically_declare_parameters_from_overrides=False)
        executor = SingleThreadedExecutor(context=context)
        executor.add_node(node)
        for name, row in settings["topics"].items():
            qos = QoSProfile(depth=row["depth"], history=HistoryPolicy.KEEP_LAST,
                             reliability=ReliabilityPolicy.RELIABLE if row["reliability"] == "reliable" else ReliabilityPolicy.BEST_EFFORT,
                             durability=DurabilityPolicy.VOLATILE)
            kind = Image if row["message_type"] == "sensor_msgs/msg/Image" else CompressedImage
            node.create_subscription(kind, row["topic"], lambda msg, name=name: callback(name, msg), qos)
        node.create_timer(1/settings["fps"], publish)
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, stop)
        print(json.dumps({"state": "waiting", "domain_id": settings["domain_id"],
                          "endpoint": config["camera_endpoint"], "topics": settings["topics"]}, ensure_ascii=False), flush=True)
        last_status = 0.
        while not stopping and context.ok():
            executor.spin_once(timeout_sec=.05)
            if time.monotonic()-last_status >= .25:
                state = "streaming" if all(v["live"] for v in frames.status()["views"].values()) and "synchronization" not in frames.errors else "waiting"
                write_status(state)
                last_status = time.monotonic()
        write_status("stopped")
    except Exception as exc:
        write_status("failed", exc)
        print(f"Camera bridge failed: {exc}", flush=True)
        raise
    finally:
        if executor is not None:
            executor.shutdown()
        if node is not None:
            node.destroy_node()
        if context.ok():
            context.shutdown()
        pub.close()
        zmq_context.term()


if __name__ == "__main__":
    main()
