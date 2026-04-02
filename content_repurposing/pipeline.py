import json
import os
import re
import urllib.request
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from logger import log

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

IMAGES_DIR = Path("article_images")
IMAGES_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = (
    "You are a research agent. "
    "You will receive the full text of a webpage that may contain multiple articles. "
    "Focus ONLY on the main article — the one whose title and topic match what was requested. "
    "Ignore any 'related articles', 'you may also like', or secondary content at the bottom. "
    "Extract the key information and return ONLY a valid JSON object with exactly these fields:\n"
    "  main_topic   — string: what the article is actually about\n"
    "  key_facts    — array of exactly 5 strings: most important facts\n"
    "  hook_angle   — string: the most surprising or controversial angle\n"
    "  best_quote   — string: the most quotable line from the article\n"
    "Return ONLY raw JSON. No markdown, no code fences, no explanation."
)

REEL_SYSTEM_PROMPT = (
    "You are a short-form video scriptwriter specialising in AI/tech reels (TikTok, Instagram Reels, YouTube Shorts). "
    "You will receive a research brief as JSON. Write a punchy ~45-50 second reel script and return ONLY a valid JSON object "
    "with exactly these fields:\n"
    "  title        — string: a short catchy title for the reel\n"
    "  runtime      — string: estimated runtime e.g. '~47 seconds'\n"
    "  tone         — string: e.g. 'calm and ominous', 'high energy', 'skeptical'\n"
    "  segments     — array of objects, each with:\n"
    "                   label       — string: e.g. 'HOOK', 'CONTEXT', 'TWIST', 'VISION', 'CTA'\n"
    "                   timestamp   — string: e.g. '0:00-0:05'\n"
    "                   on_screen   — string: bold text shown on screen (keep short, max 10 words)\n"
    "                   voiceover   — string: what the creator says out loud\n"
    "  b_roll       — array of strings: 4-6 b-roll / visual suggestions\n"
    "Return ONLY raw JSON. No markdown, no code fences, no explanation."
)

VISUAL_STYLES = {
    "glitch": (
        "Glitch art-inspired digital aesthetic. Images look intentionally corrupted, as if breaking or being rewritten by a machine. "
        "Human figures, logos, text, or charts appear slightly distorted using RGB channel separation, scanlines, digital noise, pixel sorting, or fragmented overlays. "
        "High-contrast colors — strong reds, blues, and blacks — often misaligned to create tension and visual vibration. "
        "One clear idea per frame, but with parts appearing unstable or glitched to reinforce the message. "
        "Screens, interfaces, or recognizable logos can be included but should feel digitally affected rather than clean. "
        "Raw, technological, and slightly chaotic — like a system under pressure or evolving in real time — while still readable and intentional."
    ),
    "vaporwave": (
        "Vaporwave-inspired aesthetic. Dreamy, nostalgic, and slightly surreal interpretation of digital culture and capitalism. "
        "Softened, retro-futuristic scenes using pastel gradients, neon tones, and smooth lighting that creates a calm but uncanny atmosphere. "
        "Human figures, logos, and objects are stylized and slightly unreal, placed within abstract environments like endless grids, horizons, or empty digital spaces. "
        "Colors lean toward pinks, purples, blues, and soft glows — creating depth and mood rather than realism. "
        "Simple composition centered around one clear idea per frame, expressed symbolically and atmospherically. "
        "Brands or devices can be included but integrated into a surreal digital dreamscape. "
        "Nostalgic, smooth, and reflective — like a slowed-down vision of the internet and business world."
    ),
    "algorithmic": (
        "Algorithmic or generative art approach. Images feel constructed by rules rather than drawn freely, using geometric shapes, grids, symmetry, and patterns to represent how systems operate. "
        "Human figures, icons, or objects are simplified into basic forms and placed within organized layouts that suggest order and scalability. "
        "Minimal and controlled color palette for clarity and precision. "
        "Lines, spacing, and repetition are key — showing how complexity emerges from simple rules. "
        "One main idea per frame, expressed through structure rather than metaphor alone. "
        "Platforms or workflows abstracted into systems of nodes, connections, or repeated units. "
        "Precise, intelligent, and systematic — like visualizing the logic behind technology and automation. "
        "The very bottom edge of the frame (roughly the last 20 pixels) should not be visually overwhelming — elements can exist there but keep it calm and uncluttered near that edge."
    ),
    "data": (
        "Data-driven art approach. Information itself is the visual composition — a blend between an infographic and an artistic data representation. "
        "Charts, numbers, flows, and metrics are not just supporting elements but the main subject. "
        "Human figures or real-world objects can provide context but are surrounded or shaped by data structures like graphs, timelines, percentages, or connected nodes. "
        "Colors used intentionally to differentiate meaning — green for growth, red for decline, blue for neutral systems — with an overall clean and readable palette. "
        "Lines, arrows, and connections show movement, relationships, and cause-effect. "
        "Simple composition focused on one key idea per frame, expressed through measurable or quantifiable visuals. "
        "Analytical, insightful, and grounded in reality — like seeing the hidden data behind a story."
    ),
}

VISUAL_SYSTEM_PROMPT = (
    "You are a visual director for short-form video content. "
    "You will receive a reel script as JSON with segments, each containing a label and voiceover. "
    "Your job: generate 8-12 visuals spread across the entire script — "
    "each image covers roughly 6-10 seconds of video, so plan accordingly. "
    "Include the hook, every key turning point, the main revelation, supporting context beats, and the call to action. "
    "Multiple visuals per segment is encouraged — break segments into sub-moments. "
    "One main idea per frame — bold, striking, and punchy. "
    "CRITICAL for image_prompt: every image MUST include bold text or keywords directly embedded in the scene — "
    "short words, stats, or phrases (1-4 words max) rendered as large, high-contrast text within the composition. "
    "These are NOT subtitles — they are part of the image itself, integrated into the visual design. "
    "Examples: a giant '$122B' floating above a skyline, 'NO MANAGERS' stamped across a figure, 'AI FIRST' as neon signage. "
    "Return ONLY a valid JSON array of 8-12 objects, each with exactly these fields:\n"
    "  label         — string: the segment label this image belongs to (e.g. 'HOOK', 'TWIST')\n"
    "  visual_tag    — string: a short cinematic scene description, 10-20 words, "
    "                  e.g. 'tired man sitting alone on edge of bed before sunrise, dim blue room light, heavy quiet mood, cinematic handheld'\n"
    "  voiceover     — string: the voiceover line(s) this image covers (copy from input)\n"
    "  image_prompt  — string: a full ready-to-paste image generation prompt — describe the bold scene with embedded text/keywords in vivid detail "
    "                  then append the exact visual style specification provided\n"
    "Return ONLY raw JSON array. No markdown, no code fences, no explanation."
)


# ---------------------------------------------------------------------------
# Article fetching
# ---------------------------------------------------------------------------

def fetch_article(url: str) -> tuple[str, str | None]:
    """
    Load the article page in a headless browser.
    Returns (main_article_text, image_url).
    Strips nav / footer / related-articles sections before extracting text.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ))
        page.goto(url, wait_until="networkidle", timeout=30000)

        # Remove noise sections, then extract the main article text
        article_text = page.evaluate("""() => {
            // Remove sections that are NOT the main article
            document.querySelectorAll(
                'nav, footer, header, aside, ' +
                '[class*="related"], [class*="recommended"], [class*="sidebar"], ' +
                '[id*="related"], [id*="recommended"]'
            ).forEach(el => el.remove());

            // Try specific article containers first
            const candidates = [
                'article',
                '[class*="article-body"]',
                '[class*="post-body"]',
                '[class*="post-content"]',
                '[class*="entry-content"]',
                'main',
            ];
            for (const sel of candidates) {
                const el = document.querySelector(sel);
                if (el && el.innerText.trim().length > 300) {
                    return el.innerText.trim();
                }
            }
            return document.body.innerText.trim();
        }""")

        # Find the first meaningful image in the article area
        image_url = page.evaluate("""() => {
            const selectors = [
                'article img',
                '[class*="article"] img',
                '[class*="hero"] img',
                '[class*="post"] img',
                'main img',
                'meta[property="og:image"]',
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (!el) continue;
                const src = el.src || el.getAttribute('content') || '';
                // Skip tiny icons, logos, avatars
                if (src && !/logo|avatar|icon|pixel|tracking/i.test(src)) {
                    return src.startsWith('http') ? src : null;
                }
            }
            return null;
        }""")

        browser.close()
    return article_text, image_url


# ---------------------------------------------------------------------------
# Image download
# ---------------------------------------------------------------------------

def download_image(image_url: str, article_url: str) -> str | None:
    """Download the article image to article_images/ and return the local path."""
    if not image_url:
        return None
    try:
        slug = article_url.rstrip("/").split("/")[-1]
        ext = image_url.split("?")[0].rsplit(".", 1)[-1].lower()
        if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
            ext = "jpg"
        dest = IMAGES_DIR / f"{slug}.{ext}"

        req = urllib.request.Request(
            image_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            dest.write_bytes(resp.read())
        return str(dest)
    except Exception as e:
        print(f"  Image download failed: {e}", flush=True)
        return None


# ---------------------------------------------------------------------------
# Claude call
# ---------------------------------------------------------------------------

def _call_claude(article_text: str, retry: bool = False) -> dict:
    """Send article text to Claude and parse the returned JSON."""
    if retry:
        user_content = (
            "Article text below. Reply with ONLY a raw JSON object, zero markdown:\n\n"
            + article_text[:8000]
        )
    else:
        user_content = article_text[:12000]

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        response = stream.get_final_message()

    text = next((b.text for b in response.content if b.type == "text"), "")
    # Strip accidental markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def research_article(url: str) -> dict:
    """
    Fetch the article at `url`, analyse it with Claude, and return a dict:
      {
        "main_topic":        str,
        "key_facts":         [str, str, str, str, str],
        "hook_angle":        str,
        "best_quote":        str,
        "downloaded_image":  str | None   # local file path
      }
    Retries the Claude call once with a stricter prompt if JSON parsing fails.
    """
    log(f"Fetching article: {url}")
    print(f"  Fetching article content: {url}", flush=True)
    article_text, image_url = fetch_article(url)
    log(f"Article fetched ({len(article_text)} chars): {url}")

    print(f"  Downloading image ...", flush=True)
    image_path = download_image(image_url, url)
    if image_path:
        log(f"Image downloaded: {image_path}")
    else:
        log(f"No image available for: {url}")

    log("Calling Claude (research)")
    print(f"  Calling Claude for research ...", flush=True)
    try:
        result = _call_claude(article_text)
    except (json.JSONDecodeError, ValueError) as e:
        log(f"Claude research JSON parse failed ({e}), retrying", level="ERROR")
        print(f"  JSON parse failed ({e}), retrying ...", flush=True)
        result = _call_claude(article_text, retry=True)
    log(f"Claude research complete — topic: {result.get('main_topic', 'N/A')}")

    result["downloaded_image"] = image_path
    return result


def generate_reel_script(research: dict) -> dict:
    """
    Takes a research dict and returns a structured reel script JSON:
      {
        "title":    str,
        "runtime":  str,
        "tone":     str,
        "segments": [{"label", "timestamp", "on_screen", "voiceover"}, ...],
        "b_roll":   [str, ...]
      }
    Retries once with a stricter prompt if JSON parsing fails.
    """
    brief = {k: v for k, v in research.items() if k != "downloaded_image"}
    user_content = json.dumps(brief, ensure_ascii=False)

    log("Calling Claude (reel script)")
    print("  Generating reel script ...", flush=True)

    def _call(retry: bool = False) -> dict:
        content = (
            "Research brief below. Reply with ONLY a raw JSON object, zero markdown:\n\n" + user_content
            if retry else user_content
        )
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=REEL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        ) as stream:
            response = stream.get_final_message()
        text = next((b.text for b in response.content if b.type == "text"), "")
        text = re.sub(r"^```(?:json)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    try:
        result = _call()
    except (json.JSONDecodeError, ValueError) as e:
        log(f"Reel script JSON parse failed ({e}), retrying", level="ERROR")
        print(f"  Reel JSON parse failed ({e}), retrying ...", flush=True)
        result = _call(retry=True)
    log(f"Reel script complete — title: {result.get('title', 'N/A')}, runtime: {result.get('runtime', 'N/A')}")
    return result


def generate_visual_prompts(reel: dict, style: str) -> list[dict]:
    """
    Takes a reel script dict and a style key (one of VISUAL_STYLES) and returns
    a list of visual prompt objects:
      [
        {
          "label":        str,
          "visual_tag":   str,
          "voiceover":    str,
          "image_prompt": str,
        },
        ...
      ]
    Retries once with a stricter prompt if JSON parsing fails.
    """
    segments = [
        {
            "label": seg.get("label", ""),
            "timestamp": seg.get("timestamp", ""),
            "voiceover": seg.get("voiceover", ""),
        }
        for seg in reel.get("segments", [])
        if seg.get("voiceover")
    ]
    user_content = json.dumps(
        {"title": reel.get("title", ""), "tone": reel.get("tone", ""), "segments": segments, "visual_style": VISUAL_STYLES[style]},
        ensure_ascii=False,
    )

    log("Calling Claude (visual prompts)")
    print("  Generating visual prompts ...", flush=True)

    def _call(retry: bool = False) -> list:
        content = (
            "Segments below. Reply with ONLY a raw JSON array, zero markdown:\n\n" + user_content
            if retry else user_content
        )
        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=VISUAL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        ) as stream:
            response = stream.get_final_message()
        text = next((b.text for b in response.content if b.type == "text"), "")
        text = re.sub(r"^```(?:json)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    try:
        result = _call()
    except (json.JSONDecodeError, ValueError) as e:
        log(f"Visual prompts JSON parse failed ({e}), retrying", level="ERROR")
        print(f"  Visual prompts JSON parse failed ({e}), retrying ...", flush=True)
        result = _call(retry=True)
    log(f"Visual prompts complete — {len(result)} frames generated")
    return result
