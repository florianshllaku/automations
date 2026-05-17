"""
Renders the Ventura Travel story template via Playwright.
Story format: 1080x1920 (9:16, Instagram Stories).

Usage (standalone test):
  py turizem_story_renderer.py
"""

import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import ASSETS_DIR, OUTPUT_DIR
from utils import file_url

HANDLE     = "turizem"
ASSETS     = ASSETS_DIR / HANDLE
ICON_WHITE = ASSETS / "venture-icon-white.png"
FONTS_DIR  = ASSETS / "fonts"
TEMPLATE   = Path(__file__).parent / "templates" / "turizem_story.html"


def render_story(
    bg_path:       Path,
    output_path:   Path,
    destination:   str,
    price:         str,
    event_badge:   str = "",
    includes_text: str = "",
    template_name: str = "turizem_story.html",
) -> Path:
    """
    Fill the story template and render via Playwright at 1080x1920.

    Args:
        bg_path:       Path to background photo
        output_path:   Where to save the JPEG
        destination:   e.g. "VERONA"
        price:         e.g. "159"
        event_badge:   Optional event label (empty = hidden)
        includes_text: What's included, e.g. "BILETA • HOTELI • TAKSAT" (empty = hidden)
        template_name: HTML template filename (default: "turizem_story.html")
    """
    template_path = Path(__file__).parent / "templates" / template_name
    html = template_path.read_text(encoding="utf-8")

    html = html.replace("{{ bg_image }}",           file_url(bg_path))
    html = html.replace("{{ venture_icon_white }}", file_url(ICON_WHITE))
    html = html.replace("{{ font_poppins }}",        file_url(FONTS_DIR / "Poppins-Bold.ttf"))
    html = html.replace("{{ font_exo2 }}",           file_url(FONTS_DIR / "Exo2-SemiBold.otf"))
    html = html.replace("{{ font_biryani }}",        file_url(FONTS_DIR / "Biryani-Regular.ttf"))
    html = html.replace("{{ font_bigtimes }}",       file_url(FONTS_DIR / "Bigtimes.ttf"))
    html = html.replace("{{ destination }}",         destination.upper())
    html = html.replace("{{ price }}",               price)
    html = html.replace("{{ event_badge }}",         event_badge)
    html = html.replace("{{ event_badge_hidden }}",  "" if event_badge else "hidden")
    html = html.replace("{{ includes_text }}",       includes_text)
    html = html.replace("{{ includes_hidden }}",     "" if includes_text else "hidden")

    with tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(html)
        tmp_html = Path(f.name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page    = browser.new_page(viewport={"width": 1080, "height": 1920})
            page.goto(f"file:///{tmp_html.as_posix()}")
            page.wait_for_timeout(800)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(output_path),
                type="jpeg",
                quality=95,
                full_page=False,
                clip={"x": 0, "y": 0, "width": 1080, "height": 1920},
            )
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)

    print(f"  Story render saved: {output_path}")
    return output_path


# ── Standalone test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bg  = ASSETS / "background.jpg"
    out = OUTPUT_DIR / "turizem" / "test_story.jpg"

    print("Rendering test story...")
    render_story(
        bg_path       = bg,
        output_path   = out,
        destination   = "VERONA",
        price         = "159",
        event_badge   = "Oferta Verore",
        includes_text = "BILETA • HOTELI • TAKSAT",
    )
    print(f"Done -> {out}")
