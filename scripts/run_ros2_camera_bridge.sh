#!/usr/bin/env bash
set -euo pipefail
STATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
set +u
source /opt/ros/humble/setup.bash
set -u
exec "$STATION_ROOT/apps/.venv_ros2_camera/bin/python" -u "$STATION_ROOT/apps/ros2_camera_bridge.py" "$@"
