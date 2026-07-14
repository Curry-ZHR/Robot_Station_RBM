#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-9999}"
CONTROL_PORT="${CONTROL_PORT:-9998}"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-99}"
export ROS_LOCALHOST_ONLY="${ROS_LOCALHOST_ONLY:-0}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"

if [[ ! -f "${FRONTEND_DIR}/index.html" ]]; then
  echo "frontend/index.html not found"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to run Robot Station"
  exit 1
fi

ROS_SETUP="/opt/ros/${ROS_DISTRO:-humble}/setup.bash"
PIPER_WS="${ROOT_DIR}/ros_packages/control/piper"
PIPER_SETUP="${ROOT_DIR}/ros_packages/control/piper/install/setup.bash"
PIPER_ACTION_MIRROR="${ROOT_DIR}/ros_packages/control/piper/install/piper/lib/piper/piper_action_mirror"
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

ROBOT_STATION_CLEANUP_PATTERNS=(
  "python3 -m backend.server"
  "backend.server --host"
  "robot_station_joint_state_bridge"
  "modules.robot_description.joint_state_bridge"
  "robot_station_robot_state_publisher"
  "robot_state_publisher robot_state_publisher ${ROOT_DIR}"
  "__node:=robot_station_static_tf_"
  "__node:=robot_station_static_tf_base_to_rslidar"
  "robot_station_localizer_node"
  "robot_station_gpu_localizer_node"
  "ros2 run robot_station_mapper robot_station_localizer_node"
  "ros2 run robot_station_mapper robot_station_gpu_localizer_node"
  "robot_station_mapper_cli"
  "rslidar_sdk_node"
  "rslidar_self_filter_node"
  "ros2 launch rslidar_sdk"
  "filtered_start.py"
  "start_orbbec_camera.sh"
  "robot_station_camera_bringup"
  "ros2 launch orbbec_camera"
  "orbbec_camera_node"
  "camera_container"
  "usb_cam_node_exe"
  "__node:=wide_angle_camera"
  "ranger_base_node"
  "chassis_velocity_smoother_node"
  "ros2 launch ranger_base"
  "ranger_mini_v3.launch.py"
  "ranger_mini_v2.launch.py"
  "ranger.launch.py"
  "start_double_piper.launch.py"
  "start_remote_master_piper.launch.py"
  "start_two_piper.launch.py"
  "start_single_piper.launch.py"
  "start_single_piper_rviz.launch.py"
  "piper_single_ctrl"
  "piper_joint_smoother"
  "piper_action_mirror"
  "piper_ms_ctrl"
  "lifting_ctrl_ros2_pkg"
  "service_830abs"
  "service_850pro"
  "lifting_ctrl_server_node"
  "ros2-daemon"
)

ROBOT_STATION_PROTECTED_PATTERNS=(
  "codex"
  ".vscode-server"
  ".cursor-server"
  "copilot"
  "sshd:"
  "ssh "
)

read_cmdline() {
  local pid="$1"
  if [[ ! -r "/proc/${pid}/cmdline" ]]; then
    return 1
  fi
  tr '\0' ' ' < "/proc/${pid}/cmdline" | sed 's/[[:space:]]*$//'
}

cmdline_has_any_pattern() {
  local cmdline="$1"
  shift
  local pattern
  for pattern in "$@"; do
    if [[ "${cmdline}" == *"${pattern}"* ]]; then
      return 0
    fi
  done
  return 1
}

is_current_user_process() {
  local pid="$1"
  local proc_uid
  proc_uid="$(stat -c '%u' "/proc/${pid}" 2>/dev/null || true)"
  [[ -n "${proc_uid}" && "${proc_uid}" == "$(id -u)" ]]
}

signal_robot_station_processes() {
  local signal_name="$1"
  shift
  local current_pgid pid pgid
  local -A signaled_groups=()
  current_pgid="$(ps -o pgid= -p "$$" 2>/dev/null | tr -d ' ' || true)"
  for pid in "$@"; do
    if [[ -z "${pid}" || ! -d "/proc/${pid}" ]]; then
      continue
    fi
    pgid="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d ' ' || true)"
    if [[ -n "${pgid}" && "${pgid}" != "${current_pgid}" && -z "${signaled_groups[${pgid}]:-}" ]]; then
      kill "-${signal_name}" -- "-${pgid}" 2>/dev/null || true
      signaled_groups["${pgid}"]=1
    else
      kill "-${signal_name}" -- "${pid}" 2>/dev/null || true
    fi
  done
}

robot_station_cleanup_matches() {
  local current_pgid proc pid cmdline pgid
  local matches=()
  current_pgid="$(ps -o pgid= -p "$$" 2>/dev/null | tr -d ' ' || true)"
  for proc in /proc/[0-9]*; do
    pid="${proc##*/}"
    if [[ "${pid}" == "$$" || "${pid}" == "${PPID:-}" ]]; then
      continue
    fi
    if ! is_current_user_process "${pid}"; then
      continue
    fi
    pgid="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d ' ' || true)"
    if [[ -n "${current_pgid}" && "${pgid}" == "${current_pgid}" ]]; then
      continue
    fi
    cmdline="$(read_cmdline "${pid}" || true)"
    if [[ -z "${cmdline}" ]]; then
      continue
    fi
    if cmdline_has_any_pattern "${cmdline}" "${ROBOT_STATION_PROTECTED_PATTERNS[@]}"; then
      continue
    fi
    if cmdline_has_any_pattern "${cmdline}" "${ROBOT_STATION_CLEANUP_PATTERNS[@]}"; then
      matches+=("${pid}")
    fi
  done
  printf '%s\n' "${matches[@]}"
}

cleanup_robot_station_processes() {
  if [[ "${ROBOT_STATION_SKIP_PRESTART_CLEANUP:-0}" == "1" ]]; then
    return
  fi

  local pids remaining pid cmdline
  mapfile -t pids < <(robot_station_cleanup_matches)
  if (( ${#pids[@]} == 0 )); then
    return
  fi

  echo "Cleaning stale Robot Station processes: ${pids[*]}"
  if [[ "${ROBOT_STATION_PRESTART_CLEANUP_DRY_RUN:-0}" == "1" ]]; then
    for pid in "${pids[@]}"; do
      cmdline="$(read_cmdline "${pid}" || true)"
      echo "Would clean pid=${pid}: ${cmdline}"
    done
    return
  fi

  signal_robot_station_processes TERM "${pids[@]}"
  sleep 1
  mapfile -t remaining < <(robot_station_cleanup_matches)
  if (( ${#remaining[@]} > 0 )); then
    signal_robot_station_processes KILL "${remaining[@]}"
    sleep 0.3
  fi
}

piper_needs_build() {
  if [[ "${ROBOT_STATION_SKIP_PIPER_BUILD:-0}" == "1" ]]; then
    return 1
  fi
  if [[ ! -x "${PIPER_ACTION_MIRROR}" ]]; then
    return 0
  fi

  local source_file
  for source_file in \
    "${PIPER_WS}/piper/setup.py" \
    "${PIPER_WS}/piper/piper/action_mirror.py" \
    "${PIPER_WS}/piper/piper/piper_action_mirror_node.py" \
    "${PIPER_WS}/piper/launch/start_double_piper.launch.py"
  do
    if [[ -e "${source_file}" && "${source_file}" -nt "${PIPER_ACTION_MIRROR}" ]]; then
      return 0
    fi
  done

  return 1
}

ensure_piper_build() {
  if ! piper_needs_build; then
    return
  fi
  if ! command -v colcon >/dev/null 2>&1; then
    echo "piper package needs rebuild, but colcon is not available"
    exit 1
  fi
  echo "Building piper ROS package..."
  (cd "${PIPER_WS}" && colcon build --symlink-install --packages-select piper)
}

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

cleanup_robot_station_processes

if [[ -f "${ROS_SETUP}" ]]; then
  source_setup "${ROS_SETUP}"
fi

ensure_piper_build

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
