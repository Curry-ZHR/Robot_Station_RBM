#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-9999}"
CONTROL_PORT="${CONTROL_PORT:-9998}"

if [[ ! -f "${FRONTEND_DIR}/index.html" ]]; then
  echo "frontend/index.html not found"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to run Robot Station"
  exit 1
fi

ROS_SETUP="/opt/ros/${ROS_DISTRO:-humble}/setup.bash"
PIPER_SETUP="${ROOT_DIR}/ros_packages/control/piper/install/setup.bash"
LIFTING_SETUP="${ROOT_DIR}/ros_packages/control/lifting/install/setup.bash"
CHASSIS_SETUP="${ROOT_DIR}/ros_packages/control/chassis/install/setup.bash"
CAMERA_SETUP="${ROOT_DIR}/ros_packages/sensors/camera/orbbec/install/setup.bash"
LIDAR_SETUP="${ROOT_DIR}/ros_packages/sensors/lidar/install/setup.bash"

disable_proxy_env() {
  unset http_proxy https_proxy ftp_proxy all_proxy ws_proxy wss_proxy rsync_proxy no_proxy
  unset HTTP_PROXY HTTPS_PROXY FTP_PROXY ALL_PROXY WS_PROXY WSS_PROXY RSYNC_PROXY NO_PROXY
}

source_setup() {
  local setup_file="$1"
  set +u
  # shellcheck source=/dev/null
  source "${setup_file}"
  set -u
}

if [[ -f "${ROS_SETUP}" ]]; then
  source_setup "${ROS_SETUP}"
fi

if [[ -f "${PIPER_SETUP}" ]]; then
  source_setup "${PIPER_SETUP}"
fi

if [[ -f "${LIFTING_SETUP}" ]]; then
  source_setup "${LIFTING_SETUP}"
fi

if [[ -f "${CHASSIS_SETUP}" ]]; then
  source_setup "${CHASSIS_SETUP}"
fi

if [[ -f "${CAMERA_SETUP}" ]]; then
  source_setup "${CAMERA_SETUP}"
fi

if [[ -f "${LIDAR_SETUP}" ]]; then
  source_setup "${LIDAR_SETUP}"
fi

disable_proxy_env

cd "${ROOT_DIR}"
exec python3 -m backend.server --host "${HOST}" --port "${PORT}" --control-port "${CONTROL_PORT}"
