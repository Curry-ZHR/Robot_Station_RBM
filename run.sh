#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-9999}"

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

cd "${ROOT_DIR}"
exec python3 -m backend.server --host "${HOST}" --port "${PORT}"
