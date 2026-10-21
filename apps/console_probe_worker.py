"""Passive DDS/ZMQ/XRoboToolkit readers. This module has no command publisher."""
from __future__ import annotations

import argparse
import base64
from collections import deque
import json
from pathlib import Path
import signal
import socket
import sys
import threading
import time

from console_support import atomic_json, finite, now, read_json

# Unitree SDK2 example/g1/low_level/g1_low_level_example.py: G1JointIndex.
# This explicit hardware mapping is independent of the web URDF traversal order.
MOTOR_NAMES = [f"{side}_{name}_joint" for side in ("left", "right")
               for name in ("hip_pitch", "hip_roll", "hip_yaw", "knee", "ankle_pitch", "ankle_roll")]
MOTOR_NAMES += ["waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint"]
MOTOR_NAMES += [f"{side}_{name}_joint" for side in ("left", "right")
                for name in ("shoulder_pitch", "shoulder_roll", "shoulder_yaw", "elbow", "wrist_roll", "wrist_pitch", "wrist_yaw")]


class PassiveProbe:
    def __init__(self, root, directory, config, mode):
        self.root, self.directory, self.config, self.mode = Path(root), Path(directory), config, mode
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.data = {"mode": mode, "worker_version":config.get("_worker_version"), "robot": {}, "battery": {}, "pico": {}, "controller": {}, "cameras": {}, "errors": {}}
        self.previous = {}

    def update(self, key, value):
        with self.lock:
            self.data[key] = value

    def error(self, key, error):
        with self.lock:
            self.data["errors"][key] = str(error)[:400]

    def run_dds(self):
        while not self.stop.is_set():
            if self.mode=="real":
                try:carrier=(Path('/sys/class/net')/self.config['interface']/'carrier').read_text().strip()
                except OSError:carrier='0'
                if carrier!='1':
                    self.error('dds','等待机器人网卡接线并获得链路')
                    self.stop.wait(1)
                    continue
            self._run_dds_once()
            self.stop.wait(2)

    def _run_dds_once(self):
        try:
            from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelSubscriber
            from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_, BmsState_
            interface = self.config["interface"]
            if not Path("/sys/class/net", interface).exists():
                raise RuntimeError(f"网卡不存在：{interface}")
            ChannelFactoryInitialize(self.config.get("dds_domain", 0), interface)
            last_tick = [None]

            def lowstate(msg):
                if msg.tick == last_tick[0]:
                    return
                last_tick[0] = msg.tick
                rows = []
                for name, motor in zip(MOTOR_NAMES, msg.motor_state):
                    if not finite(motor.q):
                        return
                    temp = motor.temperature
                    row = {"name": name, "position_rad": float(motor.q)}
                    for key, value in [("velocity_rad_s", motor.dq), ("effort_nm", motor.tau_est),
                                       ("temperature_c", max(temp) if isinstance(temp, (tuple, list)) else temp)]:
                        if finite(value):
                            row[key] = float(value)
                    rows.append(row)
                if len(rows) == 29:
                    self.update("robot", {"connected": True, "observed_at": now(), "joints": rows,
                                          "source": f"DDS {interface}:rt/lowstate", "mode": "UNKNOWN", "tick": int(msg.tick), "mode_machine": int(msg.mode_machine), "mode_pr": int(msg.mode_pr)})

            subscribers = []
            sub = ChannelSubscriber("rt/lowstate", LowState_)
            sub.Init(lowstate, 10)
            subscribers.append(sub)
            for topic in self.config.get("bms_topics", ["rt/bmsstate", "rt/lf/bmsstate"]):
                def bms(msg, source=topic):
                    percent = getattr(msg, "soc", None)
                    if finite(percent) and 0 <= percent <= 100:
                        self.update("battery", {"percent": float(percent), "observed_at": now(),
                                                "source": f"DDS {interface}:{source}", "current_a": float(msg.current) / 1000})
                sub = ChannelSubscriber(topic, BmsState_)
                sub.Init(bms, 10)
                subscribers.append(sub)
            self.stop.wait()
            for sub in subscribers:
                sub.Close()
        except Exception as exc:
            self.error("dds", exc)

    def run_state(self):
        try:
            import msgpack
            import zmq
            from sonic_feedback import SonicFeedback
            from gear_sonic.data.features_sonic_vla import get_g1_robot_model
            names = list(get_g1_robot_model().supplemental_info.body_actuated_joints)
            tracker = SonicFeedback(max_age=.5)
            context = zmq.Context()
            sub = context.socket(zmq.SUB)
            sub.setsockopt(zmq.LINGER, 0)
            sub.setsockopt(zmq.RCVHWM, 5)
            for topic in (b'g1_debug', b'robot_config'):
                sub.setsockopt(zmq.SUBSCRIBE, topic)
            sub.connect(self.config['state_endpoint'])
            try:
                while not self.stop.is_set():
                    if sub.poll(100):
                        raw = sub.recv()
                        try:
                            if len(raw) > 2 * 1024 * 1024:
                                raise ValueError('SONIC反馈消息过大')
                            if raw.startswith(b'robot_config'):
                                message = msgpack.unpackb(raw[len(b'robot_config'):], raw=False)
                                tracker.configuration(message)
                                self.update('robot_config', message)
                            elif raw.startswith(b'g1_debug'):
                                message = msgpack.unpackb(raw[len(b'g1_debug'):], raw=False)
                                accepted = tracker.feed(message)
                                if accepted and self.mode == 'sim' and len(names) == 29:
                                    self.update('robot', {'connected': True, 'observed_at': tracker.observed_at,
                                        'mode': 'SONIC', 'source': 'SONIC g1_debug / simulation / measured',
                                        'joints': [{'name': name, 'position_rad': value} for name, value in zip(names, tracker.values)]})
                        except Exception as exc:
                            self.error('state_message', exc)
                    status = tracker.status()
                    self.update('controller', {**status, 'state': 'running' if status['valid'] else 'ready' if status['configuration_age_seconds'] is not None and status['configuration_age_seconds'] < 3 else 'offline',
                        'source': self.config['state_endpoint']})
            finally:
                sub.close()
                context.term()
        except Exception as exc:
            self.error('state', exc)

    def run_pico(self):
        # Device clock must advance; repeated SDK arrays do not count as new tracking.
        while not self.stop.is_set():
            try:
                with socket.create_connection(("127.0.0.1", 60061), timeout=.3):
                    pass
                import numpy as np
                import xrobotoolkit_sdk as xrt
                xrt.init()
                previous = None
                consecutive = 0
                while not self.stop.wait(.1):
                    stamp = int(xrt.get_body_timestamp_ns())
                    if not xrt.is_body_data_available() or stamp <= 0 or stamp == previous:
                        continue
                    if previous is not None and stamp < previous:
                        consecutive=0
                        self.update("pico", {"body_ready":False,"observed_at":now(),"source":"XRoboToolkit SDK","message":"身体追踪时钟重置，等待连续新帧"})
                    previous = stamp
                    consecutive += 1
                    poses = np.asarray(xrt.get_body_joints_pose())
                    if poses.shape != (24,7) or not np.isfinite(poses).all():
                        continue
                    norms=np.linalg.norm(poses[:,3:7],axis=1)
                    if consecutive<2 or not ((norms>.5)&(norms<1.5)).all():continue
                    self.update("pico", {"body_ready": True, "observed_at": now(), "body_timestamp_ns": stamp,
                                         "device_timestamp_ns":int(xrt.get_time_stamp_ns()),
                                         "source": "XRoboToolkit SDK", "calibration_confirmed": self.config.get("pico_calibration_confirmed", False)})
            except Exception as exc:
                self.error("pico", exc)
                self.stop.wait(5)

    def run_cameras(self):
        try:
            import cv2
            import msgpack
            import msgpack_numpy
            import numpy as np
            import zmq
            context = zmq.Context()
            sub = context.socket(zmq.SUB)
            sub.setsockopt(zmq.SUBSCRIBE, b"")
            sub.setsockopt(zmq.LINGER, 0)
            sub.setsockopt(zmq.CONFLATE, 1)
            sub.connect(self.config["camera_endpoint"])
            histories = {name: deque(maxlen=30) for name in self.config["camera_keys"]}
            while not self.stop.is_set():
                if not sub.poll(100):
                    continue
                try:
                    raw = sub.recv()
                    if len(raw) > 32 * 1024 * 1024:
                        raise ValueError("相机消息过大")
                    packet = msgpack.unpackb(raw, raw=False, object_hook=msgpack_numpy.decode)
                    with self.lock:self.data['camera_source_keys']=list(packet.get('images',{}))
                    for camera, key in self.config["camera_keys"].items():
                        value = packet.get("images", {}).get(key)
                        timestamp = packet.get("timestamps", {}).get(key)
                        if value is None or not finite(timestamp) or timestamp <= self.previous.get(camera,0):
                            continue
                        if not -.5 <= time.time() - timestamp <= 5:
                            self.error(camera, "相机源时间戳过期或时钟未同步")
                            continue
                        if isinstance(value, str):
                            value = base64.b64decode(value, validate=True)
                        if isinstance(value, bytes):
                            image = cv2.imdecode(np.frombuffer(value, dtype=np.uint8), cv2.IMREAD_COLOR)
                        else:
                            image = np.asarray(value)[..., ::-1]
                        if image is None or image.ndim != 3 or image.shape[2] != 3:
                            raise ValueError("相机帧无法解码为 RGB")
                        ok, jpeg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if not ok:
                            raise ValueError("相机 JPEG 编码失败")
                        self.previous[camera] = timestamp
                        path = self.directory / (camera + ".jpg")
                        temp = path.with_suffix(".tmp")
                        temp.write_bytes(jpeg.tobytes())
                        temp.replace(path)
                        history = histories[camera]
                        history.append(timestamp)
                        fps = (len(history)-1)/(history[-1]-history[0]) if len(history)>1 and history[-1]>history[0] else 0
                        with self.lock:
                            self.data["cameras"][camera] = {"id": camera, "state": "streaming", "observed_at": now(),
                                "source_timestamp": timestamp, "source": key, "fps": round(fps, 1),
                                "latency_ms": max(0, (time.time()-timestamp)*1000), "transport": "mjpeg",
                                "url": f"/api/v1/console/cameras/{camera}/stream?mode={self.mode}"}
                except Exception as exc:
                    self.error("camera_message", exc)
            sub.close()
            context.term()
        except Exception as exc:
            self.error("cameras", exc)

    def run(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        for target in (self.run_dds, self.run_state, self.run_cameras, self.run_pico):
            threading.Thread(target=target, daemon=True).start()
        while not self.stop.wait(.25):
            with self.lock:
                atomic_json(self.directory / "status.json", {**self.data, "heartbeat_at": now()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sonic-root", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--mode", choices=["real", "sim"], required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.sonic_root))
    probe = PassiveProbe(args.sonic_root, args.directory, read_json(args.config), args.mode)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: probe.stop.set())
    probe.run()


if __name__ == "__main__":
    main()
