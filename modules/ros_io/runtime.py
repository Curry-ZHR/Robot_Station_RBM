import threading

from modules.logger import get_logger
from modules.ros_io.serializers import import_message_class


LOGGER = get_logger()


class RosRuntimeError(RuntimeError):
    pass


class RosRuntime:
    def __init__(self, node_name="robot_station_bridge"):
        self.node_name = node_name
        self._lock = threading.RLock()
        self._rclpy = None
        self._executor = None
        self._node = None
        self._thread = None
        self._owns_context = False
        self._subscriptions = {}
        self._publishers = {}

    def _import_rclpy(self):
        if self._rclpy is not None:
            return self._rclpy
        try:
            import rclpy
            from rclpy.executors import MultiThreadedExecutor
        except ImportError as exc:
            raise RosRuntimeError(
                "Python package rclpy is not available. Source a ROS2 environment before starting Robot Station."
            ) from exc
        self._rclpy = rclpy
        self._executor_class = MultiThreadedExecutor
        return self._rclpy

    def ensure_started(self):
        with self._lock:
            if self._node is not None and self._thread is not None and self._thread.is_alive():
                return

            rclpy = self._import_rclpy()
            if not rclpy.ok():
                rclpy.init(args=None)
                self._owns_context = True

            self._node = rclpy.create_node(self.node_name)
            self._executor = self._executor_class(num_threads=2)
            self._executor.add_node(self._node)
            self._thread = threading.Thread(
                target=self._spin,
                name=f"{self.node_name}_executor",
                daemon=True,
            )
            self._thread.start()
            LOGGER.info("ROS runtime started with node %s", self.node_name)

    def _spin(self):
        try:
            self._executor.spin()
        except Exception:
            LOGGER.exception("ROS runtime executor stopped unexpectedly")

    def now_msg(self):
        self.ensure_started()
        return self._node.get_clock().now().to_msg()

    def create_subscription(self, key, message_type, topic, callback, qos_depth=10):
        with self._lock:
            if key in self._subscriptions:
                return self._subscriptions[key]
            message_class = import_message_class(message_type)
            self.ensure_started()
            subscription = self._node.create_subscription(
                message_class,
                topic,
                callback,
                int(qos_depth),
            )
            self._subscriptions[key] = subscription
            LOGGER.info("ROS subscription registered: %s -> %s", key, topic)
            return subscription

    def get_publisher(self, key, message_type, topic, qos_depth=10):
        with self._lock:
            if key in self._publishers:
                return self._publishers[key]
            message_class = import_message_class(message_type)
            self.ensure_started()
            publisher = self._node.create_publisher(message_class, topic, int(qos_depth))
            self._publishers[key] = publisher
            LOGGER.info("ROS publisher registered: %s -> %s", key, topic)
            return publisher

    def shutdown(self):
        with self._lock:
            if self._executor is not None:
                try:
                    self._executor.shutdown(timeout_sec=1.0)
                except Exception:
                    LOGGER.exception("Failed to shut down ROS executor")
            if self._node is not None:
                try:
                    self._node.destroy_node()
                except Exception:
                    LOGGER.exception("Failed to destroy ROS bridge node")
            if self._rclpy is not None and self._owns_context and self._rclpy.ok():
                try:
                    self._rclpy.shutdown()
                except Exception:
                    LOGGER.exception("Failed to shut down rclpy")

            self._executor = None
            self._node = None
            self._thread = None
            self._subscriptions.clear()
            self._publishers.clear()

