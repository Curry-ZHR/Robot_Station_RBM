"""Synthetic ROS image publisher. Test namespaces only; no robot subscriptions."""
import argparse
import json
import os
from pathlib import Path
import signal
import time


def main():
    parser = argparse.ArgumentParser()
    for name in ("config", "ready", "control"):
        parser.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    settings = config["ros2_camera"]
    os.environ.update(ROS_DOMAIN_ID=str(settings["domain_id"]), RMW_IMPLEMENTATION=settings["rmw"], ROS_LOCALHOST_ONLY="1")
    import cv2
    import numpy as np
    import rclpy
    from rclpy.context import Context
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image, CompressedImage
    context = Context()
    rclpy.init(context=context, domain_id=settings["domain_id"])
    node = Node("robot_station_synthetic_camera", context=context)
    executor = SingleThreadedExecutor(context=context)
    executor.add_node(node)
    pubs, arrays, stamps = {}, {}, {}
    for index, (name, row) in enumerate(settings["topics"].items()):
        kind = Image if row["message_type"].endswith("/Image") else CompressedImage
        pubs[name] = node.create_publisher(kind, row["topic"], qos_profile_sensor_data)
        image = np.zeros((480, 640, 3), np.uint8)
        image[:, :, index] = 190
        cv2.putText(image, "SYNTHETIC / "+name.upper(), (20, 55), cv2.FONT_HERSHEY_SIMPLEX, .7, (255, 255, 255), 2)
        arrays[name] = image
    running = True

    def stop(*_):
        nonlocal running
        running = False

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, stop)
    args.ready.write_text(json.dumps({"domain_id": settings["domain_id"], "pid": os.getpid()}))
    try:
        while running:
            try:control = json.loads(args.control.read_text())
            except (OSError, ValueError):control = {}
            for index, (name, row) in enumerate(settings["topics"].items()):
                if control.get("disable") or name in control.get("disabled", []):
                    continue
                if name not in control.get("frozen", []) or name not in stamps:
                    stamps[name] = time.time_ns()
                image = arrays[name]
                if row["message_type"].endswith("/CompressedImage"):
                    msg = CompressedImage()
                    msg.format = "jpeg"
                    msg.data = cv2.imencode(".jpg", image)[1].tobytes()
                else:
                    msg = Image()
                    msg.width, msg.height = 640, 480
                    msg.encoding = "rgb8" if index == 0 else "bgr8"
                    msg.is_bigendian = 0
                    msg.step = 640*3
                    msg.data = (image[..., ::-1].copy() if index == 0 else image).tobytes()
                msg.header.stamp.sec, msg.header.stamp.nanosec = divmod(stamps[name], 1_000_000_000)
                msg.header.frame_id = "synthetic_"+name
                pubs[name].publish(msg)
            executor.spin_once(timeout_sec=.02)
            time.sleep(.02)
    finally:
        executor.shutdown()
        node.destroy_node()
        context.shutdown()


if __name__ == "__main__":
    main()
