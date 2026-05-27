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
    cwd: str = "."
    shutdown_timeout_sec: float = 6.0
    startup_grace_sec: float = 0.8
    description: str = ""

    def to_dict(self):
        payload = asdict(self)
        payload["command"] = list(self.command)
        payload["setupScripts"] = payload.pop("setup_scripts")
        payload["shutdownTimeoutSec"] = payload.pop("shutdown_timeout_sec")
        payload["startupGraceSec"] = payload.pop("startup_grace_sec")
        return payload


def default_service_specs():
    ros_distro = os.environ.get("ROS_DISTRO", "humble")
    piper_install = ROOT_DIR / "ros_packages" / "control" / "piper" / "install" / "setup.bash"
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
            ),
            setup_scripts=(
                f"/opt/ros/{ros_distro}/setup.bash",
                str(piper_install),
            ),
            cwd=str(ROOT_DIR),
            description="Launch the dual-arm Piper ROS control nodes.",
        ),
    }
