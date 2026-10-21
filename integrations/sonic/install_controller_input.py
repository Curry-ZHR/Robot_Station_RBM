"""Add a backwards-compatible loopback bind option to the pinned SONIC PICO manager."""
from pathlib import Path
import argparse
import hashlib
from datetime import datetime, timezone

BASELINE = '4ea92b19a42604a2d487a7cc78ea7cca1bd4be93359217832889c290fbb08925'
PATCHED = '98591749fa2f0ba43f860f9c6eee81971ca8e1d5eb5349efd7067d7bd0694ebc'
MARKER = '# Robot Station: optional private manager uplink.'


def install(root):
    root = Path(root).resolve()
    path = root / 'gear_sonic/scripts/pico_manager_thread_server.py'
    source = path.read_text()
    if MARKER in source:
        if hashlib.sha256(path.read_bytes()).hexdigest() != PATCHED: raise RuntimeError('Patched manager changed; inspect before overwriting')
        compile(source, str(path), 'exec')
        return 'already installed'
    if hashlib.sha256(path.read_bytes()).hexdigest() != BASELINE:
        raise RuntimeError('PICO manager differs from reviewed baseline; inspect before applying integration')
    anchor = 'def run_pico_manager(\n    port: int = 5556,'
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '\n    bind_host: str = "*",  ' + MARKER)
    anchor = '    socket.bind(f"tcp://*:{port}")'
    start = source.index('def run_pico_manager(')
    before, after = source[:start], source[start:]
    assert after.count(anchor) == 1
    after = after.replace(anchor, '    socket.bind(f"tcp://{bind_host}:{port}")')
    source = before + after
    anchor = '    parser.add_argument("--port", type=int, default=5556, help="ZMQ server port (default: 5556)")'
    assert source.count(anchor) == 1
    source = source.replace(anchor, anchor + '\n    parser.add_argument("--bind-host", choices=["*", "127.0.0.1"], default="*", help="Manager publisher bind address")')
    start = source.index('        run_pico_manager(')
    anchor = '            port=args.port,'
    before, after = source[:start], source[start:]
    assert anchor in after
    source = before + after.replace(anchor, anchor + '\n            bind_host=args.bind_host,', 1)
    compile(source, str(path), 'exec')
    backup = root / '.local-backups' / ('station-manager-bind-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    (backup / path.name).write_bytes(path.read_bytes())
    temporary = path.with_name(path.name + '.station-bind')
    temporary.write_text(source)
    temporary.chmod(path.stat().st_mode)
    temporary.replace(path)
    return 'installed; original saved in ' + str(backup)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sonic_root', type=Path)
    print(install(parser.parse_args().sonic_root))
