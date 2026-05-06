"""Quick test for corner-right and corner-left templates."""
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

from config import ASSETS_DIR, OUTPUT_DIR

HANDLE    = "sharp_group"
ASSETS    = ASSETS_DIR / HANDLE
LOGO_PATH = ASSETS / "logo.png"
FONTS_DIR = ASSETS / "fonts"


def _file_url(path: Path) -> str:
    return path.resolve().as_uri()


def _strip_white_bg(src: Path, dst: Path, threshold: int = 240) -> Path:
    img  = Image.open(src).convert("RGBA")
    data = np.array(img, dtype=np.uint8)
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    white_mask = (r >= threshold) & (g >= threshold) & (b >= threshold)
    data[:,:,3] = np.where(white_mask, 0, a)
    result = Image.fromarray(data)
    bbox = result.getbbox()
    if bbox:
        result = result.crop(bbox)
    result.save(dst)
    return dst


def render_template(template_path: Path, bg_path: Path, post_text: str, output_path: Path) -> Path:
    html = template_path.read_text(encoding="utf-8")

    tmp_logo = Path(tempfile.mktemp(suffix="_logo.png"))
    _strip_white_bg(LOGO_PATH, tmp_logo)

    clean_text = post_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")

    html = html.replace("{{ bg_image }}",      _file_url(bg_path))
    html = html.replace("{{ logo }}",          _file_url(tmp_logo))
    html = html.replace("{{ font_bold }}",     _file_url(FONTS_DIR / "Poppins-Bold.ttf"))
    html = html.replace("{{ font_semibold }}", _file_url(FONTS_DIR / "Poppins-SemiBold.ttf"))
    html = html.replace("{{ post_text }}",     clean_text)
    html = html.replace("{{ cta_text }}",      "")

    with tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(html)
        tmp_path = Path(f.name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page    = browser.new_page(viewport={"width": 1080, "height": 1350})
            page.goto(f"file:///{tmp_path.as_posix()}")
            page.wait_for_timeout(800)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(output_path),
                type="jpeg",
                quality=95,
                full_page=False,
                clip={"x": 0, "y": 0, "width": 1080, "height": 1350},
            )
            browser.close()
    finally:
        tmp_path.unlink(missing_ok=True)
        tmp_logo.unlink(missing_ok=True)

    print(f"  Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    templates_dir = Path(__file__).parent / "templates"
    bg  = OUTPUT_DIR / "sharp_group" / "post_014_gpt_ref.jpg"
    text = 'Shumica e bizneseve\nnuk kane <span class="hl">strategji</span>.\nVetem aktivitet.'

    print("Rendering corner-right...")
    render_template(
        templates_dir / "sharp_group_corner_right.html",
        bg,
        text,
        OUTPUT_DIR / "sharp_group" / "test_corner_right.jpg",
    )

    print("Rendering corner-left...")
    render_template(
        templates_dir / "sharp_group_corner_left.html",
        bg,
        text,
        OUTPUT_DIR / "sharp_group" / "test_corner_left.jpg",
    )

    print("Done. Check output/sharp_group/test_corner_right.jpg and test_corner_left.jpg")
