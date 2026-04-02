import json
import os
import re
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from telegram_bot import send_approval_message, wait_for_approval, send_message, send_audio, send_generated_images, send_document
from pipeline import research_article, generate_reel_script, generate_visual_prompts, VISUAL_STYLES
from voice import generate_audio
from image_gen import generate_images_for_visuals
from video import generate_srt, generate_video
from logger import log, init_run_log, write_raw


class _Tee:
    """Wraps a stream (stdout or stderr) and mirrors all writes to the run log file."""
    def __init__(self, stream):
        self._stream = stream

    def write(self, data):
        self._stream.write(data)
        write_raw(data)

    def flush(self):
        self._stream.flush()

    def reconfigure(self, **kwargs):
        self._stream.reconfigure(**kwargs)

BASE_URL  = "https://www.rundown.ai/articles?category=AI"
SEEN_FILE = "seen_articles.json"
MAX_PAGES = 4

PAGE_BTN     = '[fs-cmsload-element="page-button"]'
ARTICLE_LINK = "a[href^='/articles/']"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_seen() -> tuple[dict[str, dict], str | None, int]:
    """
    Returns (seen_dict, checkpoint_url, next_id).
    checkpoint_url is the URL of the FIRST entry in seen_articles.json —
    the most recently known article. The scraper stops when it hits this URL.
    next_id is the next available article ID (starts at 1000).
    """
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            return {}, None, 1000
        checkpoint = data[0]["url"]
        next_id = max((a.get("id", 999) for a in data), default=999) + 1
        return {a["url"]: a for a in data}, checkpoint, next_id
    except (FileNotFoundError, json.JSONDecodeError):
        return {}, None, 1000


def save_seen(seen: dict[str, dict]) -> None:
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen.values()), f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_title(raw: str) -> str:
    """
    Card text structure:  Category \\n\\n Title \\n\\n Author · N minutes
    Title is always the second non-empty line.
    """
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    return lines[1] if len(lines) >= 2 else (lines[0] if lines else "")


def fmt_date(raw) -> str | None:
    if not raw:
        return None
    s = str(raw)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:26], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------

def scrape_page(page) -> list[dict]:
    seen_urls: set[str] = set()
    articles = []

    for a in page.query_selector_all(ARTICLE_LINK):
        href = a.get_attribute("href") or ""
        if not re.match(r"^/articles/[a-z0-9\-]+$", href):
            continue

        url = f"https://www.rundown.ai{href}"
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = extract_title(a.inner_text() or "")
        if len(title) < 8:
            continue

        time_el = a.query_selector("time")
        date = fmt_date(
            time_el.get_attribute("datetime") or time_el.inner_text() if time_el else None
        )

        articles.append({"title": title, "url": url, "date": date})

    return articles


def go_to_page(page, num: int) -> bool:
    """Click the pagination button for page `num` and wait for content to swap."""
    try:
        btn = page.locator(PAGE_BTN).filter(has_text=re.compile(rf"^{num}$"))
        btn.wait_for(state="visible", timeout=5000)

        first_before = page.locator(ARTICLE_LINK).first.get_attribute("href")
        btn.click()

        # Wait up to 5 s for the article list to swap out
        for _ in range(10):
            page.wait_for_timeout(500)
            if page.locator(ARTICLE_LINK).first.get_attribute("href") != first_before:
                break

        return True
    except PlaywrightTimeout:
        print(f"  Page {num} button not found.", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    run_log = init_run_log()
    sys.stdout = _Tee(sys.stdout)
    sys.stderr = _Tee(sys.stderr)
    log("=" * 60)
    log(f"RUN STARTED — log: {run_log.name}")
    log("=" * 60)
    seen, checkpoint, next_id = load_seen()
    first_run  = checkpoint is None
    all_new: list[dict] = []
    new_urls:  set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        pw = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )).new_page()

        log(f"Scraping {BASE_URL}")
        print(f"Loading {BASE_URL} ...", file=sys.stderr)
        pw.goto(BASE_URL, wait_until="networkidle", timeout=30000)

        for page_num in range(1, MAX_PAGES + 1):
            if page_num > 1:
                print(f"  → Page {page_num} ...", file=sys.stderr)
                if not go_to_page(pw, page_num):
                    break

            articles = scrape_page(pw)
            print(f"  Page {page_num}: {len(articles)} articles.", file=sys.stderr)
            log(f"Page {page_num}: {len(articles)} articles found")

            done = False
            for art in articles:
                if art["url"] == checkpoint:
                    print(f"  Reached checkpoint at page {page_num}. Stopping.", file=sys.stderr)
                    log(f"Reached checkpoint at page {page_num} — stopping scrape")
                    done = True
                    break
                elif art["url"] not in new_urls:
                    all_new.append(art)
                    new_urls.add(art["url"])

            if done:
                break

        browser.close()

    # Assign IDs to new articles
    for art in all_new:
        art["id"] = next_id
        next_id += 1

    if not all_new:
        log("No new articles found — nothing to do")
        print("No new articles found.")
        return

    log(f"{len(all_new)} new article(s) found")
    print(json.dumps(all_new, indent=2, ensure_ascii=False))

    # ── Phase 1: send ALL notifications immediately (5s gap between each) ──
    saved_new: dict[str, dict] = {}
    pending: list[tuple[dict, int]] = []  # (article, telegram_message_id)

    for idx, art in enumerate(all_new):
        saved_new[art["url"]] = art
        merged = dict(saved_new)
        merged.update(seen)
        save_seen(merged)

        if idx > 0:
            print(f"  Waiting 5 seconds before next notification ...", file=sys.stderr)
            time.sleep(5)

        print(f"  Sending notification for: {art['title']}", file=sys.stderr)
        log(f"Telegram notification sent: {art['title']}")
        try:
            msg_id = send_approval_message(art["title"], art["url"])
            pending.append((art, msg_id))
        except Exception as e:
            log(f"Telegram notification failed for '{art['title']}': {type(e).__name__}: {e}", level="ERROR")
            print(f"  [TELEGRAM ERROR] Could not send notification for '{art['title']}': {type(e).__name__}: {e}", file=sys.stderr)

    if not pending:
        log("No notifications could be sent — aborting", level="ERROR")
        print("No notifications could be sent.", file=sys.stderr)
        return

    log(f"All {len(pending)} notification(s) sent — waiting for responses")
    print(f"\nAll {len(pending)} notification(s) sent. Waiting for your responses ...\n", file=sys.stderr)

    # ── Phase 2: collect responses and generate content for approved articles ──
    for art, msg_id in pending:
        print(f"  Waiting for response on: {art['title']}", file=sys.stderr)
        log(f"Waiting for user response: {art['title']}")
        try:
            approved = wait_for_approval(msg_id)
        except Exception as e:
            log(f"wait_for_approval failed for '{art['title']}': {type(e).__name__}: {e}", level="ERROR")
            print(f"  [TELEGRAM ERROR] wait_for_approval failed: {type(e).__name__}: {e}", file=sys.stderr)
            continue

        if approved:
            log(f"User approved: {art['title']}")
            print(f"User approved — generating content: {art['title']}")
            try:
                research = research_article(art["url"])
            except Exception as e:
                log(f"research_article failed for '{art['title']}': {type(e).__name__}: {e}", level="ERROR")
                print(f"  [PIPELINE ERROR] research_article failed: {type(e).__name__}: {e}", file=sys.stderr)
                continue

            try:
                reel = generate_reel_script(research)
            except Exception as e:
                log(f"generate_reel_script failed for '{art['title']}': {type(e).__name__}: {e}", level="ERROR")
                print(f"  [PIPELINE ERROR] generate_reel_script failed: {type(e).__name__}: {e}", file=sys.stderr)
                continue

            # Build the exact voiceover script that goes to ElevenLabs
            voiceover_text = " ".join(
                seg["voiceover"] for seg in reel.get("segments", []) if seg.get("voiceover")
            )

            audio_path = None
            if voiceover_text:
                # 1. Send the script text
                try:
                    script_msg = f"🎙 <b>SCRIPT</b>\n\n{voiceover_text}"
                    send_message(script_msg)
                    log("Script sent to Telegram")
                except Exception as e:
                    log(f"send script failed: {type(e).__name__}: {e}", level="ERROR")
                    print(f"  [TELEGRAM ERROR] send script failed: {type(e).__name__}: {e}", file=sys.stderr)

                # 2. Send the audio
                try:
                    audio_path = generate_audio(voiceover_text)
                    send_audio(audio_path, title=reel.get("title", ""))
                except Exception as e:
                    log(f"Audio generation or send failed: {type(e).__name__}: {e}", level="ERROR")
                    print(f"  [AUDIO/TELEGRAM ERROR] audio send failed: {type(e).__name__}: {e}", file=sys.stderr)

            # 3. Generate visuals for each style
            all_style_visuals = {}  # style -> visuals list (for video generation)
            for style_key, style_name in [("algorithmic", "Algorithmic")]:
                # 3a. Generate visual prompts for this style
                style_visuals = None
                try:
                    log(f"Generating visual prompts — style: {style_name}")
                    print(f"  Generating visual prompts ({style_name}) ...", flush=True)
                    style_visuals = generate_visual_prompts(reel, style_key)
                    log(f"Visual prompts ready — {style_name}: {len(style_visuals)} frames")
                except Exception as e:
                    log(f"generate_visual_prompts failed ({style_name}): {type(e).__name__}: {e}", level="ERROR")
                    print(f"  [VISUAL ERROR] {style_name}: {type(e).__name__}: {e}", file=sys.stderr)
                    continue

                # 3b. Generate images from fal.ai
                try:
                    log(f"Generating images from fal.ai — style: {style_name}")
                    style_visuals = generate_images_for_visuals(style_visuals, art.get("title", "article"), style_slug=style_key)
                    log(f"--- Image collection summary ({style_name}) ---")
                    for v in style_visuals:
                        label = v.get("label", "?")
                        path = v.get("image_path")
                        size_kb = (os.path.getsize(path) // 1024) if path and os.path.exists(path) else None
                        status = f"OK — {size_kb} KB at {path}" if size_kb else "FAILED — no local file"
                        log(f"  [{label}] {status}")
                    log(f"--- End image collection summary ({style_name}) ---")
                except Exception as e:
                    log(f"generate_images_for_visuals failed ({style_name}): {type(e).__name__}: {e}", level="ERROR")
                    print(f"  [IMAGE GEN ERROR] {style_name}: {type(e).__name__}: {e}", file=sys.stderr)
                    continue

                # 3c. Send images to Telegram with style label
                try:
                    log(f"Sending images to Telegram — style: {style_name}")
                    send_message(f"🎨 <b>{style_name}</b>")
                    send_generated_images(style_visuals, title=reel.get("title", ""))
                except Exception as e:
                    log(f"send_generated_images failed ({style_name}): {type(e).__name__}: {e}", level="ERROR")
                    print(f"  [TELEGRAM IMAGE ERROR] {style_name}: {type(e).__name__}: {e}", file=sys.stderr)

                all_style_visuals[style_key] = style_visuals

            # Use the first successfully generated style for the video
            visuals = next(iter(all_style_visuals.values()), None)

            # 4. Generate SRT + video (after all images are stored)
            if visuals and audio_path:
                title_slug = re.sub(r"[^a-z0-9]+", "_", art.get("title", "article").lower())[:40].strip("_")
                srt_path = None
                try:
                    log("Generating SRT file")
                    srt_path = generate_srt(reel, title_slug, audio_path)
                    log(f"Sending SRT to Telegram: {srt_path}")
                    send_document(srt_path, filename=f"{title_slug}.srt")
                    log("SRT sent to Telegram")
                except Exception as e:
                    log(f"SRT generation or send failed: {type(e).__name__}: {e}", level="ERROR")
                    print(f"  [SRT ERROR] {type(e).__name__}: {e}", file=sys.stderr)

                if srt_path:
                    try:
                        log("Generating video with ffmpeg")
                        video_path = generate_video(visuals, audio_path, srt_path, title_slug)
                        if video_path:
                            log(f"Video saved: {video_path}")
                        else:
                            log("Video generation returned None", level="WARNING")
                    except Exception as e:
                        log(f"Video generation failed: {type(e).__name__}: {e}", level="ERROR")
                        print(f"  [VIDEO ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        else:
            log(f"User skipped: {art['title']}")
            print(f"User skipped: {art['title']}")

    log("=" * 60)
    log("RUN COMPLETE")
    log("=" * 60)


if __name__ == "__main__":
    main()
