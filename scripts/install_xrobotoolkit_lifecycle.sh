#!/usr/bin/env bash
# Install the reviewed shared XR lifecycle helper; preserve any existing source.
set -euo pipefail
STATION_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SONIC_PROJECT="${1:-$STATION_ROOT/../sonic_deploy}"
python3 - "$STATION_ROOT" "$SONIC_PROJECT" <<'PY'
from pathlib import Path
from datetime import datetime
import hashlib
import os
import shutil
import sys
import tempfile

station,sonic=map(lambda p:Path(p).resolve(),sys.argv[1:])
source=station/'integrations/sonic/xrobotoolkit_runtime.py'
target=sonic/'gear_sonic/utils/teleop/xrobotoolkit_runtime.py'
data=source.read_bytes()
original=target.read_bytes()
if original==data:
    print('XRoboToolkit lifecycle helper already installed.')
    raise SystemExit(0)
upstream='bcce96b3c4599f52a7529915df98d64ee7c7643772daed9ffa42e0bbbb1ce73d'
if hashlib.sha256(original).hexdigest()!=upstream:
    raise SystemExit('XR runtime has other changes; merge the reviewed integration source before installing.')
backup=sonic/'.local-backups'/('xr-lifecycle-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'))/'xrobotoolkit_runtime.py'
backup.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(target,backup)
with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.xr-lifecycle-',delete=False) as f:
    f.write(data)
    temp=Path(f.name)
os.chmod(temp,target.stat().st_mode & 0o777)
os.replace(temp,target)
print('Installed XR lifecycle helper; backup:',backup)
PY
