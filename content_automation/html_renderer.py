"""
Renders the Sharp Group post template via Playwright.
Loads templates/sharp_group.html, fills in values, screenshots at 1080x1350.

Usage (standalone test):
  py html_renderer.py
"""

import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import ASSETS_DIR
from utils import file_url, strip_white_bg

HANDLE       = "sharp_group"
ASSETS       = ASSETS_DIR / HANDLE
LOGO_PATH    = ASSETS / "logo.png"
FONTS_DIR    = ASSETS / "fonts"
TEMPLATES_DIR = Path(__file__).parent / "templates"

TEMPLATE_MAP = {
    "default": TEMPLATES_DIR / "sharp_group.html",
    "orange":  TEMPLATES_DIR / "sharp_group_orange.html",
}


def render_post(bg_path: Path, post_text: str, output_path: Path, cta_text: str = None, template: str = "default") -> Path:
    """
    Fills in the chosen template and renders it via Playwright.

    Args:
        bg_path:     Path to the background image (fal.ai output)
        post_text:   Albanian headline — goes on the image
        output_path: Where to save the final JPEG
        cta_text:    Optional CTA button text (None = button hidden)
        template:    "default" | "corner_left" | "corner_right"
    """
    tpl_path = TEMPLATE_MAP.get(template, TEMPLATE_MAP["default"])
    html = tpl_path.read_text(encoding="utf-8")

    # Strip white background from logo into a temp file
    tmp_logo = Path(tempfile.mktemp(suffix="_logo.png"))
    strip_white_bg(LOGO_PATH, tmp_logo)

    # Inject file:// URLs for local assets
    html = html.replace("{{ bg_image }}",    file_url(bg_path))
    html = html.replace("{{ logo }}",        file_url(tmp_logo))
    html = html.replace("{{ font_bold }}",   file_url(FONTS_DIR / "Poppins-Bold.ttf"))
    html = html.replace("{{ font_semibold }}", file_url(FONTS_DIR / "Poppins-SemiBold.ttf"))
    clean_text = post_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    html = html.replace("{{ post_text }}",   clean_text)
    html = html.replace("{{ cta_text }}",    cta_text or "")

    # Show CTA button only when text is provided
    if cta_text:
        html = html.replace('class="cta-button"', 'class="cta-button visible"')

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

    print(f"  HTML render saved: {output_path}")
    return output_path


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    from config import OUTPUT_DIR

    bg   = OUTPUT_DIR / "sharp_group" / "post_002_gpt_ref.jpg"
    out  = OUTPUT_DIR / "sharp_group" / "post_002_final.jpg"
    text = "Investo me strategji, jo me humbje!"

    print("Rendering test post...")
    render_post(bg, text, out, cta_text="Behu me i mprehte")
    print(f"Done -> {out}")
