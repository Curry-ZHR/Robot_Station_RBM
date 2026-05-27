#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-9999}"

if [[ ! -f "${FRONTEND_DIR}/index.html" ]]; then
  echo "frontend/index.html not found"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to run Robot Station"
  exit 1
fi

cd "${ROOT_DIR}"
exec python3 -m backend.server --host "${HOST}" --port "${PORT}"
