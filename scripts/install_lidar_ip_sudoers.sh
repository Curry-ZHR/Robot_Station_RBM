#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${SUDO_USER:-${USER}}"
LIDAR_HOST_IP_CIDR="${ROBOT_STATION_LIDAR_HOST_IP_CIDR:-192.168.1.100/24}"
LIDAR_INTERFACE="${ROBOT_STATION_LIDAR_INTERFACE:-enp11s0}"
LIDAR_ROUTE_DEST="${ROBOT_STATION_LIDAR_ROUTE_DEST:-192.168.1.154/32}"
LIDAR_ROUTE_VIA="${ROBOT_STATION_LIDAR_ROUTE_VIA:-172.16.18.1}"
LIDAR_ROUTE_INTERFACE="${ROBOT_STATION_LIDAR_ROUTE_INTERFACE:-eno1}"
IP_BIN="$(command -v ip || true)"
SUDOERS_FILE="/etc/sudoers.d/robot-station-lidar-ip"
TMP_FILE="$(mktemp)"

cleanup() {
  rm -f "${TMP_FILE}"
}
trap cleanup EXIT

if [[ -z "${IP_BIN}" ]]; then
  echo "错误: 未找到 ip 命令，请先安装 iproute2。"
  exit 1
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "错误: 未找到 sudo。"
  exit 1
fi

if [[ "${TARGET_USER}" == "root" ]]; then
  echo "错误: 请用实际登录用户运行本脚本，不要直接用 root 运行。"
  exit 1
fi

cat >"${TMP_FILE}" <<EOF
# Robot Station LiDAR network whitelist.
# Allows ${TARGET_USER} to configure the LiDAR receive IP and route.
Cmnd_Alias ROBOT_STATION_LIDAR_IP = \\
    ${IP_BIN} addr add ${LIDAR_HOST_IP_CIDR} dev ${LIDAR_INTERFACE}, \\
    ${IP_BIN} route replace ${LIDAR_ROUTE_DEST} via ${LIDAR_ROUTE_VIA} dev ${LIDAR_ROUTE_INTERFACE}

${TARGET_USER} ALL=(root) NOPASSWD: ROBOT_STATION_LIDAR_IP
EOF

sudo visudo -cf "${TMP_FILE}" >/dev/null
sudo install -o root -g root -m 0440 "${TMP_FILE}" "${SUDOERS_FILE}"
sudo visudo -cf "${SUDOERS_FILE}" >/dev/null

echo "已安装 LiDAR IP sudoers 白名单: ${SUDOERS_FILE}"
echo "允许命令:"
echo "  sudo -n ${IP_BIN} addr add ${LIDAR_HOST_IP_CIDR} dev ${LIDAR_INTERFACE}"
echo "  sudo -n ${IP_BIN} route replace ${LIDAR_ROUTE_DEST} via ${LIDAR_ROUTE_VIA} dev ${LIDAR_ROUTE_INTERFACE}"
echo "run.sh 会自动补 ${LIDAR_HOST_IP_CIDR}，并配置 ${LIDAR_ROUTE_DEST} 路由。"
