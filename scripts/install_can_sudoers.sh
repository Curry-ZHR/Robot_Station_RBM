#!/usr/bin/env bash
set -euo pipefail

TARGET_USER="${SUDO_USER:-${USER}}"
IP_BIN="$(command -v ip || true)"
SUDOERS_FILE="/etc/sudoers.d/robot-station-can"
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
# Robot Station CAN activation whitelist.
# Allows ${TARGET_USER} to activate and rename only Piper CAN interfaces.
Cmnd_Alias ROBOT_STATION_CAN = \\
    ${IP_BIN} link set can0 down, \\
    ${IP_BIN} link set can1 down, \\
    ${IP_BIN} link set can_left down, \\
    ${IP_BIN} link set can_right down, \\
    ${IP_BIN} link set can0 type can bitrate 1000000, \\
    ${IP_BIN} link set can1 type can bitrate 1000000, \\
    ${IP_BIN} link set can_left type can bitrate 1000000, \\
    ${IP_BIN} link set can_right type can bitrate 1000000, \\
    ${IP_BIN} link set can0 name can_left, \\
    ${IP_BIN} link set can0 name can_right, \\
    ${IP_BIN} link set can1 name can_left, \\
    ${IP_BIN} link set can1 name can_right, \\
    ${IP_BIN} link set can_left up, \\
    ${IP_BIN} link set can_right up

${TARGET_USER} ALL=(root) NOPASSWD: ROBOT_STATION_CAN
EOF

sudo visudo -cf "${TMP_FILE}" >/dev/null
sudo install -o root -g root -m 0440 "${TMP_FILE}" "${SUDOERS_FILE}"
sudo visudo -cf "${SUDOERS_FILE}" >/dev/null

echo "已安装 CAN sudoers 白名单: ${SUDOERS_FILE}"
echo "验证命令:"
echo "  sudo -n -l ${IP_BIN} link set can0 down"
echo "如果验证命令不再提示 password，则 sudoers 已生效。"
