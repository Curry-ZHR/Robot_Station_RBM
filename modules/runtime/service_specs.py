from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
import shlex

from modules.drivers.can.can_interface import DEFAULT_CHASSIS_CAN_TARGETS, load_chassis_can_config


ROOT_DIR = Path(__file__).resolve().parents[2]
STATIC_TRANSFORMS_CONFIG = ROOT_DIR / "config" / "static_transforms.json"


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


def _default_chassis_can_port():
    ports = load_chassis_can_config().get("ports", {})
    for target in DEFAULT_CHASSIS_CAN_TARGETS:
        if target in ports:
            return target
    return next(iter(ports), "can_chassis")


def _coerce_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off", ""}:
        return False
    return default


def _number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _format_number(value):
    return f"{float(value):.12g}"


def _frame_name(value, field):
    text = str(value or "").strip().lstrip("/")
    if not text:
        raise ValueError(f"Static transform {field} must be a non-empty frame name.")
    return text


def _triplet(raw, names):
    if isinstance(raw, dict):
        return tuple(_number(raw.get(name, 0.0)) for name in names)
    if isinstance(raw, (list, tuple)) and len(raw) >= 3:
        return tuple(_number(raw[index], 0.0) for index in range(3))
    return (0.0, 0.0, 0.0)


def _node_name(value):
    text = re.sub(r"[^A-Za-z0-9_]", "_", str(value or "").strip())
    text = re.sub(r"_+", "_", text).strip("_")
    if not text:
        text = "transform"
    if not re.match(r"^[A-Za-z_]", text):
        text = f"tf_{text}"
    return f"robot_station_static_tf_{text[:64]}"


def static_transforms_config_path():
    configured = os.environ.get("ROBOT_STATION_STATIC_TRANSFORMS_CONFIG")
    if configured:
        return Path(configured).expanduser()
    return STATIC_TRANSFORMS_CONFIG


def load_static_transform_config(path=None):
    config_path = Path(path).expanduser() if path else static_transforms_config_path()
    if not config_path.exists():
        return {"enabled": False, "transforms": [], "path": str(config_path)}

    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Static transform config must be a JSON object.")

    transforms = payload.get("transforms", [])
    if transforms is None:
        transforms = []
    if not isinstance(transforms, list):
        raise ValueError("Static transform config field transforms must be a list.")

    return {
        "enabled": _coerce_bool(payload.get("enabled"), True),
        "transforms": transforms,
        "path": str(config_path),
    }


def _static_transform_command(transform):
    if not isinstance(transform, dict):
        raise ValueError("Each static transform entry must be a JSON object.")

    parent = _frame_name(
        transform.get("parentFrame") or transform.get("parent_frame") or transform.get("parent"),
        "parentFrame",
    )
    child = _frame_name(
        transform.get("childFrame") or transform.get("child_frame") or transform.get("child"),
        "childFrame",
    )
    name = transform.get("name") or f"{parent}_to_{child}"
    x, y, z = _triplet(transform.get("translation", {}), ("x", "y", "z"))
    roll, pitch, yaw = _triplet(transform.get("rotation", {}), ("roll", "pitch", "yaw"))
    node_name = _node_name(name)

    return (
        "ros2",
        "run",
        "tf2_ros",
        "static_transform_publisher",
        "--x",
        _format_number(x),
        "--y",
        _format_number(y),
        "--z",
        _format_number(z),
        "--roll",
        _format_number(roll),
        "--pitch",
        _format_number(pitch),
        "--yaw",
        _format_number(yaw),
        "--frame-id",
        parent,
        "--child-frame-id",
        child,
        "--ros-args",
        "-r",
        f"__node:={node_name}",
    ), node_name


def static_transform_service_spec(ros_distro=None, config=None):
    ros_distro = ros_distro or os.environ.get("ROS_DISTRO", "humble")
    config = config or load_static_transform_config()
    if not config.get("enabled", True):
        return None

    transform_entries = config.get("transforms", [])
    if not transform_entries:
        return None

    commands = []
    cleanup_patterns = []
    for transform in transform_entries:
        command, node_name = _static_transform_command(transform)
        commands.append(command)
        cleanup_patterns.append(f"__node:={node_name}")

    if len(commands) == 1:
        command = commands[0]
    else:
        shell_lines = ["set -e"]
        shell_lines.extend(f"{shlex.join(entry)} &" for entry in commands)
        shell_lines.append("wait")
        command = ("bash", "-lc", "\n".join(shell_lines))

    return ManagedServiceSpec(
        key="transforms",
        name="Static robot transforms",
        command=command,
        setup_scripts=(f"/opt/ros/{ros_distro}/setup.bash",),
        cleanup_process_patterns=tuple(cleanup_patterns),
        cwd=str(ROOT_DIR),
        shutdown_timeout_sec=4.0,
        startup_grace_sec=0.5,
        description="Publish configured static TF frames for Robot Station.",
    )


def default_service_specs():
    ros_distro = os.environ.get("ROS_DISTRO", "humble")
    piper_joint_speed_percent = os.environ.get("PIPER_JOINT_SPEED_PERCENT", "10")
    piper_install = ROOT_DIR / "ros_packages" / "control" / "piper" / "install" / "setup.bash"
    lifting_install = ROOT_DIR / "ros_packages" / "control" / "lifting" / "install" / "setup.bash"
    chassis_install = ROOT_DIR / "ros_packages" / "control" / "chassis" / "install" / "setup.bash"
    camera_ws = ROOT_DIR / "ros_packages" / "sensors" / "camera" / "orbbec"
    camera_install = camera_ws / "install" / "setup.bash"
    camera_start_script = camera_ws / "scripts" / "start_orbbec_camera.sh"
    lidar_ws = ROOT_DIR / "ros_packages" / "sensors" / "lidar"
    lidar_install = lidar_ws / "install" / "setup.bash"
    lidar_config = lidar_ws / "rslidar_sdk" / "config" / "config.yaml"
    lifting_motor_id = os.environ.get("LIFTING_MOTOR_ID", "1")
    lifting_executable = os.environ.get("LIFTING_SERVICE_EXECUTABLE", "service_850pro")
    chassis_launch_file = os.environ.get("CHASSIS_LAUNCH_FILE", "ranger_mini_v3.launch.py")
    chassis_can_port = os.environ.get("CHASSIS_CAN_PORT", _default_chassis_can_port())
    chassis_robot_model = os.environ.get("CHASSIS_ROBOT_MODEL", "ranger_mini_v3")
    chassis_update_rate = os.environ.get("CHASSIS_UPDATE_RATE", "50")
    chassis_publish_odom_tf = os.environ.get("CHASSIS_PUBLISH_ODOM_TF", "false")
    chassis_smoother_publish_rate_hz = os.environ.get("CHASSIS_SMOOTHER_PUBLISH_RATE_HZ", "50")
    chassis_smoother_linear_accel_mps2 = os.environ.get("CHASSIS_SMOOTHER_LINEAR_ACCEL_MPS2", "0.25")
    chassis_smoother_linear_decel_mps2 = os.environ.get("CHASSIS_SMOOTHER_LINEAR_DECEL_MPS2", "0.60")
    chassis_smoother_angular_accel_rad_s2 = os.environ.get("CHASSIS_SMOOTHER_ANGULAR_ACCEL_RAD_S2", "0.80")
    chassis_smoother_angular_decel_rad_s2 = os.environ.get("CHASSIS_SMOOTHER_ANGULAR_DECEL_RAD_S2", "1.50")
    chassis_smoother_watchdog_timeout_sec = os.environ.get("CHASSIS_SMOOTHER_WATCHDOG_TIMEOUT_SEC", "0.25")
    chassis_smoother_linear_deadband_mps = os.environ.get("CHASSIS_SMOOTHER_LINEAR_DEADBAND_MPS", "0.005")
    chassis_smoother_angular_deadband_rad_s = os.environ.get("CHASSIS_SMOOTHER_ANGULAR_DEADBAND_RAD_S", "0.01")
    chassis_raw_action_topic = os.environ.get("CHASSIS_RAW_ACTION_TOPIC", "/action/chassis")
    chassis_smoothed_action_topic = os.environ.get("CHASSIS_SMOOTHED_ACTION_TOPIC", "/action/chassis_smoothed")
    specs = {
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
        "chassis": ManagedServiceSpec(
            key="chassis",
            name="Ranger Mini chassis ROS control",
            command=(
                "ros2",
                "launch",
                "ranger_base",
                chassis_launch_file,
                f"port_name:={chassis_can_port}",
                f"robot_model:={chassis_robot_model}",
                f"update_rate:={chassis_update_rate}",
                f"publish_odom_tf:={chassis_publish_odom_tf}",
                f"chassis_smoother_publish_rate_hz:={chassis_smoother_publish_rate_hz}",
                f"chassis_smoother_linear_accel_mps2:={chassis_smoother_linear_accel_mps2}",
                f"chassis_smoother_linear_decel_mps2:={chassis_smoother_linear_decel_mps2}",
                f"chassis_smoother_angular_accel_rad_s2:={chassis_smoother_angular_accel_rad_s2}",
                f"chassis_smoother_angular_decel_rad_s2:={chassis_smoother_angular_decel_rad_s2}",
                f"chassis_smoother_watchdog_timeout_sec:={chassis_smoother_watchdog_timeout_sec}",
                f"chassis_smoother_linear_deadband_mps:={chassis_smoother_linear_deadband_mps}",
                f"chassis_smoother_angular_deadband_rad_s:={chassis_smoother_angular_deadband_rad_s}",
                f"chassis_raw_action_topic:={chassis_raw_action_topic}",
                f"chassis_smoothed_action_topic:={chassis_smoothed_action_topic}",
            ),
            setup_scripts=(
                f"/opt/ros/{ros_distro}/setup.bash",
                str(chassis_install),
            ),
            cleanup_process_patterns=(
                "ranger_base_node",
                "chassis_velocity_smoother_node",
                "ros2 launch ranger_base",
                "ranger_mini_v3.launch.py",
                "ranger_mini_v2.launch.py",
                "ranger.launch.py",
            ),
            cwd=str(ROOT_DIR),
            shutdown_timeout_sec=8.0,
            startup_grace_sec=0.8,
            description="Launch the Ranger Mini chassis ROS control node.",
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
                "launch",
                "rslidar_sdk",
                "filtered_start.py",
                f"config_path:={lidar_config}",
            ),
            setup_scripts=(
                f"/opt/ros/{ros_distro}/setup.bash",
                str(lidar_install),
            ),
            cleanup_process_patterns=(
                "rslidar_sdk_node",
                "rslidar_self_filter_node",
                "ros2 launch rslidar_sdk",
                "filtered_start.py",
            ),
            cwd=str(lidar_ws),
            shutdown_timeout_sec=8.0,
            startup_grace_sec=0.8,
            description="Launch the RoboSense LiDAR driver without RViz.",
        ),
    }
    transforms = static_transform_service_spec(ros_distro=ros_distro)
    if transforms is not None:
        specs["transforms"] = transforms
    return specs
