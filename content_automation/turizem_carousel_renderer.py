"""
Renders the Ventura Travel carousel cover template via Playwright.

Usage (standalone test):
  py turizem_carousel_renderer.py
"""

import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from config import ASSETS_DIR, OUTPUT_DIR
from utils import file_url, strip_white_bg


def _bg_brightness_at_logo(bg_path: Path, x: int = 36, y: int = 28, w: int = 220, h: int = 90) -> float:
    """Return perceived luminance (0-255) of the logo region in the background image."""
    img = Image.open(bg_path).convert("RGB")
    # Scale sample region to actual image size
    iw, ih = img.size
    sx = int(x * iw / 1080)
    sy = int(y * ih / 1080)
    sw = int(w * iw / 1080)
    sh = int(h * ih / 1080)
    region = img.crop((sx, sy, sx + sw, sy + sh))
    pixels = list(region.getdata())
    n = len(pixels)
    # Perceived luminance: 0.299R + 0.587G + 0.114B
    avg = sum(0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels) / n
    return avg

HANDLE     = "turizem"
ASSETS     = ASSETS_DIR / HANDLE
LOGO_BLUE  = ASSETS / "venture-travel-logo.png"
LOGO_WHITE = ASSETS / "venture-travel-logo-whtie.png"
FONTS_DIR  = ASSETS / "fonts"
TEMPLATES  = Path(__file__).parent / "templates"


def render_carousel_cover(
    template_name: str,
    bg_path:       Path,
    output_path:   Path,
    hotel_name:    str,
    destination:   str,
    days:          str,
    nights:        str,
    price:         str,
    date_from:     str,
    date_to:       str,
    event_badge:   str = "",
    hotel_label:   str = "HOTEL",
    season_tag:    str = "VERA",
    year_tag:      str = "2026",
    month:         str = "",
    logo_variant:  str = "white",   # "white" | "blue" | "auto"
) -> Path:
    """
    Fill a carousel cover template and render via Playwright.

    date_from / date_to: e.g. "17 Maj" / "23 Maj"
    logo_variant: "white" = always white, "blue" = always blue, "auto" = JS brightness pick
    """
    template_path = TEMPLATES / template_name
    html = template_path.read_text(encoding="utf-8")

    tmp_logo_blue = Path(tempfile.mktemp(suffix="_logo_blue.png"))
    strip_white_bg(LOGO_BLUE, tmp_logo_blue)

    # Resolve which logo to use
    if logo_variant == "auto":
        brightness = _bg_brightness_at_logo(bg_path)
        resolved = "blue" if brightness >= 80 else "white"
        print(f"  Logo auto-pick: brightness={brightness:.1f} -> {resolved}")
    else:
        resolved = logo_variant  # "blue" or "white"

    logo_src = file_url(tmp_logo_blue) if resolved == "blue" else file_url(LOGO_WHITE)

    html = html.replace("{{ bg_image }}",       file_url(bg_path))
    html = html.replace("{{ logo_src }}",       logo_src)
    html = html.replace("{{ logo_blue }}",      file_url(tmp_logo_blue))
    html = html.replace("{{ logo_white }}",     file_url(LOGO_WHITE))
    html = html.replace("{{ logo_variant }}",   logo_variant)
    html = html.replace("{{ font_poppins }}",   file_url(FONTS_DIR / "Poppins-Bold.ttf"))
    html = html.replace("{{ font_bigtimes }}",  file_url(FONTS_DIR / "Bigtimes.otf"))
    html = html.replace("{{ font_guarantia }}", file_url(FONTS_DIR / "Guarantia_PERSONAL_USE_ONLY.otf"))
    html = html.replace("{{ font_exo2 }}",      file_url(FONTS_DIR / "Exo2-SemiBold.otf"))
    html = html.replace("{{ font_biryani }}",   file_url(FONTS_DIR / "Biryani-Regular.ttf"))
    html = html.replace("{{ sun_icon }}",       file_url(ASSETS / "sun-icon.png"))
    html = html.replace("{{ moon_icon }}",      file_url(ASSETS / "moon-icon.png"))
    html = html.replace("{{ phone_icon }}",     file_url(ASSETS / "phone-icon.png"))
    html = html.replace("{{ payment_icon }}",   file_url(ASSETS / "payment.png"))
    html = html.replace("{{ bus_icon }}",       file_url(ASSETS / "bus-icon.png"))
    html = html.replace("{{ beach_icon }}",     file_url(ASSETS / "beach-icon.png"))
    html = html.replace("{{ luggage_icon }}",   file_url(ASSETS / "luggage-icon.png"))
    html = html.replace("{{ hotel_name }}",     hotel_name)
    html = html.replace("{{ hotel_label }}",    hotel_label.upper())
    html = html.replace("{{ destination }}",    destination)
    html = html.replace("{{ days }}",           days)
    html = html.replace("{{ nights }}",         nights)
    html = html.replace("{{ price }}",          price)
    html = html.replace("{{ date_from }}",      date_from)
    html = html.replace("{{ date_to }}",        date_to)
    html = html.replace("{{ month }}",          month)
    html = html.replace("{{ month_hidden }}",   "" if month else "hidden")
    html = html.replace("{{ event_badge }}",    event_badge)
    html = html.replace("{{ season_tag }}",     season_tag)
    html = html.replace("{{ year_tag }}",       year_tag)

    if not event_badge:
        html = html.replace('class="bookmark"', 'class="bookmark hidden"')

    with tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(html)
        tmp_html = Path(f.name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1080})
            page.goto(f"file:///{tmp_html.as_posix()}")
            page.wait_for_timeout(1000)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(output_path),
                type="jpeg", quality=95,
                full_page=False,
                clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
            )
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)
        tmp_logo_blue.unlink(missing_ok=True)

    print(f"  Carousel cover saved: {output_path}")
    return output_path


BORDER_VARIANTS = {
    # 1 — Double line: thin outer + hairline inner, bold L-corners
    1: (
        """
        .f-out  { position:absolute; inset:36px; border:1.5px solid rgba(255,255,255,0.55); z-index:10; pointer-events:none; }
        .f-in   { position:absolute; inset:50px; border:1px   solid rgba(255,255,255,0.22); z-index:10; pointer-events:none; }
        .fc { position:absolute; z-index:12; pointer-events:none; }
        .fc.tl { top:36px;    left:36px;  width:60px; height:60px; border-top:3px solid #fff; border-left:3px solid #fff; }
        .fc.tr { top:36px;    right:36px; width:60px; height:60px; border-top:3px solid #fff; border-right:3px solid #fff; }
        .fc.bl { bottom:36px; left:36px;  width:60px; height:60px; border-bottom:3px solid #fff; border-left:3px solid #fff; }
        .fc.br { bottom:36px; right:36px; width:60px; height:60px; border-bottom:3px solid #fff; border-right:3px solid #fff; }
        """,
        """<div class="f-out"></div><div class="f-in"></div>
        <div class="fc tl"></div><div class="fc tr"></div><div class="fc bl"></div><div class="fc br"></div>"""
    ),
    # 2 — Single frame + diamond corners, top border split with logo gap
    2: (
        """
        /* right / bottom / left borders */
        .f-main { position:absolute; inset:52px; border-right:2px solid rgba(255,255,255,0.60); border-bottom:2px solid rgba(255,255,255,0.60); border-left:2px solid rgba(255,255,255,0.60); z-index:10; pointer-events:none; }
        /* top border — left segment */
        .f-top-l { position:absolute; top:52px; left:52px; width:calc(50% - 52px - 200px); height:0; border-top:2px solid rgba(255,255,255,0.60); z-index:10; pointer-events:none; }
        /* top border — right segment */
        .f-top-r { position:absolute; top:52px; right:52px; width:calc(50% - 52px - 200px); height:0; border-top:2px solid rgba(255,255,255,0.60); z-index:10; pointer-events:none; }
        /* diamond corner ornaments */
        .fdiam  { position:absolute; z-index:12; width:14px; height:14px; background:#fff; transform:rotate(45deg); pointer-events:none; }
        .fdiam.tl { top:45px;    left:45px; }
        .fdiam.tr { top:45px;    right:45px; }
        .fdiam.bl { bottom:45px; left:45px; }
        .fdiam.br { bottom:45px; right:45px; }
        """,
        """<div class="f-main"></div>
        <div class="f-top-l"></div><div class="f-top-r"></div>
        <div class="fdiam tl"></div><div class="fdiam tr"></div><div class="fdiam bl"></div><div class="fdiam br"></div>"""
    ),
    # 3 — Triple thin lines (very close together, luxury print feel)
    3: (
        """
        .f1 { position:absolute; inset:38px; border:1px solid rgba(255,255,255,0.70); z-index:10; pointer-events:none; }
        .f2 { position:absolute; inset:44px; border:1px solid rgba(255,255,255,0.35); z-index:10; pointer-events:none; }
        .f3 { position:absolute; inset:50px; border:1px solid rgba(255,255,255,0.18); z-index:10; pointer-events:none; }
        """,
        """<div class="f1"></div><div class="f2"></div><div class="f3"></div>"""
    ),
    # 4 — Thick outer frame + long bold corner L-marks only (no inner line)
    4: (
        """
        .f-thick { position:absolute; inset:40px; border:2.5px solid rgba(255,255,255,0.45); z-index:10; pointer-events:none; }
        .fc { position:absolute; z-index:12; pointer-events:none; }
        .fc.tl { top:40px;    left:40px;  width:110px; height:110px; border-top:4px solid #fff; border-left:4px solid #fff; }
        .fc.tr { top:40px;    right:40px; width:110px; height:110px; border-top:4px solid #fff; border-right:4px solid #fff; }
        .fc.bl { bottom:40px; left:40px;  width:110px; height:110px; border-bottom:4px solid #fff; border-left:4px solid #fff; }
        .fc.br { bottom:40px; right:40px; width:110px; height:110px; border-bottom:4px solid #fff; border-right:4px solid #fff; }
        """,
        """<div class="f-thick"></div>
        <div class="fc tl"></div><div class="fc tr"></div><div class="fc bl"></div><div class="fc br"></div>"""
    ),
    # 5 — Double line + mid-side tick marks (ornamental, high-end)
    5: (
        """
        .f-o { position:absolute; inset:36px; border:1.5px solid rgba(255,255,255,0.55); z-index:10; pointer-events:none; }
        .f-i { position:absolute; inset:48px; border:1px   solid rgba(255,255,255,0.25); z-index:10; pointer-events:none; }
        /* mid-side ticks on the outer frame */
        .ftick { position:absolute; z-index:12; background:#fff; opacity:0.70; pointer-events:none; }
        .ftick.t  { top:28px;  left:50%; transform:translateX(-50%); width:28px; height:4px; }
        .ftick.b  { bottom:28px; left:50%; transform:translateX(-50%); width:28px; height:4px; }
        .ftick.l  { left:28px; top:50%; transform:translateY(-50%); width:4px; height:28px; }
        .ftick.r  { right:28px; top:50%; transform:translateY(-50%); width:4px; height:28px; }
        """,
        """<div class="f-o"></div><div class="f-i"></div>
        <div class="ftick t"></div><div class="ftick b"></div><div class="ftick l"></div><div class="ftick r"></div>"""
    ),
}


def render_carousel_slide(
    bg_path:        Path,
    output_path:    Path,
    slide_title:    str  = "",
    slide_subtitle: str  = "",
    logo_variant:   str  = "white",
    border_variant: int  = 2,
) -> Path:
    """
    Render a simple inner carousel slide — framed background + logo.

    slide_title:    optional large Bigtimes title (empty = hidden)
    slide_subtitle: optional small Exo2 subtitle (empty = hidden)
    logo_variant:   "auto" | "blue" | "white"
    border_variant: 1-5
    """
    frame_css, frame_html = BORDER_VARIANTS[border_variant]
    template_path = TEMPLATES / "turizem_carousel_slide.html"
    html = template_path.read_text(encoding="utf-8")

    tmp_logo_blue = Path(tempfile.mktemp(suffix="_logo_blue.png"))
    strip_white_bg(LOGO_BLUE, tmp_logo_blue)

    if logo_variant == "auto":
        brightness = _bg_brightness_at_logo(bg_path)
        resolved = "blue" if brightness >= 80 else "white"
        print(f"  Logo auto-pick: brightness={brightness:.1f} -> {resolved}")
    else:
        resolved = logo_variant

    logo_src = file_url(tmp_logo_blue) if resolved == "blue" else file_url(LOGO_WHITE)

    html = html.replace("{{ bg_image }}",        file_url(bg_path))
    html = html.replace("{{ logo_src }}",         logo_src)
    html = html.replace("{{ font_poppins }}",     file_url(FONTS_DIR / "Poppins-Bold.ttf"))
    html = html.replace("{{ font_bigtimes }}",    file_url(FONTS_DIR / "Bigtimes.otf"))
    html = html.replace("{{ font_exo2 }}",        file_url(FONTS_DIR / "Exo2-SemiBold.otf"))
    html = html.replace("{{ slide_title }}",      slide_title)
    html = html.replace("{{ slide_subtitle }}",   slide_subtitle)
    html = html.replace("{{ title_hidden }}",     "" if slide_title else "hidden")
    html = html.replace("{{ subtitle_hidden }}",  "" if slide_subtitle else "hidden")
    html = html.replace("{{ frame_css }}",        frame_css)
    html = html.replace("{{ frame_html }}",       frame_html)

    with tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(html)
        tmp_html = Path(f.name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1080})
            page.goto(f"file:///{tmp_html.as_posix()}")
            page.wait_for_timeout(800)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(output_path),
                type="jpeg", quality=95,
                full_page=False,
                clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
            )
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)
        tmp_logo_blue.unlink(missing_ok=True)

    print(f"  Carousel slide saved: {output_path}")
    return output_path


# ── Standalone test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bg  = ASSETS / "background.jpg"
    out = OUTPUT_DIR / "turizem" / "test_carousel_cover_v2.jpg"

    print("Rendering carousel cover v2 test...")
    render_carousel_cover(
        template_name = "turizem_carousel_cover_v2.html",
        bg_path       = bg,
        output_path   = out,
        hotel_name    = "SENZA THE INN RESORT",
        destination   = "Antalya",
        days          = "7",
        nights        = "6",
        price         = "449",
        date_from     = "17 Maj",
        date_to       = "23 Maj",
        event_badge   = "OFERTA VERORE",
        logo_variant  = "auto",
    )
    print(f"Done -> {out}")

    for v in range(1, 6):
        out_v = OUTPUT_DIR / "turizem" / f"test_slide_border_v{v}.jpg"
        print(f"Rendering slide border variant {v}...")
        render_carousel_slide(
            bg_path        = bg,
            output_path    = out_v,
            slide_title    = "Antalya",
            slide_subtitle = "Vera 2026",
            logo_variant   = "white",
            border_variant = v,
        )
        print(f"Done -> {out_v}")
