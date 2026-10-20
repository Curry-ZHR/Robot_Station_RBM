#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$APP_ROOT/.runtime/server.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "Data_platform 未运行：找不到 $PID_FILE"
  exit 0
fi

PID="$(tr -d '[:space:]' < "$PID_FILE")"
if [[ ! "$PID" =~ ^[0-9]+$ ]]; then
  echo "PID 文件内容无效：$PID_FILE" >&2
  exit 1
fi

if ! kill -0 "$PID" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "Data_platform 已停止，已清理过期 PID 文件。"
  exit 0
fi

if [[ -r "/proc/$PID/cmdline" ]]; then
  COMMAND="$(tr '\0' ' ' < "/proc/$PID/cmdline")"
else
  COMMAND="$(ps -p "$PID" -o command= 2>/dev/null || true)"
fi

if [[ "$COMMAND" != *"$APP_ROOT/server.py"* ]]; then
  echo "拒绝停止 PID $PID：该进程不是 Data_platform 服务。" >&2
  echo "当前命令：$COMMAND" >&2
  exit 1
fi

kill "$PID"

for _ in {1..50}; do
  if ! kill -0 "$PID" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "Data_platform 已停止（PID $PID）。"
    exit 0
  fi
  sleep 0.1
done

echo "Data_platform 在 5 秒内未退出，请检查进程 PID $PID。" >&2
exit 1
