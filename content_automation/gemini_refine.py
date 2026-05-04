"""
Gemini-powered iterative post refinement loop.

Each round:
1. Render the post with current settings
2. Send the rendered image to Gemini
3. Gemini critiques it, rates it, and returns updated parameters
4. Apply ALL parameter changes and re-render
5. Repeat until Gemini rates it >= 9/10
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime

from google import genai
from PIL import Image

from config import GEMINI_API_KEY
from text_overlay import overlay_text_and_logo

# ── Config ─────────────────────────────────────────────────────────────────────
BG_PATH    = Path("output/sharp_group/bg/bg_3eae4048.jpg")
POST_TEXT  = "Strategjia e qarte sjell sukses!"
OUT_PNG    = Path("output/sharp_group/post_001.png")
OUT_JPG    = Path("output/sharp_group/post_001.jpg")
LOG_PATH   = Path("output/sharp_group/gemini_refinement_log.txt")
MODEL      = "gemini-3-flash-preview"
MAX_ROUNDS = 8
MIN_RATING = 9

client = genai.Client(api_key=GEMINI_API_KEY)

# ── Default starting placement ─────────────────────────────────────────────────
DEFAULT_PLACEMENT = {
    "text_vertical":  "top",
    "text_color":     "black",
    "needs_overlay":  False,
    "overlay_vertical": "top",
    "text_align":     "left",
    "show_accent_bar": True,
    "show_brand_tag":  True,
    "logo_text_gap":  180,
}

# ── Prompts ────────────────────────────────────────────────────────────────────

FIRST_PROMPT = f"""
You are a world-class social media designer critiquing an Instagram post (1080x1350px).

This is the RAW BACKGROUND IMAGE. No text has been placed yet.

The post will have:
- Logo at top center (fixed, do not touch)
- Headline: "{POST_TEXT}"
- Optional orange accent bar above the headline
- Optional small "SHARP GROUP" brand tag at the very bottom

Study the image carefully and decide the IDEAL starting configuration.
Think like a top-tier designer. Be specific and demanding.

Respond with ONLY valid JSON, nothing else:
{{
  "text_vertical": "top",
  "text_color": "black" or "white",
  "needs_overlay": false,
  "overlay_vertical": "top",
  "text_align": "left" or "center",
  "show_accent_bar": true or false,
  "show_brand_tag": true or false,
  "logo_text_gap": 180,
  "rating": 0,
  "satisfied": false,
  "feedback": "explain your exact reasoning"
}}

Parameter guide:
- text_vertical: where the headline sits vertically (top/center/bottom)
- text_color: black or white — must contrast with that area
- needs_overlay: true if a dark band is needed behind text for readability
- overlay_vertical: must always match text_vertical
- text_align: left or center — should it align with the logo axis?
- show_accent_bar: the small orange dash above text — intentional or noisy?
- show_brand_tag: the tiny "SHARP GROUP" footer — adds value or clutters?
- logo_text_gap: pixels of space between logo bottom and text top (min 100, max 500)
- rating: 0 here since you haven't seen the rendered result
- satisfied: false here
"""

def build_review_prompt(round_num: int, prev_placement: dict) -> str:
    return f"""
You are a world-class social media designer reviewing a rendered Instagram post (1080x1350px).

This is Round {round_num}. I have attached the rendered image. Look at it very carefully.

Previous settings were:
- text_vertical  : {prev_placement['text_vertical']}
- text_align     : {prev_placement['text_align']}
- text_color     : {prev_placement['text_color']}
- needs_overlay  : {prev_placement['needs_overlay']}
- show_accent_bar: {prev_placement['show_accent_bar']}
- show_brand_tag : {prev_placement['show_brand_tag']}
- logo_text_gap  : {prev_placement['logo_text_gap']}px

Is this better than before? Be honest and demanding.
Ask yourself:
- Is the text perfectly readable and balanced?
- Does the alignment feel premium and intentional?
- Is there enough breathing room between logo and headline?
- Does every element earn its place, or does something clutter the design?
- Does this look like a world-class Instagram post?

Rate it /10. Only satisfied=true if rating >= 9.
If not satisfied, give EXACT new values that will fix the issues.

Respond with ONLY valid JSON, nothing else:
{{
  "text_vertical": "top" or "center" or "bottom",
  "text_color": "black" or "white",
  "needs_overlay": true or false,
  "overlay_vertical": "top" or "center" or "bottom",
  "text_align": "left" or "center",
  "show_accent_bar": true or false,
  "show_brand_tag": true or false,
  "logo_text_gap": <integer between 100 and 500>,
  "rating": <integer 1-10>,
  "satisfied": true or false,
  "feedback": "be very specific — what changed, what still needs fixing, what looks great"
}}

overlay_vertical must always match text_vertical.
satisfied must only be true if rating >= 9.
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def log(msg: str, logger):
    print(msg)
    logger.write(msg + "\n")
    logger.flush()


def extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return json.loads(text.strip())


def render(placement: dict):
    overlay_text_and_logo(BG_PATH, POST_TEXT, placement, OUT_PNG)
    overlay_text_and_logo(BG_PATH, POST_TEXT, placement, OUT_JPG)


def ask_gemini(prompt: str, image_path: Path, logger) -> dict:
    img          = Image.open(image_path)
    img_size_kb  = os.path.getsize(image_path) // 1024
    img_dims     = img.size

    log(f"  >> Attaching  : {image_path}", logger)
    log(f"     Dimensions : {img_dims[0]}x{img_dims[1]}px  |  Size: {img_size_kb} KB", logger)
    log(f"  >> Sending to : {MODEL}", logger)

    response = client.models.generate_content(
        model=MODEL,
        contents=[prompt, img],
    )
    raw = response.text
    log(f"  << Gemini says:\n{raw}", logger)
    return extract_json(raw)


def log_placement(placement: dict, logger):
    log(f"    text_vertical  : {placement.get('text_vertical')}", logger)
    log(f"    text_align     : {placement.get('text_align')}", logger)
    log(f"    text_color     : {placement.get('text_color')}", logger)
    log(f"    needs_overlay  : {placement.get('needs_overlay')}", logger)
    log(f"    show_accent_bar: {placement.get('show_accent_bar')}", logger)
    log(f"    show_brand_tag : {placement.get('show_brand_tag')}", logger)
    log(f"    logo_text_gap  : {placement.get('logo_text_gap')}px", logger)


# ── Main loop ──────────────────────────────────────────────────────────────────

def main():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as logger:

        log(f"{'='*60}", logger)
        log(f"  GEMINI REFINEMENT LOG", logger)
        log(f"  Model  : {MODEL}", logger)
        log(f"  Post   : {POST_TEXT}", logger)
        log(f"  Date   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", logger)
        log(f"  Goal   : Rating >= {MIN_RATING}/10", logger)
        log(f"{'='*60}", logger)

        # ── Round 0: analyze raw background ───────────────────────────────────
        log(f"\n[Round 0] Analyzing raw background image...", logger)
        result = ask_gemini(FIRST_PROMPT, BG_PATH, logger)
        placement = {**DEFAULT_PLACEMENT, **{k: result[k] for k in DEFAULT_PLACEMENT if k in result}}
        log(f"\n  Initial placement:", logger)
        log_placement(placement, logger)
        log(f"  Feedback: {result.get('feedback')}", logger)

        # ── Refinement rounds ──────────────────────────────────────────────────
        for round_num in range(1, MAX_ROUNDS + 1):
            log(f"\n{'-'*60}", logger)
            log(f"[Round {round_num}] Rendering post with current settings...", logger)
            render(placement)
            log(f"  Rendered -> {OUT_PNG}", logger)

            log(f"\n[Round {round_num}] Asking Gemini: is this better? what needs to change?", logger)
            result = ask_gemini(build_review_prompt(round_num, placement), OUT_PNG, logger)

            rating    = result.get("rating", 0)
            satisfied = result.get("satisfied", False)
            feedback  = result.get("feedback", "")

            log(f"\n  Gemini verdict:", logger)
            log(f"    Rating   : {rating}/10", logger)
            log(f"    Satisfied: {satisfied}", logger)
            log(f"    Feedback : {feedback}", logger)

            if satisfied and rating >= MIN_RATING:
                log(f"\n{'='*60}", logger)
                log(f"  Gemini approved! Rating: {rating}/10 after {round_num} round(s)", logger)
                log(f"  Final post: {OUT_PNG}", logger)
                log(f"{'='*60}", logger)
                break

            # Apply ALL updated params from Gemini
            new_placement = {**placement}
            for key in DEFAULT_PLACEMENT:
                if key in result:
                    new_placement[key] = result[key]

            log(f"\n  Applying Gemini's changes:", logger)
            for key in DEFAULT_PLACEMENT:
                old = placement.get(key)
                new = new_placement.get(key)
                changed = " <-- CHANGED" if old != new else ""
                log(f"    {key}: {old} -> {new}{changed}", logger)

            placement = new_placement

        else:
            log(f"\n  Reached max rounds ({MAX_ROUNDS}). Using last placement.", logger)

        log(f"\n  Log saved to: {LOG_PATH}", logger)
        log(f"\nDone!", logger)


if __name__ == "__main__":
    main()
