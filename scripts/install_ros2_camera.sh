#!/usr/bin/env bash
# ROS ABI stays on system Python/numpy; only wire dependencies go in this venv.
set -euo pipefail
STATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CAMERA_ENV="$STATION_ROOT/apps/.venv_ros2_camera"
[[ -f /opt/ros/humble/setup.bash ]] || { echo 'ROS 2 Humble is required.' >&2; exit 1; }
set +u
source /opt/ros/humble/setup.bash
set -u
UV_BIN="$(command -v uv || true)"
[[ -n "$UV_BIN" ]] || UV_BIN="$HOME/.local/bin/uv"
[[ -x "$UV_BIN" ]] || { echo 'uv is required.' >&2; exit 1; }
if [[ ! -x "$CAMERA_ENV/bin/python" ]]; then
  "$UV_BIN" venv "$CAMERA_ENV" --python /usr/bin/python3 --system-site-packages
fi
"$UV_BIN" pip install --python "$CAMERA_ENV/bin/python" -r "$STATION_ROOT/apps/requirements-ros2-camera.txt"
"$CAMERA_ENV/bin/python" -c 'import rclpy,cv2,cv_bridge,sensor_msgs.msg,zmq,msgpack,numpy; print("ROS 2 camera environment: OK; numpy",numpy.__version__)'
