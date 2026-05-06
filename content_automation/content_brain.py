"""
Content brain:
1. generate_content_brief  -> theme + Albanian text + caption  (ChatGPT)
2. generate_image_prompts  -> 3 Fal.ai prompt variations via Gemini Vision (3 ref images attached)
"""

import json
import re
import base64
import random
from pathlib import Path
from PIL import Image
from openai import OpenAI
from google import genai as google_genai
from config import OPENAI_API_KEY, OPENAI_MODEL, GEMINI_API_KEY, PROFILES_DIR, HISTORY_DIR, ASSETS_DIR

GEMINI_MODEL = "gemini-3-flash-preview"

client        = OpenAI(api_key=OPENAI_API_KEY)
gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)


def load_profile(handle: str) -> dict:
    with open(PROFILES_DIR / f"{handle}.json", encoding="utf-8") as f:
        return json.load(f)


def load_history(handle: str) -> list[dict]:
    path = HISTORY_DIR / f"{handle}.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("posts", [])[-10:]


def pick_reference_images(handle: str, n: int = 3) -> list[Path]:
    upload_dir = ASSETS_DIR / handle / "uploaded_posts"
    all_images = list(upload_dir.glob("*.jpg")) + list(upload_dir.glob("*.png"))
    return random.sample(all_images, min(n, len(all_images)))


def encode_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# -- CALL 1: Theme + Albanian text + caption  (ChatGPT) ------------------------

def generate_content_brief(handle: str) -> dict:
    """
    Returns:
    {
        "theme": "...",
        "post_text": "...",   <- Albanian, goes ON the image
        "caption": "..."      <- Albanian, goes as Instagram caption
    }
    """
    profile  = load_profile(handle)
    history  = load_history(handle)

    recent_types     = [p["post_type"]  for p in history[-3:]]
    recent_headlines = [p["headline"]   for p in history[-5:]]

    brand_brain_path = ASSETS_DIR / handle / "BRAND.md"
    brand_brain = brand_brain_path.read_text(encoding="utf-8") if brand_brain_path.exists() else ""

    system = (
        "You are an expert Instagram content strategist for digital marketing agencies. "
        "Always respond with a valid JSON object only. No markdown, no explanation."
    )

    user = f"""
You must follow this brand guide exactly:
---
{brand_brain}
---

Recent post types used (do NOT repeat the last 2): {recent_types}
Recent headlines (do NOT repeat these): {recent_headlines}

Plan the next Instagram post following the brand guide above, especially section 15 (Copywriting Direction). Rules:

- post_text goes ON the image. Follow the copywriting style in section 15 — psychologically sharp, tension, perspective shift. NOT generic slogans. Max 15 words total. MUST be in Albanian. Wrap 1-3 key words in <span class="hl"> </span> for orange highlight. Use \n ONLY to separate distinct thought units (max 1 newline). NEVER use <br> tags. JavaScript will handle all line wrapping and font sizing automatically.
- caption is the Instagram caption — Albanian, up to 120 words, same emotionally intelligent tone as section 15. No corporate language. Include hashtags. End with "Behu me i mprehte me ne."
- theme is a short internal description (English) of what this post is about.

Respond with exactly this JSON:
{{
  "post_type": "tip|educational|case_study|promotional|testimonial|trend",
  "theme": "...",
  "post_text": "...",
  "caption": "..."
}}"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=800,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return json.loads(response.choices[0].message.content)


# -- CALL 2: 3 image prompts via Gemini Vision ---------------------------------

def _last_visual_style(handle: str) -> str:
    """Returns 'people' or 'graphics' based on the last post's visual_description."""
    history = load_history(handle)
    for post in reversed(history):
        desc = post.get("visual_description", "").lower()
        if any(w in desc for w in ["person", "people", "woman", "man", "human", "sitting", "scrolling", "editorial photo"]):
            return "people"
        if desc:
            return "graphics"
    return "graphics"


COMPOSITION_RULES = {
    "default": (
        "- Background must be off-white (#F9F9F9) or very light — never dark\n"
        "- Leave a calm, uncluttered area at the top center for logo and text overlay"
    ),
    "orange": (
        "- Background must be off-white (#F9F9F9) or very light — never dark\n"
        "- Leave a calm, uncluttered area at the top center for logo and text overlay\n"
        "- The final post will have a solid orange (#FF680B) background overlaid — keep the composition clean and minimal"
    ),
}


def generate_image_prompts(theme: str, post_text: str, ref_images: list[Path], handle: str = "sharp_group", layout: str = "default") -> list[str]:
    """
    Sends 3 reference images + theme to Gemini Vision.
    Returns 1 strategically chosen Fal.ai prompt for the BACKGROUND image
    (no text, no logo -- those are added programmatically).
    """
    pil_images = [Image.open(p) for p in ref_images]

    brand_brain_path = ASSETS_DIR / handle / "BRAND.md"
    brand_brain = brand_brain_path.read_text(encoding="utf-8") if brand_brain_path.exists() else ""

    last_style   = _last_visual_style(handle)
    next_style   = "people" if last_style == "graphics" else "graphics"
    style_instruction = (
        "IMPORTANT: The last post used 3D abstract graphics. This post MUST use Style B — a real photorealistic person in a business/digital context (studio quality, off-white background, full figure visible in bottom 40-50%, smart casual clothing, orange accent details). Follow section 16 of the brand guide exactly."
        if next_style == "people" else
        "IMPORTANT: The last post used a real person. This post MUST use Style A — a 3D abstract/geometric/symbolic composition. No people, no photographs. Follow section 16 of the brand guide exactly."
    )

    prompt_text = f"""You are a creative director for a digital marketing agency. Your job is to write one single Fal.ai image generation prompt that is strictly grounded in the brand guide below.

---
BRAND GUIDE:
{brand_brain}
---

Theme of the new post: "{theme}"
Text that will be placed on the image: "{post_text}"

{style_instruction}

The 3 reference images attached show the agency's existing posts. Study them to understand the visual level — but the new prompt must follow the BRAND GUIDE above, not just copy the references.

Your task: decide what the BEST possible visual concept is for this specific theme and text within the required style above, then write one detailed Fal.ai prompt for it. Think like a creative director, not a template.

Non-negotiable rules:
- Absolutely NO text, NO logos, NO letters anywhere in the image
- Orange (#FF680B) as the dominant accent color on key objects
- Black for depth, contrast, and grounding
- 3D objects must be matte or semi-gloss — clean lighting, soft shadows
- Vertical composition (4:5 ratio, 1080x1350px)
- Feel: modern, premium, minimal, professional digital marketing agency
{COMPOSITION_RULES[layout]}

Respond with ONLY valid JSON, nothing else:
{{
  "visual_concept": "one sentence explaining what you chose and why",
  "prompt": "the full detailed Fal.ai generation prompt"
}}"""

    contents = [prompt_text] + pil_images

    for attempt in range(3):
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
        )
        raw = response.text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        raw = raw.strip()
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            raw = m.group(0)
        try:
            data = json.loads(raw)
            print(f"  Visual concept: {data['visual_concept']}")
            return [data["prompt"]]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  Gemini JSON parse failed (attempt {attempt+1}/3): {e}, retrying...")

    raise RuntimeError("Gemini failed to return valid JSON after 3 attempts")
