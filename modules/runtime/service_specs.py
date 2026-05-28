from dataclasses import asdict, dataclass, field
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ManagedServiceSpec:
    key: str
    name: str
    command: tuple[str, ...]
    setup_scripts: tuple[str, ...] = field(default_factory=tuple)
    cleanup_process_patterns: tuple[str, ...] = field(default_factory=tuple)
    cwd: str = "."
    shutdown_timeout_sec: float = 6.0
    startup_grace_sec: float = 0.8
    description: str = ""

    def to_dict(self):
        payload = asdict(self)
        payload["command"] = list(self.command)
        payload["setupScripts"] = payload.pop("setup_scripts")
        payload["cleanupProcessPatterns"] = payload.pop("cleanup_process_patterns")
        payload["shutdownTimeoutSec"] = payload.pop("shutdown_timeout_sec")
        payload["startupGraceSec"] = payload.pop("startup_grace_sec")
        return payload


def default_service_specs():
    ros_distro = os.environ.get("ROS_DISTRO", "humble")
    piper_joint_speed_percent = os.environ.get("PIPER_JOINT_SPEED_PERCENT", "10")
    piper_install = ROOT_DIR / "ros_packages" / "control" / "piper" / "install" / "setup.bash"
    lifting_install = ROOT_DIR / "ros_packages" / "control" / "lifting" / "install" / "setup.bash"
    camera_ws = ROOT_DIR / "ros_packages" / "sensors" / "camera" / "orbbec"
    camera_install = camera_ws / "install" / "setup.bash"
    camera_start_script = camera_ws / "scripts" / "start_orbbec_camera.sh"
    lidar_ws = ROOT_DIR / "ros_packages" / "sensors" / "lidar"
    lidar_install = lidar_ws / "install" / "setup.bash"
    lidar_config = lidar_ws / "rslidar_sdk" / "config" / "config.yaml"
    lifting_motor_id = os.environ.get("LIFTING_MOTOR_ID", "1")
    lifting_executable = os.environ.get("LIFTING_SERVICE_EXECUTABLE", "service_850pro")
    return {
        "piper": ManagedServiceSpec(
            key="piper",
            name="Piper ROS control",
            command=(
                "ros2",
                "launch",
                "piper",
                "start_double_piper.launch.py",
                "can_left_port:=can_left",
                "can_right_port:=can_right",
                "auto_enable:=false",
                f"joint_speed_percent:={piper_joint_speed_percent}",
            ),
            setup_scripts=(
                f"/opt/ros/{ros_distro}/setup.bash",
                str(piper_install),
            ),
            cleanup_process_patterns=(
                "start_double_piper.launch.py",
                "start_two_piper.launch.py",
                "start_single_piper.launch.py",
                "start_single_piper_rviz.launch.py",
                "piper_single_ctrl",
                "piper_joint_smoother",
                "piper_ms_ctrl",
            ),
            cwd=str(ROOT_DIR),
            description="Launch the dual-arm Piper ROS control nodes.",
        ),
        "lifting": ManagedServiceSpec(
            key="lifting",
            name="Lifting axis ROS control",
            command=(
                "ros2",
                "run",
                "lifting_ctrl_ros2_pkg",
                lifting_executable,
                "--id",
                str(lifting_motor_id),
            ),
            setup_scripts=(
                f"/opt/ros/{ros_distro}/setup.bash",
                str(lifting_install),
            ),
            cleanup_process_patterns=(
                "lifting_ctrl_ros2_pkg",
                "service_830abs",
                "service_850pro",
                "lifting_ctrl_server_node",
                "lifting_ctrl_server_node_830abs",
                "lifting_ctrl_server_node_850pro",
            ),
            cwd=str(ROOT_DIR),
            shutdown_timeout_sec=8.0,
            startup_grace_sec=0.8,
            description="Launch the lifting axis motor service node.",
        ),
        "camera": ManagedServiceSpec(
            key="camera",
            name="Orbbec camera ROS",
            command=(
                str(camera_start_script),
            ),
            setup_scripts=(
                f"/opt/ros/{ros_distro}/setup.bash",
                str(camera_install),
            ),
            cleanup_process_patterns=(
                "start_orbbec_camera.sh",
                "ros2 launch orbbec_camera",
                "orbbec_camera_node",
                "camera_container",
            ),
            cwd=str(camera_ws),
            shutdown_timeout_sec=8.0,
            startup_grace_sec=0.8,
            description="Launch the Orbbec multi-camera ROS nodes.",
        ),
        "lidar": ManagedServiceSpec(
            key="lidar",
            name="RoboSense LiDAR ROS",
            command=(
                "ros2",
                "run",
                "rslidar_sdk",
                "rslidar_sdk_node",
                "--ros-args",
                "-p",
                f"config_path:={lidar_config}",
            ),
            setup_scripts=(
                f"/opt/ros/{ros_distro}/setup.bash",
                str(lidar_install),
            ),
            cleanup_process_patterns=(
                "rslidar_sdk_node",
                "ros2 run rslidar_sdk",
            ),
            cwd=str(lidar_ws),
            shutdown_timeout_sec=8.0,
            startup_grace_sec=0.8,
            description="Launch the RoboSense LiDAR driver without RViz.",
        ),
    }
