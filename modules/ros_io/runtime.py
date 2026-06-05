import threading

from modules.logger import get_logger
from modules.ros_io.serializers import import_message_class, import_service_class


LOGGER = get_logger()


class RosRuntimeError(RuntimeError):
    pass


class RosRuntime:
    _context_lock = threading.RLock()
    _managed_context = False
    _active_managed_runtimes = 0

    def __init__(self, node_name="robot_station_bridge", num_threads=2):
        self.node_name = node_name
        self.num_threads = max(1, int(num_threads))
        self._lock = threading.RLock()
        self._rclpy = None
        self._executor = None
        self._node = None
        self._thread = None
        self._owns_context = False
        self._subscriptions = {}
        self._publishers = {}
        self._clients = {}

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
            with RosRuntime._context_lock:
                if not rclpy.ok():
                    rclpy.init(args=None)
                    RosRuntime._managed_context = True
                if RosRuntime._managed_context:
                    RosRuntime._active_managed_runtimes += 1
                    self._owns_context = True

            self._node = rclpy.create_node(self.node_name)
            self._executor = self._executor_class(num_threads=self.num_threads)
            self._executor.add_node(self._node)
            self._thread = threading.Thread(
                target=self._spin,
                name=f"{self.node_name}_executor",
                daemon=True,
            )
            self._thread.start()
            LOGGER.info("ROS runtime started with node %s using %d executor thread(s)", self.node_name, self.num_threads)

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

    def get_client(self, key, service_type, service_name):
        with self._lock:
            if key in self._clients:
                return self._clients[key]
            service_class = import_service_class(service_type)
            self.ensure_started()
            client = self._node.create_client(service_class, service_name)
            self._clients[key] = client
            LOGGER.info("ROS service client registered: %s -> %s", key, service_name)
            return client

    def call_service(self, key, service_type, service_name, request, timeout_sec=5.0, wait_timeout_sec=0.2):
        client = self.get_client(key, service_type, service_name)
        if not client.wait_for_service(timeout_sec=max(0.0, float(wait_timeout_sec))):
            raise RosRuntimeError(f"ROS service is not available: {service_name}")

        done = threading.Event()
        future = client.call_async(request)
        future.add_done_callback(lambda _: done.set())
        if not done.wait(max(0.1, float(timeout_sec))):
            if hasattr(future, "cancel"):
                future.cancel()
            raise RosRuntimeError(f"Timed out waiting for ROS service response: {service_name}")

        try:
            return future.result()
        except Exception as exc:
            raise RosRuntimeError(f"ROS service call failed: {service_name}: {exc}") from exc

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
            if self._rclpy is not None and self._owns_context:
                with RosRuntime._context_lock:
                    RosRuntime._active_managed_runtimes = max(0, RosRuntime._active_managed_runtimes - 1)
                    should_shutdown = (
                        RosRuntime._active_managed_runtimes == 0
                        and RosRuntime._managed_context
                        and self._rclpy.ok()
                    )
                    if should_shutdown:
                        try:
                            self._rclpy.shutdown()
                            RosRuntime._managed_context = False
                        except Exception:
                            LOGGER.exception("Failed to shut down rclpy")
                self._owns_context = False

            self._executor = None
            self._node = None
            self._thread = None
            self._subscriptions.clear()
            self._publishers.clear()
            self._clients.clear()
