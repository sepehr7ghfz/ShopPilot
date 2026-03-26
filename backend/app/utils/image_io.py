from __future__ import annotations

from io import BytesIO
from pathlib import Path


def load_image_from_bytes(image_bytes: bytes):
    try:
        from PIL import Image, UnidentifiedImageError

        with Image.open(BytesIO(image_bytes)) as image:
            return image.convert("RGB")
    except ImportError as exc:
        raise RuntimeError("Pillow is required for image handling. Install: pip install pillow") from exc
    except UnidentifiedImageError as exc:
        raise ValueError("Uploaded file is not a valid image.") from exc
    except OSError as exc:
        raise ValueError("Uploaded image could not be read.") from exc


def load_image_from_path(path: Path):
    try:
        from PIL import Image, UnidentifiedImageError

        with Image.open(path) as image:
            return image.convert("RGB")
    except ImportError as exc:
        raise RuntimeError("Pillow is required for image handling. Install: pip install pillow") from exc
    except FileNotFoundError as exc:
        raise ValueError(f"Catalog image not found: {path}") from exc
    except UnidentifiedImageError as exc:
        raise ValueError(f"Catalog image is invalid: {path}") from exc
    except OSError as exc:
        raise ValueError(f"Catalog image could not be read: {path}") from exc


def resolve_catalog_image_path(image_path: str, data_root: Path, catalog_root: Path) -> Path:
    candidate = Path(image_path)
    if candidate.is_absolute():
        return candidate
    if candidate.parts and candidate.parts[0] == "catalog":
        return data_root / candidate
    return catalog_root / candidate
