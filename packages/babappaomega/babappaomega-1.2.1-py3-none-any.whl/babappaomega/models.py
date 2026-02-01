# babappaomega/models.py

import hashlib
from pathlib import Path
import urllib.request

from platformdirs import user_cache_dir

ZENODO_MODELS = {
    "frozen": {
        "url": "https://zenodo.org/record/18195869/files/babappaomega.pt",
        "sha256": "657a662563af31304abcb208fc903d2770a9184632a9bab2095db4c538fed8eb",
        "doi": "10.5281/zenodo.18195869",
        "filename": "babappaomega.pt",
    }
}


def get_cache_dir():
    cache = Path(user_cache_dir("babappaomega"))
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def ensure_model(model_tag="frozen") -> Path:
    if model_tag not in ZENODO_MODELS:
        raise ValueError(f"Unknown model tag: {model_tag}")

    entry = ZENODO_MODELS[model_tag]
    cache_dir = get_cache_dir()
    model_path = cache_dir / entry["filename"]

    if model_path.exists():
        if sha256sum(model_path) == entry["sha256"]:
            return model_path
        else:
            model_path.unlink()

    print(
        f"[BABAPPAΩ] Downloading frozen model from Zenodo "
        f"(DOI: {entry['doi']})"
    )

    urllib.request.urlretrieve(entry["url"], model_path)

    if sha256sum(model_path) != entry["sha256"]:
        model_path.unlink()
        raise RuntimeError("Model download failed SHA256 verification")

    return model_path
