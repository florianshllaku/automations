"""
Renders the Ventura Travel (turizem) post template via Playwright.
Loads templates/turizem.html, fills in values, screenshots at 1080x1350.

Usage (standalone test):
  py turizem_renderer.py
"""

import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import ASSETS_DIR, OUTPUT_DIR
from utils import file_url, strip_white_bg

HANDLE     = "turizem"
ASSETS     = ASSETS_DIR / HANDLE
LOGO_PATH  = ASSETS / "venture-travel-logo.png"
FONTS_DIR  = ASSETS / "fonts"
TEMPLATE   = Path(__file__).parent / "templates" / "turizem.html"


def render_post(
    bg_path:      Path,
    output_path:  Path,
    hotel_name:   str,
    destination:  str,
    days:         str,
    nights:       str,
    package_type: str,
    price:        str,
    event_badge:  str = "",
    hotel_label:  str = "HOTEL",
) -> Path:
    """
    Fill the turizem template and render it via Playwright.

    Args:
        bg_path:      Path to the background photo
        output_path:  Where to save the final JPEG
        hotel_name:   e.g. "QETESIA"
        destination:  e.g. "VELIPOJË"
        days:         e.g. "2"
        nights:       e.g. "1"
        package_type: e.g. "All Inclusive"
        price:        e.g. "45"
        event_badge:  Optional event label, e.g. "Festa e Bajramit në" (empty = hidden)
        hotel_label:  Badge left of hotel name, default "HOTEL"
    """
    html = TEMPLATE.read_text(encoding="utf-8")

    tmp_logo = Path(tempfile.mktemp(suffix="_logo.png"))
    strip_white_bg(LOGO_PATH, tmp_logo)

    html = html.replace("{{ bg_image }}",    file_url(bg_path))
    html = html.replace("{{ logo }}",        file_url(tmp_logo))
    html = html.replace("{{ font_poppins }}", file_url(FONTS_DIR / "Poppins-Bold.ttf"))
    html = html.replace("{{ font_brittany }}", file_url(FONTS_DIR / "BrittanySignature.ttf"))
    html = html.replace("{{ font_exo2 }}",   file_url(FONTS_DIR / "Exo2-SemiBold.otf"))
    html = html.replace("{{ font_capriola }}", file_url(FONTS_DIR / "Capriola-Regular.ttf"))
    html = html.replace("{{ font_biryani }}", file_url(FONTS_DIR / "Biryani-Regular.ttf"))
    html = html.replace("{{ bus_icon }}",     file_url(ASSETS / "bus-icon.png"))
    html = html.replace("{{ beach_icon }}",   file_url(ASSETS / "beach-icon.png"))
    html = html.replace("{{ luggage_icon }}", file_url(ASSETS / "luggage-icon.png"))
    html = html.replace("{{ phone_icon }}",   file_url(ASSETS / "phone-icon.png"))
    html = html.replace("{{ sun_icon }}",      file_url(ASSETS / "sun-icon.png"))
    html = html.replace("{{ moon_icon }}",     file_url(ASSETS / "moon-icon.png"))
    html = html.replace("{{ payment_icon }}", file_url(ASSETS / "payment.png"))
    html = html.replace("{{ hotel_name }}",  hotel_name)
    html = html.replace("{{ hotel_label }}",  hotel_label.upper())
    html = html.replace("{{ destination }}",  destination.upper())
    html = html.replace("{{ days }}",         days)
    html = html.replace("{{ nights }}",       nights)
    html = html.replace("{{ package_type }}", package_type)
    html = html.replace("{{ price }}",        price)
    html = html.replace("{{ event_badge }}",  event_badge)

    if not event_badge:
        html = html.replace('class="event-badge"', 'class="event-badge hidden"')

    with tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(html)
        tmp_html = Path(f.name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page    = browser.new_page(viewport={"width": 1080, "height": 1350})
            page.goto(f"file:///{tmp_html.as_posix()}")
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
        tmp_html.unlink(missing_ok=True)
        tmp_logo.unlink(missing_ok=True)

    print(f"  Turizem render saved: {output_path}")
    return output_path


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    bg  = ASSETS / "template.jpg"
    out = OUTPUT_DIR / "turizem" / "test_render.jpg"

    print("Rendering test post...")
    render_post(
        bg_path      = bg,
        output_path  = out,
        hotel_name   = "QETESIA",
        destination  = "VELIPOJË",
        days         = "2",
        nights       = "1",
        package_type = "All Inclusive",
        price        = "45",
        event_badge  = "Festa e Bajramit në",
        hotel_label  = "HOTEL",
    )
    print(f"Done -> {out}")
