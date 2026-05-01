from pathlib import Path

from PIL import Image

from vaultix_api.services.image_derivatives import create_image_derivatives


def test_create_image_derivatives_writes_thumbnail_and_preview_webp(tmp_path: Path):
    source = tmp_path / "original" / "dashboard-hero.png"
    source.parent.mkdir()
    Image.new("RGB", (1600, 900), color=(24, 88, 160)).save(source)

    result = create_image_derivatives(
        source_path=str(source),
        slug="dashboard-hero",
        public_url_prefix=None,
    )

    thumbnail = Image.open(result.thumbnail_path)
    preview = Image.open(result.preview_path)
    assert result.thumbnail_path == str(tmp_path / "thumb" / "dashboard-hero.webp")
    assert result.preview_path == str(tmp_path / "preview" / "dashboard-hero.webp")
    assert result.thumbnail_url == result.thumbnail_path
    assert result.preview_url == result.preview_path
    assert thumbnail.format == "WEBP"
    assert preview.format == "WEBP"
    assert max(thumbnail.size) <= 480
    assert max(preview.size) <= 1280
