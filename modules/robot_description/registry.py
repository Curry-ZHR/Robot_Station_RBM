import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT_DIR / "models.json"


class RobotModelError(ValueError):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _load_manifest():
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    models = payload.get("models", [])
    if not isinstance(models, list):
        raise RobotModelError("MODEL-MANIFEST", "Robot model manifest must contain a models list.")
    return models


def _asset_url(model, relative_path):
    family = model["family"]
    key = model["key"]
    return f"/api/robot-model-assets/{family}/{key}/{relative_path}"


def _public_model(model, include_detail=False):
    payload = {
        "key": model["key"],
        "family": model["family"],
        "name": model["name"],
        "description": model.get("description", ""),
        "urdfUrl": _asset_url(model, model["urdf"]),
    }
    if include_detail:
        payload.update(
            {
                "assetRoot": model.get("assetRoot", ""),
                "jointMap": model.get("jointMap", {}),
                "frames": model.get("frames", {}),
            }
        )
    return payload


def list_models():
    return {
        "ok": True,
        "models": [_public_model(model) for model in _load_manifest()],
    }


def get_model(key):
    for model in _load_manifest():
        if model.get("key") == key:
            return {
                "ok": True,
                "model": _public_model(model, include_detail=True),
            }
    return {
        "ok": False,
        "code": "MODEL-UNKNOWN",
        "detail": f"Unknown robot model: {key}",
    }


def _find_model(family, key):
    for model in _load_manifest():
        if model.get("family") == family and model.get("key") == key:
            return model
    raise RobotModelError("MODEL-UNKNOWN", f"Unknown robot model: {family}/{key}")


def _allowed_asset_paths(model):
    paths = {model["urdf"]}
    urdf_path = (ROOT_DIR / model["family"] / model["urdf"]).resolve()
    asset_root = model.get("assetRoot", "")
    if asset_root:
        asset_root_path = (ROOT_DIR / model["family"] / asset_root).resolve()
        if asset_root_path.exists():
            for path in asset_root_path.rglob("*"):
                if path.is_file():
                    paths.add(path.relative_to(ROOT_DIR / model["family"]).as_posix())

    if urdf_path.exists():
        for line in urdf_path.read_text(encoding="utf-8").splitlines():
            marker = 'filename="'
            if marker not in line:
                continue
            fragment = line.split(marker, 1)[1].split('"', 1)[0]
            if fragment.startswith("../"):
                candidate = (urdf_path.parent / fragment).resolve()
                try:
                    paths.add(candidate.relative_to(ROOT_DIR / model["family"]).as_posix())
                except ValueError:
                    pass
    return paths


def resolve_model_asset(family, key, relative_path):
    model = _find_model(family, key)
    clean_path = Path(relative_path)
    if clean_path.is_absolute() or any(part in {"", ".", ".."} for part in clean_path.parts):
        raise RobotModelError("MODEL-ASSET-PATH", "Robot model asset path is invalid.")

    allowed_paths = _allowed_asset_paths(model)
    normalized = clean_path.as_posix()
    if normalized not in allowed_paths:
        raise RobotModelError("MODEL-ASSET-DENIED", f"Robot model asset is not in the manifest: {normalized}")

    root = (ROOT_DIR / family).resolve()
    candidate = (root / normalized).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise RobotModelError("MODEL-ASSET-PATH", "Robot model asset path escapes model root.") from exc
    if not candidate.is_file():
        raise RobotModelError("MODEL-ASSET-MISSING", f"Robot model asset does not exist: {normalized}")
    return candidate
