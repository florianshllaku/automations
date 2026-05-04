"""
1. Gemini Vision analyzes the background image -> 3 placement options (up to 3 Gemini calls)
2. Pillow draws the post text + logo on the image
"""

import json
import re
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI
from google import genai as google_genai
from config import OPENAI_API_KEY, OPENAI_MODEL, GEMINI_API_KEY, ASSETS_DIR, INSTAGRAM_WIDTH, INSTAGRAM_HEIGHT

client        = OpenAI(api_key=OPENAI_API_KEY)
gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL  = "gemini-3-flash-preview"

HANDLE        = "sharp_group"
FONT_BOLD     = ASSETS_DIR / HANDLE / "fonts" / "Poppins-Bold.ttf"
FONT_SEMIBOLD = ASSETS_DIR / HANDLE / "fonts" / "Poppins-SemiBold.ttf"
LOGO_PATH     = ASSETS_DIR / HANDLE / "logo.png"

ORANGE = (255, 134, 67)
BLACK  = (8, 8, 8)
WHITE  = (255, 255, 255)

LOGO_WIDTH = 900   # px — width the logo is scaled to
LOGO_Y     = 150   # px — distance from top of image


def encode_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ── GPT Vision: where to place text ───────────────────────────────────────────

def analyze_placement(image_path: Path, post_text: str) -> dict:
    """
    Asks GPT-4o Vision where the calmest area of the image is
    so text will be readable. Returns placement dict.
    """
    b64 = encode_image(image_path)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=300,
        response_format={"type": "json_object"},
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""This is a background image for an Instagram post.
The text "{post_text}" will be placed on it.

Analyze the image and find the calmest, most visually uncluttered area where bold text will be most readable.

Respond with exactly this JSON:
{{
  "text_vertical": "top" | "center" | "bottom",
  "text_color": "white" | "black",
  "needs_overlay": true | false,
  "overlay_vertical": "top" | "center" | "bottom"
}}

Rules:
- text_color: choose whichever contrasts best with the calm area
- needs_overlay: true if the calm area still isn't clean enough for text, false if text can sit directly
- overlay_vertical must match text_vertical"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}",
                        "detail": "high"
                    }
                }
            ]
        }]
    )
    return json.loads(response.choices[0].message.content)


# -- Gemini Vision: 3 placement options (up to 3 calls) -----------------------

_PLACEMENT_STYLES = [
    (
        "bold and high-contrast",
        "Maximize readability. Use a strong overlay band if needed, "
        "high contrast text color, and a prominent accent bar. "
        "Prioritize text legibility above all else.",
    ),
    (
        "minimal and clean",
        "Let the background breathe. Avoid overlay bands if possible. "
        "Choose text placement in the calmest natural area of the image. "
        "Prefer no accent bar for a premium, understated feel.",
    ),
    (
        "centered and balanced",
        "Symmetric composition. Center-align the text for a magazine-style layout. "
        "Use the center of the image. Logo and text should feel like one unified block.",
    ),
]

_PLACEMENT_PROMPT = """You are a world-class social media designer.

This is a background image for an Instagram post (1080x1350px, 4:5).
The text "{post_text}" will be placed on it.
A logo sits at the very top center (fixed -- do not adjust).

Design philosophy for THIS option: {style_name}
Guidance: {style_desc}

Analyze the image carefully and return placement settings that perfectly match this philosophy.

Respond with ONLY valid JSON, nothing else:
{{
  "text_vertical": "top" or "center" or "bottom",
  "text_color": "white" or "black",
  "needs_overlay": true or false,
  "overlay_vertical": "top" or "center" or "bottom",
  "text_align": "left" or "center",
  "show_accent_bar": true or false,
  "show_brand_tag": true or false,
  "logo_text_gap": <integer between 100 and 500>,
  "style_label": "{style_name}"
}}

Rules:
- overlay_vertical must always match text_vertical
- text_color must contrast well with the chosen text area
- logo_text_gap is pixels between logo bottom and text top (100-500)
"""


def get_placement_options_gemini(image_path: Path, post_text: str, n: int = 3) -> list[dict]:
    """
    Calls Gemini up to n times (max 3), each time asking for a different
    layout philosophy. Returns a list of placement dicts.
    """
    img     = Image.open(image_path)
    options = []

    for style_name, style_desc in _PLACEMENT_STYLES[:min(n, 3)]:
        prompt = _PLACEMENT_PROMPT.format(
            post_text=post_text,
            style_name=style_name,
            style_desc=style_desc,
        )
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt, img],
        )
        raw = response.text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        placement = json.loads(raw.strip())
        options.append(placement)
        print(f"    Option {len(options)} [{style_name}]: {placement}")

    return options


# ── Pillow: draw everything ────────────────────────────────────────────────────

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = font.getbbox(test)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_overlay(draw: ImageDraw.ImageDraw, vertical: str, img_h: int, img_w: int, overlay_h: int):
    """Draw a semi-transparent band behind the text area."""
    if vertical == "top":
        y0, y1 = 0, overlay_h
    elif vertical == "bottom":
        y0, y1 = img_h - overlay_h, img_h
    else:
        mid = img_h // 2
        y0, y1 = mid - overlay_h // 2, mid + overlay_h // 2

    overlay = Image.new("RGBA", (img_w, y1 - y0), (0, 0, 0, 140))
    return overlay, y0


def overlay_text_and_logo(
    bg_path: Path,
    post_text: str,
    placement: dict,
    output_path: Path,
) -> Path:
    img = Image.open(bg_path).convert("RGBA")
    W, H = img.size

    padding      = int(W * 0.08)        # 8% side padding
    max_text_w   = W - 2 * padding
    font_size    = 260
    line_spacing = 24

    # ── Design params from Gemini feedback ────────────────────────────────────
    text_align      = placement.get("text_align", "left")          # "left" | "center"
    show_accent_bar = placement.get("show_accent_bar", True)
    show_brand_tag  = placement.get("show_brand_tag", True)
    logo_text_gap   = placement.get("logo_text_gap", 180)          # px gap after logo

    font = ImageFont.truetype(str(FONT_BOLD), font_size)
    lines = wrap_text(post_text, font, max_text_w)

    # Shrink font until it fits within 50% of image height
    while font_size > 72:
        font  = ImageFont.truetype(str(FONT_BOLD), font_size)
        lines = wrap_text(post_text, font, max_text_w)
        total_h = len(lines) * (font_size + line_spacing)
        if total_h < H * 0.5:
            break
        font_size -= 4

    total_text_h = len(lines) * (font_size + line_spacing)
    vertical     = placement.get("text_vertical", "center")
    text_color   = WHITE if placement.get("text_color", "white") == "white" else BLACK

    if vertical == "top":
        text_y_start = padding + logo_text_gap
    elif vertical == "bottom":
        text_y_start = H - total_text_h - padding - 60
    else:
        text_y_start = (H - total_text_h) // 2

    # ── Optional overlay band ──────────────────────────────────────────────────
    if placement.get("needs_overlay", False):
        overlay_h = total_text_h + padding * 2
        overlay_img, overlay_y = draw_overlay(
            None, vertical, H, W, overlay_h
        )
        img.paste(overlay_img, (0, overlay_y), overlay_img)

    draw = ImageDraw.Draw(img)

    # ── Accent bar (orange) ────────────────────────────────────────────────────
    if show_accent_bar:
        bar_w, bar_h = 70, 7
        bar_x = padding if text_align == "left" else (W - 70) // 2
        bar_y = text_y_start - 44
        draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=4, fill=ORANGE)

    # ── Text lines with shadow ─────────────────────────────────────────────────
    y = text_y_start
    for line in lines:
        line_bbox = font.getbbox(line)
        line_w    = line_bbox[2] - line_bbox[0]
        if text_align == "center":
            x = (W - line_w) // 2
        else:
            x = padding
        # Shadow
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 120))
        # Main text
        draw.text((x, y), line, font=font, fill=text_color)
        y += font_size + line_spacing

    # ── Logo (top center) ─────────────────────────────────────────────────────
    if LOGO_PATH.exists():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo = logo.crop(logo.getbbox())
        ratio  = LOGO_WIDTH / logo.width
        logo_h = int(logo.height * ratio)
        logo   = logo.resize((LOGO_WIDTH, logo_h), Image.LANCZOS)
        logo_x = (W - LOGO_WIDTH) // 2
        img.paste(logo, (logo_x, LOGO_Y), logo)

    # ── Bottom brand tag ───────────────────────────────────────────────────────
    if show_brand_tag:
        try:
            small_font = ImageFont.truetype(str(FONT_SEMIBOLD), 28)
        except Exception:
            small_font = font
        brand_text = "SHARP GROUP"
        bbox       = small_font.getbbox(brand_text)
        brand_w    = bbox[2] - bbox[0]
        draw.text(((W - brand_w) // 2, H - 64), brand_text, font=small_font, fill=ORANGE)

    # ── Save ──────────────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final = img.convert("RGB")
    final.save(str(output_path), "JPEG", quality=95)
    print(f"  Final post saved: {output_path}")
    return output_path
