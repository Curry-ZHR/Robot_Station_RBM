#!/usr/bin/env bash
# Install offline file conversion dependencies without touching SONIC environments.
set -euo pipefail
STATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONVERSION_ENV="$STATION_ROOT/apps/.venv_conversion"
if [[ ! -d "$CONVERSION_ENV" ]]; then
  python3 -m venv "$CONVERSION_ENV"
fi
if [[ ! -x "$CONVERSION_ENV/bin/python" ]]; then
  echo "Existing conversion environment is incomplete; inspect it before repair." >&2
  exit 1
fi
"$CONVERSION_ENV/bin/python" -m pip install --disable-pip-version-check -r "$STATION_ROOT/apps/requirements-conversion.txt"
"$CONVERSION_ENV/bin/python" -c 'import numpy,pyarrow,h5py; print("Offline conversion environment ready")'
command -v ffmpeg >/dev/null || echo "ffmpeg is required for RGB decoding."
command -v ffprobe >/dev/null || echo "ffprobe is required for video frame validation."
