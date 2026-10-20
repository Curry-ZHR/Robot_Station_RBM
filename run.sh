#!/usr/bin/env bash
# Unified persistent Robot Station entrypoint. No motion at boot.
set -euo pipefail
STATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE=robot-station.service
if [[ "${1:-}" == apps || "${1:-}" == console ]]; then shift; fi
case "${1:-start}" in
  start|restart)
    if ! systemctl --user cat "$SERVICE" >/dev/null 2>&1; then
      bash "$STATION_ROOT/scripts/install_station_service.sh"
    fi
    systemctl --user enable "$SERVICE" >/dev/null
    systemctl --user "${1:-start}" "$SERVICE"
    for _ in {1..100}; do
      if curl --noproxy '*' -fsS --max-time 1 http://127.0.0.1:9999/healthz >/dev/null 2>&1; then
        echo 'G1 工作台已启动：http://192.168.123.100:9999/'; exit 0
      fi
      if systemctl --user is-failed --quiet "$SERVICE"; then break; fi
      sleep .2
    done
    echo '启动尚未就绪，请运行 ./run.sh logs 查看原因。' >&2; exit 1 ;;
  stop) exec bash "$STATION_ROOT/stop.sh" ;;
  status) systemctl --user --no-pager status "$SERVICE" ;;
  logs) journalctl --user -u "$SERVICE" -n 60 --no-pager; tail -n 40 "$STATION_ROOT/apps/.runtime/station-processes/web.log" ;;
  disable-autostart) systemctl --user disable "$SERVICE"; echo '已关闭开机自启动；当前进程状态未改变。' ;;
  legacy) shift; exec bash "$STATION_ROOT/run_legacy_ros.sh" "$@" ;;
  *) echo '用法：./run.sh [start|restart|status|logs|disable-autostart|legacy]'; exit 2 ;;
esac
