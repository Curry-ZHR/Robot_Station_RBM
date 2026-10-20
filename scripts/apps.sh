#!/usr/bin/env bash
set -euo pipefail
STATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$STATION_ROOT/run.sh" "$@"
