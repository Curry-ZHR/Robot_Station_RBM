#!/usr/bin/env bash
# Add a dedicated official SONIC exporter environment without replacing existing venvs.
set -euo pipefail
STATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SONIC_ROOT="${SONIC_REPO_ROOT:-$(cd "$STATION_ROOT/../sonic_deploy" && pwd)}"
COLLECTION_ENV="$STATION_ROOT/apps/.venv_collection"
UV_BIN="$(command -v uv || true)"
[[ -n "$UV_BIN" ]] || UV_BIN="$HOME/.local/bin/uv"
[[ -x "$UV_BIN" ]] || { echo 'uv is required.' >&2; exit 1; }
[[ -x "$SONIC_ROOT/.venv_teleop/bin/python" ]] || { echo 'SONIC teleop Python is required.' >&2; exit 1; }
if [[ ! -x "$COLLECTION_ENV/bin/python" ]]; then
  "$UV_BIN" venv "$COLLECTION_ENV" --python "$SONIC_ROOT/.venv_teleop/bin/python"
fi
# gear_sonic pins the LeRobot v2.1 commit and data dependencies. CPU torch suffices for recording/FK.
COLLECTION_LOCK_ARGS=()
if [[ -f "$STATION_ROOT/apps/requirements-collection.lock" ]]; then
  COLLECTION_LOCK_ARGS=(-r "$STATION_ROOT/apps/requirements-collection.lock")
fi
GIT_LFS_SKIP_SMUDGE=1 "$UV_BIN" pip install --python "$COLLECTION_ENV/bin/python" --torch-backend cpu \
  "${COLLECTION_LOCK_ARGS[@]}" -e "$SONIC_ROOT/gear_sonic[data_collection]"
"$COLLECTION_ENV/bin/python" -c 'from gear_sonic.scripts.run_data_exporter import GrootDataCollector; from gear_sonic.data.exporter import Gr00tDataExporter; print("Official SONIC collector import: OK")'
