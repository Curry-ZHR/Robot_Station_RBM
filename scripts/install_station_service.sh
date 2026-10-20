#!/usr/bin/env bash
set -euo pipefail
STATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SONIC_ROOT="${SONIC_REPO_ROOT:-$(dirname "$STATION_ROOT")/sonic_deploy}"
PYTHON="$SONIC_ROOT/.venv_teleop/bin/python"
[[ -x "$PYTHON" && -f "$STATION_ROOT/apps/station_supervisor.py" ]] || { echo '缺少工作台或 SONIC Python 环境。' >&2; exit 1; }
mkdir -p "$HOME/.config/systemd/user"
python3 - "$HOME/.config/systemd/user/robot-station.service" "$STATION_ROOT" "$SONIC_ROOT" "$PYTHON" <<'PY'
from pathlib import Path
import sys
path,root,sonic,python=sys.argv[1:]
def quote(value):return '"'+value.replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'
unit='''[Unit]
Description=G1 Robot Station workbench (no robot motion on boot)
After=network.target
StartLimitIntervalSec=120
StartLimitBurst=10

[Service]
Type=simple
WorkingDirectory=ROOT
ExecStart=PYTHON -u SCRIPT --sonic-root SONIC --host 0.0.0.0 --port 9999
Environment=ROBOT_STATION_PUBLIC_HOST=192.168.123.100
Restart=on-failure
RestartSec=5
KillMode=mixed
TimeoutStopSec=120
UMask=0077

[Install]
WantedBy=default.target
'''
unit=unit.replace('WorkingDirectory=ROOT','WorkingDirectory='+root.replace('%','%%'))
for key,value in [('ROOT',root),('PYTHON',python),('SCRIPT',root+'/apps/station_supervisor.py'),('SONIC',sonic)]:unit=unit.replace(key,quote(value))
Path(path).write_text(unit)
PY
systemctl --user daemon-reload
systemctl --user enable robot-station.service
if [[ "$(loginctl show-user "$(id -un)" -p Linger --value)" != yes ]]; then
  echo '开机前台登录前启动服务需要启用用户驻留。'
  sudo loginctl enable-linger "$(id -un)"
fi
printf '%s\n' '自启动已配置。运行 ./run.sh 启动。'
