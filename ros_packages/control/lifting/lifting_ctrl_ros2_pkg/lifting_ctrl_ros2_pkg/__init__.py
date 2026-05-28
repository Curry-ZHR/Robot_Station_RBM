import platform
import sys
from pathlib import Path


_package_dir = Path(__file__).resolve().parent
_package_name = __name__.rpartition(".")[2]
_python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
_machine = platform.machine().lower()

_so_candidates = []
if len(_package_dir.parents) > 1:
    _so_candidates.append(
        _package_dir.parents[1]
        / "install"
        / _package_name
        / "lib"
        / f"python{_python_version}"
        / "site-packages"
        / _package_name
    )
if _machine in {"aarch64", "arm64"}:
    _so_candidates.append(_package_dir / "so" / f"agx_orin_arm64_humble_{_python_version}")
_so_candidates.append(_package_dir / "so" / f"python{_python_version}")

for _so_dir in _so_candidates:
    if _so_dir.is_dir():
        _so_path = str(_so_dir)
        if _so_path not in __path__:
            __path__.append(_so_path)
