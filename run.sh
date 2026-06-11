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
LOCALIZATION_SETUP="${ROOT_DIR}/ros_packages/localization/install/setup.bash"
FAST_GICP_SETUP="${ROOT_DIR}/modules/localization/fast_gicp_ws/install/setup.bash"
MAPPER_SETUP="${ROOT_DIR}/ros_packages/localization/robot_station_mapper/install/setup.bash"

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

prepend_path() {
  local var_name="$1"
  local path_value="$2"
  if [[ ! -d "${path_value}" ]]; then
    return
  fi
  local current_value="${!var_name:-}"
  case ":${current_value}:" in
    *":${path_value}:"*) ;;
    *)
      if [[ -n "${current_value}" ]]; then
        export "${var_name}=${path_value}:${current_value}"
      else
        export "${var_name}=${path_value}"
      fi
      ;;
  esac
}

configure_cuda_runtime() {
  local cuda_root="${FAST_GICP_CUDA_HOME:-${CUDA_HOME:-}}"
  if [[ -z "${cuda_root}" ]]; then
    if [[ -d "/usr/local/cuda-11.8" ]]; then
      cuda_root="/usr/local/cuda-11.8"
    elif [[ -d "/usr/local/cuda" ]]; then
      cuda_root="/usr/local/cuda"
    fi
  fi
  if [[ -z "${cuda_root}" || ! -d "${cuda_root}" ]]; then
    return
  fi
  export CUDA_HOME="${cuda_root}"
  prepend_path PATH "${cuda_root}/bin"
  prepend_path LD_LIBRARY_PATH "${cuda_root}/lib64"
  prepend_path LD_LIBRARY_PATH "${cuda_root}/targets/x86_64-linux/lib"
}

configure_cuda_runtime

cleanup_stale_localizers() {
  local pids
  pids="$(
    pgrep -f \
      "${ROOT_DIR}/ros_packages/localization/robot_station_mapper/install/.*/robot_station_(gpu_)?localizer_node|ros2 run robot_station_mapper robot_station_(gpu_)?localizer_node" \
      || true
  )"
  if [[ -z "${pids}" ]]; then
    return
  fi
  while read -r pid; do
    if [[ -z "${pid}" || "${pid}" == "$$" ]]; then
      continue
    fi
    local pgid
    pgid="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d ' ' || true)"
    if [[ -n "${pgid}" ]]; then
      kill -TERM "-${pgid}" 2>/dev/null || true
    else
      kill -TERM "${pid}" 2>/dev/null || true
    fi
  done <<< "${pids}"
  sleep 1
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

if [[ -f "${LOCALIZATION_SETUP}" ]]; then
  source_setup "${LOCALIZATION_SETUP}"
fi

if [[ -f "${FAST_GICP_SETUP}" ]]; then
  source_setup "${FAST_GICP_SETUP}"
fi

if [[ -f "${MAPPER_SETUP}" ]]; then
  source_setup "${MAPPER_SETUP}"
fi

cleanup_stale_localizers

disable_proxy_env

cd "${ROOT_DIR}"
exec python3 -m backend.server --host "${HOST}" --port "${PORT}" --control-port "${CONTROL_PORT}"
