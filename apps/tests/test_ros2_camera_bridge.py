import copy
import unittest
import numpy as np

from ros2_camera_bridge import CameraFrames, default_ros2_config, validate_ros2_config

KEYS = {"head": "ego_view", "left_wrist": "left_wrist", "right_wrist": "right_wrist"}


class CameraFrameTests(unittest.TestCase):
    def setUp(self):
        self.frames = CameraFrames(default_ros2_config(), KEYS)
        self.image = np.zeros((480, 640, 3), np.uint8)

    def test_source_clock_not_rewritten_and_frozen_frames_expire(self):
        self.assertTrue(self.frames.accept("head", 100., self.image, wall=100.1))
        for stamp in [100., 99.9, 0., 10., float("nan"), 102.]:
            self.assertFalse(self.frames.accept("head", stamp, self.image, wall=100.2))
        self.assertEqual(self.frames.frames["head"]["stamp"], 100.)
        self.assertIsNone(self.frames.packet(wall=101.))
        self.assertEqual(self.frames.counts["head"], 1)

    def test_packet_keys_jpeg_color_synchronization_and_no_repeated_publish(self):
        import cv2
        for i, name in enumerate(KEYS):
            image = self.image.copy();image[:, :, i] = 180
            self.assertTrue(self.frames.accept(name, 100.+i*.01, image, wall=100.1))
        packet = self.frames.packet(wall=100.2)
        self.assertEqual(set(packet["images"]), set(KEYS.values()))
        self.assertTrue(packet["source"]["synchronized"])
        for i, value in enumerate(packet["images"].values()):
            image = cv2.imdecode(np.frombuffer(value, np.uint8), cv2.IMREAD_COLOR)
            self.assertEqual(int(image.mean(axis=(0, 1)).argmax()), i)
        self.assertIsNone(self.frames.packet(wall=100.25))

    def test_skew_is_rejected_and_missing_view_is_never_fabricated(self):
        for name, stamp in zip(KEYS, [100., 100., 100.3]):self.frames.accept(name, stamp, self.image, wall=100.3)
        self.assertIsNone(self.frames.packet(wall=100.35))
        self.assertIn("synchronization", self.frames.errors)
        self.frames.accept("right_wrist", 100.7, self.image, wall=100.7)
        packet = self.frames.packet(wall=100.8)
        self.assertEqual(set(packet["images"]), {"right_wrist"})
        self.assertFalse(packet["source"]["synchronized"])

    def test_resize_is_explicit_and_letterbox_preserves_geometry(self):
        import cv2
        image = np.full((200, 200, 3), 190, np.uint8)
        self.assertTrue(self.frames.accept("head", 100., image, wall=100.))
        decoded = cv2.imdecode(np.frombuffer(self.frames.frames["head"]["jpeg"], np.uint8), cv2.IMREAD_COLOR)
        self.assertEqual(decoded.shape, (480, 640, 3))
        self.assertLess(decoded[:, 0].mean(), 5)
        self.frames.config["resize_mode"] = "reject"
        self.assertFalse(self.frames.accept("head", 100.1, image, wall=100.1))

    def test_config_checks_domain_unique_topics_message_types_and_qos(self):
        settings = default_ros2_config()
        self.assertEqual(validate_ros2_config(settings)["domain_id"], 99)
        mutations = [lambda c:c.update(domain_id=True), lambda c:c.update(fps=0), lambda c:c.update(unknown=1),
                     lambda c:c["topics"]["head"].update(topic="bad topic"),
                     lambda c:c["topics"]["head"].update(message_type="std_msgs/msg/String"),
                     lambda c:c["topics"]["head"].update(reliability="unknown"),
                     lambda c:c["topics"]["head"].update(topic=c["topics"]["left_wrist"]["topic"])]
        for mutate in mutations:
            bad = copy.deepcopy(settings);mutate(bad)
            with self.assertRaises(ValueError):validate_ros2_config(bad)


if __name__ == "__main__":unittest.main()
