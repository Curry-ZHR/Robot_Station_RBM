#!/usr/bin/env bash
set -euo pipefail
systemctl --user stop robot-station.service
printf '%s\n' 'G1 工作台已关闭；下次开机仍会自启动。关闭自启动：./run.sh disable-autostart'
