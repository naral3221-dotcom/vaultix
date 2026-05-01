from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class ImageDerivativeResult:
    thumbnail_path: str
    preview_path: str
    thumbnail_url: str
    preview_url: str


def create_image_derivatives(
    *,
    source_path: str,
    slug: str,
    public_url_prefix: str | None,
    thumbnail_max_size: int = 480,
    preview_max_size: int = 1280,
) -> ImageDerivativeResult:
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(source_path)

    root = source.parent.parent if source.parent.name == "original" else source.parent
    thumbnail_path = root / "thumb" / f"{slug}.webp"
    preview_path = root / "preview" / f"{slug}.webp"
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as image:
        normalized = image.convert("RGB")
        _save_resized_webp(normalized, thumbnail_path, thumbnail_max_size)
        _save_resized_webp(normalized, preview_path, preview_max_size)

    return ImageDerivativeResult(
        thumbnail_path=str(thumbnail_path),
        preview_path=str(preview_path),
        thumbnail_url=_to_public_url(thumbnail_path, root, public_url_prefix),
        preview_url=_to_public_url(preview_path, root, public_url_prefix),
    )


def _save_resized_webp(image: Image.Image, output_path: Path, max_size: int) -> None:
    resized = image.copy()
    resized.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    resized.save(output_path, format="WEBP", quality=82, method=6)


def _to_public_url(path: Path, root: Path, public_url_prefix: str | None) -> str:
    if public_url_prefix is None:
        return str(path)
    relative = path.relative_to(root).as_posix()
    return f"{public_url_prefix.rstrip('/')}/{relative}"
