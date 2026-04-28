import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from telegram_bot import send_approval_message, wait_for_next, send_tiktok_approval
from pipeline import generate_script, generate_visuals
from image_gen import generate_images_from_json
from voice import generate_audio, generate_subtitles
from video import generate_video
from gdrive_uploader import upload_video
from buffer_poster import post_video_to_tiktok

BASE_URL         = "https://telegrafi.com/shendetesi/ushqimi-dhe-dieta/"
SEEN_FILE        = "seen_articles.json"
MAX_PAGES        = 2
ARTICLES_XPATH   = '//*[@id="sSection_Subsection_Layout_0_0_33_0_0_4_0_4_0_0_1"]/div'
PAGINATION_XPATH = '//*[@id="sSection_Subsection_Layout_0_0_33_0_0_4_0_4_0_0_1"]/div/div[2]/nav/a'


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_seen() -> tuple[dict[str, dict], str | None, int]:
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
    """
    Scrape article cards from a telegrafi.com listing page.
    Skips any card whose text contains 'Reklama' (ads).
    Returns list of {title, url, date}.
    """
    seen_urls: set[str] = set()
    articles = []

    # Scope to the articles container only
    container = page.query_selector(f"xpath={ARTICLES_XPATH}")
    if not container:
        print("  WARNING: articles container not found on page.", file=sys.stderr)
        return articles

    for a in container.query_selector_all("a[href]"):
        href = (a.get_attribute("href") or "").strip()

        if href.startswith("https://telegrafi.com/"):
            url = href.rstrip("/") + "/"
        elif href.startswith("/"):
            url = "https://telegrafi.com" + href.rstrip("/") + "/"
        else:
            continue

        # Article URLs have exactly 1 path segment: /article-slug/
        # Author pages (/author/x/), category pages (/cat/sub/), etc. have 2+
        path = url.replace("https://telegrafi.com/", "").strip("/")
        segments = [s for s in path.split("/") if s]
        if len(segments) != 1:
            continue

        if url in seen_urls:
            continue

        # Find the nearest <article> ancestor — this is the full card
        card = a.evaluate_handle("el => el.closest('article')") or a

        card_text = card.inner_text() or ""

        # Skip ads
        if "Reklama" in card_text or "reklama" in card_text:
            print(f"  [SKIP ads] {url}", file=sys.stderr)
            continue

        # Extract title from heading tags, fallback to link text
        title = ""
        for heading_sel in ("h1", "h2", "h3", "h4"):
            el = a.query_selector(heading_sel) or card.query_selector(heading_sel)
            if el:
                title = el.inner_text().strip()
                break
        if not title:
            title = a.inner_text().strip().splitlines()[0].strip()

        if len(title) < 8:
            print(f"  [SKIP short title] {url!r} -> {title!r}", file=sys.stderr)
            continue

        # Date is in a <span> inside the article card metadata area
        # Try the known structure first: div > div > div:nth-child(2) > div:nth-child(2) > span
        # then fall back to any <time> or first <span> that looks like a date
        date = None
        date_el = card.query_selector("div > div > div:nth-child(2) > div:nth-child(2) > span")
        if not date_el:
            date_el = card.query_selector("time")
        if not date_el:
            # fallback: grab all spans and pick the one that looks like a date
            for span in card.query_selector_all("span"):
                text = span.inner_text().strip()
                if text and any(c.isdigit() for c in text):
                    date_el = span
                    break
        if date_el:
            raw = date_el.get_attribute("datetime") or date_el.inner_text().strip()
            date = fmt_date(raw) or raw  # keep raw string if fmt_date can't parse it

        seen_urls.add(url)
        articles.append({"title": title, "url": url, "date": date})

    return articles


def go_to_page(page, num: int) -> bool:
    """Click the pagination link matching page `num`."""
    try:
        nav_links = page.locator(f"xpath={PAGINATION_XPATH}")
        count = nav_links.count()
        if count == 0:
            print(f"  No pagination links found for page {num}.", file=sys.stderr)
            return False

        target = None
        for i in range(count):
            link = nav_links.nth(i)
            text = (link.inner_text() or "").strip()
            if text == str(num):
                target = link
                break

        if target is None:
            target = nav_links.last

        target.wait_for(state="visible", timeout=5000)
        target.scroll_into_view_if_needed()
        target.click()
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)  # let JS render new page articles
        return True
    except PlaywrightTimeout:
        print(f"  Pagination click timed out for page {num}.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  go_to_page error (page {num}): {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Article body fetching
# ---------------------------------------------------------------------------

ARTICLE_BODY_XPATH = '/html/body/div[4]/div/div[10]/div[1]/div[1]/div[2]/div/div[1]/div/div[1]/div[1]/div'

def fetch_article_body(url: str) -> str:
    """Load the article page and return the full body text using the known XPath."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )).new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        el = page.query_selector(f"xpath={ARTICLE_BODY_XPATH}")
        text = el.inner_text().strip() if el else ""
        browser.close()
    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    seen, checkpoint, next_id = load_seen()
    all_new: list[dict] = []
    new_urls: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        pw = browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )).new_page()

        print(f"Loading {BASE_URL} ...")
        pw.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        pw.wait_for_timeout(3000)  # let JS render the article cards

        for page_num in range(1, MAX_PAGES + 1):
            if page_num > 1:
                print(f"  → Navigating to page {page_num} ...")
                if not go_to_page(pw, page_num):
                    break

            articles = scrape_page(pw)
            print(f"  Page {page_num}: {len(articles)} articles found.")

            done = False
            for art in articles:
                if art["url"] == checkpoint:
                    print(f"  Reached checkpoint at page {page_num}. Stopping.")
                    done = True
                    break
                elif art["url"] not in new_urls:
                    all_new.append(art)
                    new_urls.add(art["url"])

            if done:
                break

        browser.close()

    # Assign IDs
    for art in all_new:
        art["id"] = next_id
        next_id += 1

    if not all_new:
        print("No new articles found.")
        return

    # Save to seen_articles.json
    merged = {a["url"]: a for a in all_new}
    merged.update(seen)
    save_seen(merged)

    print(f"\n{len(all_new)} new article(s) found. Sending to Telegram...\n")

    # Phase 1 — send all notifications (5s gap between each)
    pending: list[tuple[dict, int]] = []
    for idx, art in enumerate(all_new):
        if idx > 0:
            time.sleep(5)
        try:
            msg_id = send_approval_message(art["title"], art["url"])
            pending.append((art, msg_id))
            print(f"  Sent: {art['title']}")
        except Exception as e:
            print(f"  [ERROR] Could not send notification for '{art['title']}': {e}", file=sys.stderr)

    if not pending:
        print("No notifications could be sent.")
        return

    print(f"\nAll {len(pending)} notification(s) sent. Waiting for responses...\n")

    # Phase 2 — wait for user responses and act on them
    article_by_msg_id = {msg_id: art for art, msg_id in pending}
    remaining_ids = set(article_by_msg_id.keys())

    while remaining_ids:
        try:
            msg_id, approved = wait_for_next(remaining_ids)
        except Exception as e:
            print(f"  [ERROR] wait_for_next failed: {e}", file=sys.stderr)
            break
        remaining_ids.discard(msg_id)
        art = article_by_msg_id[msg_id]

        if approved:
            print(f"\nCreating content for: {art['title']}")

            # 1. Fetch article body
            try:
                body = fetch_article_body(art["url"])
                if not body:
                    print("  [WARNING] Article body was empty — XPath may not have matched.")
                    continue
                print(f"  Article body fetched ({len(body)} chars)")
            except Exception as e:
                print(f"  [ERROR] Could not fetch article body: {e}", file=sys.stderr)
                continue

            slug = re.sub(r"[^a-z0-9]+", "_", art.get("title", "article").lower())[:40].strip("_")

            # 2. Generate script via ChatGPT
            try:
                script = generate_script(body)
                print(f"\n{'='*60}")
                print(f"SCRIPT: {art['title']}")
                print(f"{'='*60}")
                print(script)
                print(f"{'='*60}\n")
                script_path = f"generated_content/{slug}/scripts/{slug}.txt"
                Path(script_path).parent.mkdir(parents=True, exist_ok=True)
                Path(script_path).write_text(script, encoding="utf-8")
                print(f"  Script saved: {script_path}")
            except Exception as e:
                print(f"  [ERROR] generate_script failed: {e}", file=sys.stderr)
                continue

            # 3. Generate visual prompts JSON
            try:
                visuals_path = generate_visuals(script, slug)
                print(f"  Visuals saved: {visuals_path}")
            except Exception as e:
                print(f"  [ERROR] generate_visuals failed: {e}", file=sys.stderr)
                visuals_path = None

            # 3b. Generate images from visuals JSON via fal.ai
            scenes = []
            if visuals_path:
                try:
                    scenes = generate_images_from_json(visuals_path, style_slug=slug)
                    succeeded = sum(1 for s in scenes if s.get("image_path"))
                    print(f"  Images generated: {succeeded}/{len(scenes)}")
                except Exception as e:
                    print(f"  [ERROR] generate_images_from_json failed: {e}", file=sys.stderr)

            # 4. Generate audio via OpenAI TTS (echo voice, 1.2x speed)
            try:
                audio_path = generate_audio(script, output_path=f"generated_content/{slug}/audio/{slug}.mp3")
                print(f"  Audio saved: {audio_path}")
            except Exception as e:
                print(f"  [ERROR] generate_audio failed: {e}", file=sys.stderr)
                continue

            # 5. Generate subtitles via Gladia + GPT correction
            try:
                srt_path = generate_subtitles(audio_path, output_path=f"generated_content/{slug}/subtitles/{slug}.srt", script_text=script)
                print(f"  Subtitles saved: {srt_path}")
            except Exception as e:
                print(f"  [ERROR] generate_subtitles failed: {e}", file=sys.stderr)
                srt_path = None

            # 6. Stitch animated video
            if visuals_path and srt_path and scenes:
                try:
                    visuals_for_video = [
                        {
                            "image_path": s.get("image_path"),
                            "voiceover":  s.get("script", ""),
                            "label":      str(s.get("id", i)),
                        }
                        for i, s in enumerate(scenes)
                    ]
                    video_path = f"generated_content/{slug}/video.mp4"
                    Path(video_path).parent.mkdir(parents=True, exist_ok=True)
                    result = generate_video(visuals_for_video, audio_path, srt_path, slug, output_path=video_path)
                    if result:
                        print(f"  Video saved: {result}")
                        # Upload to Google Drive and ask user whether to post on TikTok
                        try:
                            print("  Uploading to Google Drive ...")
                            drive_url = upload_video(result)
                            print(f"  Drive URL: {drive_url}")
                            msg_id = send_tiktok_approval(drive_url, art["title"])
                            _, approved = wait_for_next({msg_id})
                            if approved:
                                print("  Posting to TikTok via Buffer ...")
                                post = post_video_to_tiktok(drive_url, art["title"])
                                print(f"  TikTok post queued — id: {post.get('id')}, dueAt: {post.get('dueAt')}")
                            else:
                                print("  Skipped TikTok post.")
                        except Exception as e:
                            print(f"  [ERROR] TikTok flow failed: {e}", file=sys.stderr)
                    else:
                        print("  [ERROR] generate_video returned None", file=sys.stderr)
                except Exception as e:
                    print(f"  [ERROR] generate_video failed: {e}", file=sys.stderr)
        else:
            print(f"Skipped: {art['title']}")


if __name__ == "__main__":
    main()
