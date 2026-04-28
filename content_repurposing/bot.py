"""
Interactive Telegram bot — main entry point.

Run:  python bot.py

Features:
  • /start        — welcome message
  • /news          — scrape latest articles and present them with inline buttons
  • Any text msg   — ChatGPT reply
  • Inline buttons — create content, skip article, publish/skip TikTok
"""

import asyncio
import hashlib
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from buffer_poster import post_video_to_tiktok
from gdrive_uploader import upload_video
from image_gen import generate_images_from_json
from logger import log
from pipeline import generate_script, generate_visuals
from scraper import (
    BASE_URL,
    MAX_PAGES,
    fetch_article_body,
    go_to_page,
    load_seen,
    save_seen,
    scrape_page,
)
from voice import generate_audio, generate_subtitles
from video import generate_video

load_dotenv()

TOKEN          = os.getenv("TELEGRAM_TOKEN")
CHAT_ID        = os.getenv("CHAT_ID")
CHAT_ID2       = os.getenv("CHAT_ID2")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CHAT_IDS = [cid for cid in [CHAT_ID, CHAT_ID2] if cid]

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ── In-memory state ──────────────────────────────────────────────────────────
# Articles waiting for user decision  {hash -> article dict}
_pending_articles: dict[str, dict] = {}

# Videos ready to be published  {slug -> {drive_url, title}}
_ready_videos: dict[str, dict] = {}


# ── Utility: send to all chats ───────────────────────────────────────────────

async def _broadcast(bot: Bot, text: str, **kwargs) -> None:
    for cid in CHAT_IDS:
        await bot.send_message(chat_id=cid, text=text, **kwargs)


async def _send_images(bot: Bot, scenes: list[dict]) -> None:
    for i, s in enumerate(scenes, 1):
        path = s.get("image_path")
        if not path or not os.path.exists(path):
            continue
        try:
            for cid in CHAT_IDS:
                with open(path, "rb") as f:
                    await bot.send_photo(chat_id=cid, photo=f)
        except Exception as e:
            log(f"[bot] Failed to send image {i}: {e}", "ERROR")


async def _send_audio_file(bot: Bot, audio_path: str, title: str) -> None:
    try:
        for cid in CHAT_IDS:
            with open(audio_path, "rb") as f:
                await bot.send_audio(chat_id=cid, audio=f, title=title or "Voiceover")
    except Exception as e:
        log(f"[bot] Failed to send audio: {e}", "ERROR")


# ── /start ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Hey! I'm your content bot.\n\n"
        "Commands:\n"
        "• /news — Scrape the latest articles\n"
        "• /start — Show this message\n\n"
        "Or just send me any message and I'll reply via ChatGPT. 🤖"
    )


# ── /news ────────────────────────────────────────────────────────────────────

async def cmd_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔍 Scraping latest articles, hang on...")
    try:
        articles = await asyncio.to_thread(_scrape_new_articles)
    except Exception as e:
        await update.message.reply_text(f"❌ Scraping error: {e}")
        log(f"[bot] Scraping error: {e}", "ERROR")
        return

    if not articles:
        seen, _, _ = load_seen()
        last5 = list(seen.values())[:5]
        if not last5:
            await update.message.reply_text("✅ No new articles and no history found.")
            return
        await update.message.reply_text(
            "✅ No new articles. Here are the last 5 — want to create content for any?",
        )
        for art in last5:
            h = hashlib.md5(art["url"].encode()).hexdigest()[:8]
            _pending_articles[h] = art
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Create Content", callback_data=f"create_{h}"),
                InlineKeyboardButton("❌ Skip",           callback_data=f"skip_{h}"),
            ]])
            await update.message.reply_text(
                f"📌 <b>{art['title']}</b>\n"
                f"<a href=\"{art['url']}\">🔗 Read article</a>",
                reply_markup=keyboard,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        return

    await update.message.reply_text(
        f"📰 Found <b>{len(articles)}</b> new article(s):",
        parse_mode="HTML",
    )

    for art in articles:
        h = hashlib.md5(art["url"].encode()).hexdigest()[:8]
        _pending_articles[h] = art
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Create Content", callback_data=f"create_{h}"),
            InlineKeyboardButton("❌ Skip",           callback_data=f"skip_{h}"),
        ]])
        await update.message.reply_text(
            f"📌 <b>{art['title']}</b>\n"
            f"<a href=\"{art['url']}\">🔗 Read article</a>",
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )


# ── Callback handler ─────────────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    # ── Article: create content
    if data.startswith("create_"):
        h = data[7:]
        art = _pending_articles.get(h)
        if not art:
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("❌ Article is no longer available.")
            return
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎬 Creating content for:\n<b>{art['title']}</b>",
            parse_mode="HTML",
        )
        asyncio.create_task(_run_pipeline(context.bot, chat_id, art))

    # ── Article: skip
    elif data.startswith("skip_"):
        h = data[5:]
        art = _pending_articles.pop(h, None)
        title = art["title"] if art else "article"
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(f"⏭ Skipped: {title}")

    # ── TikTok: publish
    elif data.startswith("publish_"):
        slug = data[8:]
        info = _ready_videos.get(slug)
        if not info:
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("❌ Video is no longer available.")
            return
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("📤 Posting to TikTok...")
        try:
            post = await asyncio.to_thread(post_video_to_tiktok, info["drive_url"], info["title"])
            _ready_videos.pop(slug, None)
            await query.message.reply_text(
                f"✅ <b>Posted to TikTok!</b>\n"
                f"ID: <code>{post.get('id')}</code>\n"
                f"Scheduled: {post.get('dueAt', 'automatic')}",
                parse_mode="HTML",
            )
        except Exception as e:
            await query.message.reply_text(f"❌ TikTok posting error: {e}")
            log(f"[bot] TikTok post error: {e}", "ERROR")

    # ── TikTok: skip publish
    elif data.startswith("nopublish_"):
        slug = data[10:]
        _ready_videos.pop(slug, None)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("⏭ Skipped TikTok posting.")


# ── General message → ChatGPT ─────────────────────────────────────────────────

NEWS_TRIGGERS = ["lajme", "latest news", "show news", "news", "lajmet", "get news"]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    low  = text.lower()

    if any(t in low for t in NEWS_TRIGGERS):
        await cmd_news(update, context)
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        response = await asyncio.to_thread(
            lambda: openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a smart assistant specialized in content marketing, "
                            "social media, and TikTok. Reply concisely and clearly in English."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
            )
        )
        reply = response.choices[0].message.content or "..."
    except Exception as e:
        reply = f"❌ ChatGPT error: {e}"
        log(f"[bot] ChatGPT error: {e}", "ERROR")

    await update.message.reply_text(reply)


# ── Full content pipeline ─────────────────────────────────────────────────────

async def _run_pipeline(bot: Bot, chat_id: int, art: dict) -> None:
    """Runs the full content pipeline for one article, notifying Telegram at each step."""
    slug = re.sub(r"[^a-z0-9]+", "_", art.get("title", "article").lower())[:40].strip("_")

    async def notify(text: str) -> None:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

    log(f"[bot] Pipeline started for: {art['title']}")

    try:
        # 1. Fetch article body
        await notify("📥 Fetching article text...")
        body = await asyncio.to_thread(fetch_article_body, art["url"])
        if not body:
            await notify("⚠️ Article body was empty — XPath may have changed.")
            return

        # 2. Generate script
        await notify("✍️ Generating script with ChatGPT...")
        script = await asyncio.to_thread(generate_script, body)
        script_path = f"generated_content/{slug}/scripts/{slug}.txt"
        Path(script_path).parent.mkdir(parents=True, exist_ok=True)
        Path(script_path).write_text(script, encoding="utf-8")
        await notify(f"📝 <b>Script:</b>\n\n{script}")

        # 3. Generate visual prompts JSON
        await notify("🎨 Generating visual prompts...")
        visuals_path = await asyncio.to_thread(generate_visuals, script, slug)

        # 4. Generate images via fal.ai
        await notify("🖼 Generating images with AI... (this may take a few minutes)")
        scenes = await asyncio.to_thread(generate_images_from_json, visuals_path, slug)
        succeeded = sum(1 for s in scenes if s.get("image_path"))
        await notify(f"✅ Images: {succeeded}/{len(scenes)} generated")
        await _send_images(bot, scenes)

        # 5. Generate audio
        await notify("🔊 Generating voiceover (TTS)...")
        audio_path = await asyncio.to_thread(
            generate_audio, script,
            f"generated_content/{slug}/audio/{slug}.mp3"
        )
        await _send_audio_file(bot, audio_path, art["title"])

        # 6. Generate subtitles
        await notify("💬 Generating subtitles (Gladia)...")
        srt_path = await asyncio.to_thread(
            generate_subtitles,
            audio_path,
            f"generated_content/{slug}/subtitles/{slug}.srt",
            script,
        )

        # 7. Stitch video
        await notify("🎬 Assembling video with ffmpeg...")
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
        result = await asyncio.to_thread(
            generate_video, visuals_for_video, audio_path, srt_path, slug, video_path
        )
        if not result:
            await notify("❌ Video generation failed.")
            return

        # 8. Upload to Google Drive
        await notify("☁️ Uploading video to Google Drive...")
        drive_url = await asyncio.to_thread(upload_video, result)
        log(f"[bot] Drive URL: {drive_url}")

        # Store for publish callback
        _ready_videos[slug] = {"drive_url": drive_url, "title": art["title"]}

        # 9. Send TikTok approval prompt
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Post to TikTok!", callback_data=f"publish_{slug}"),
            InlineKeyboardButton("❌ Skip",            callback_data=f"nopublish_{slug}"),
        ]])
        for cid in CHAT_IDS:
            await bot.send_message(
                chat_id=cid,
                text=(
                    f"🎬 <b>VIDEO READY!</b>\n\n"
                    f"<b>{art['title']}</b>\n\n"
                    f"📁 <a href=\"{drive_url}\">View on Google Drive</a>\n\n"
                    f"Post this to TikTok?"
                ),
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    except Exception as e:
        log(f"[bot] Pipeline error for '{art['title']}': {type(e).__name__}: {e}", "ERROR")
        await notify(f"❌ <b>Pipeline error:</b>\n{type(e).__name__}: {e}")


# ── Scraper (blocking, safe to call from asyncio.to_thread) ──────────────────

def _scrape_new_articles() -> list[dict]:
    """Scrape Telegrafi and return new unseen articles (no Telegram calls)."""
    from playwright.sync_api import sync_playwright

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

        pw.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        pw.wait_for_timeout(3000)

        for page_num in range(1, MAX_PAGES + 1):
            if page_num > 1:
                if not go_to_page(pw, page_num):
                    break
            articles = scrape_page(pw)
            done = False
            for art in articles:
                if art["url"] == checkpoint:
                    done = True
                    break
                if art["url"] not in new_urls:
                    all_new.append(art)
                    new_urls.add(art["url"])
            if done:
                break

        browser.close()

    for art in all_new:
        art["id"] = next_id
        next_id += 1

    if all_new:
        merged = {a["url"]: a for a in all_new}
        merged.update(seen)
        save_seen(merged)

    return all_new


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN is not set in .env")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("news",  cmd_news))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log("[bot] Starting bot — polling for updates...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
