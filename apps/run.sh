#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SONIC_ROOT="${SONIC_REPO_ROOT:-$(cd "$APP_ROOT/../../sonic_deploy" && pwd)}"
PYTHON="$SONIC_ROOT/.venv_teleop/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3)"
fi

export PYTHONUNBUFFERED=1

exec "$PYTHON" "$APP_ROOT/server.py" \
  --host "${DATA_PLATFORM_HOST:-192.168.123.100}" \
  --port "${DATA_PLATFORM_PORT:-9999}" \
  --sonic-root "$SONIC_ROOT"
