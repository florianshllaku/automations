import asyncio
import os
import tempfile
import urllib.request

import requests
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from logger import log

load_dotenv()

TOKEN     = os.getenv("TELEGRAM_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
CHAT_ID2  = os.getenv("CHAT_ID2")

# All chat IDs that receive informational messages (audio, images, documents, plain text)
CHAT_IDS = [cid for cid in [CHAT_ID, CHAT_ID2] if cid]

# Persistent polling state — shared across all wait_for_approval calls so that
# callbacks tapped out-of-order are never lost.
_telegram_offset: int | None = None
_buffered_responses: dict[int, bool] = {}  # message_id -> approved


async def _send_message(text: str) -> None:
    async with Bot(TOKEN) as bot:
        for cid in CHAT_IDS:
            await bot.send_message(chat_id=cid, text=text, parse_mode="HTML")


def send_message(text: str) -> None:
    """Send a message (HTML parse mode) to the configured chat."""
    log(f"[DEBUG] send_message — chars: {len(text)}, preview: {text[:80].strip()}", "DEBUG")
    asyncio.run(_send_message(text))
    log("[DEBUG] send_message — delivered", "DEBUG")


async def _send_approval_message(title: str, url: str) -> int:
    """Send the YES/NO notification and return the message_id. Does NOT wait for a reply."""
    text = (
        f"🆕 <b>NEW ARTICLE DETECTED</b>\n\n"
        f"{title}\n"
        f"{url}\n\n"
        f"Want to create content for this?"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Create Content", callback_data="yes"),
        InlineKeyboardButton("❌ No",             callback_data="no"),
    ]])
    async with Bot(TOKEN) as bot:
        msg = await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    return msg.message_id


def send_approval_message(title: str, url: str) -> int:
    """Send the approval notification. Returns the message_id for later response collection."""
    log(f"[DEBUG] send_approval_message — title: {title}, url: {url}", "DEBUG")
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN env var is not set")
    if not CHAT_ID:
        raise ValueError("CHAT_ID env var is not set")
    msg_id = asyncio.run(_send_approval_message(title, url))
    log(f"[DEBUG] Approval message sent — message_id: {msg_id}", "DEBUG")
    return msg_id


async def _flush_offset() -> None:
    """Flush stale Telegram updates so we only see new button presses."""
    global _telegram_offset
    if _telegram_offset is not None:
        return
    async with Bot(TOKEN) as bot:
        updates = await bot.get_updates(timeout=0)
        if updates:
            _telegram_offset = updates[-1].update_id + 1
        else:
            await bot.get_updates(offset=-1, timeout=0)
            fresh = await bot.get_updates(timeout=0)
            _telegram_offset = (fresh[-1].update_id + 1) if fresh else 1
        log(f"[DEBUG] Initial flush — starting offset: {_telegram_offset}", "DEBUG")


async def _wait_for_next(message_ids: set[int]) -> tuple[int, bool]:
    """
    Poll until ONE of the given message_ids gets a YES/NO tap.
    Returns (message_id, approved). Any other taps are buffered.
    """
    global _telegram_offset, _buffered_responses

    # Check buffer first
    for mid in list(message_ids):
        if mid in _buffered_responses:
            result = _buffered_responses.pop(mid)
            log(f"[DEBUG] Used buffered response for message_id={mid} — {result}", "DEBUG")
            return mid, result

    await _flush_offset()

    async with Bot(TOKEN) as bot:
        poll_count = 0
        while True:
            updates = await bot.get_updates(offset=_telegram_offset, timeout=10)
            poll_count += 1
            if updates:
                log(f"[DEBUG] Poll #{poll_count} — {len(updates)} update(s)", "DEBUG")
            for update in updates:
                _telegram_offset = update.update_id + 1
                cq = update.callback_query
                if not (cq and cq.message):
                    continue
                mid = cq.message.message_id
                approved = cq.data == "yes"
                label = "✅ YES — creating content!" if approved else "❌ NO — skipped."
                log(f"User tapped {'YES' if approved else 'NO'} on message_id={mid}")
                await bot.answer_callback_query(cq.id)
                await bot.edit_message_reply_markup(chat_id=CHAT_ID, message_id=mid, reply_markup=None)
                await bot.send_message(chat_id=CHAT_ID, text=label)
                if mid in message_ids:
                    return mid, approved
                else:
                    _buffered_responses[mid] = approved
                    log(f"[DEBUG] Buffered tap for message_id={mid}", "DEBUG")


def wait_for_next(message_ids: set[int]) -> tuple[int, bool]:
    """
    Wait for the next YES/NO tap on any of the given message_ids.
    Returns (message_id, approved) as soon as one comes in.
    """
    return asyncio.run(_wait_for_next(message_ids))


async def _send_audio(audio_path: str, title: str) -> None:
    async with Bot(TOKEN) as bot:
        for cid in CHAT_IDS:
            with open(audio_path, "rb") as f:
                await bot.send_audio(
                    chat_id=cid,
                    audio=f,
                    title=title or "Reel Voiceover",
                    performer="Content Pipeline",
                )


def send_audio(audio_path: str, title: str = "") -> None:
    """Send the generated audio file to the Telegram chat."""
    size_kb = os.path.getsize(audio_path) // 1024 if os.path.exists(audio_path) else -1
    log(f"Sending audio to Telegram — file: {audio_path}, size: {size_kb} KB, title: {title}")
    log(f"[DEBUG] audio file exists: {os.path.exists(audio_path)}", "DEBUG")
    asyncio.run(_send_audio(audio_path, title))
    log(f"Audio sent to Telegram — {audio_path}")


def send_generated_images(visuals: list[dict], title: str = "") -> None:
    """
    Send all successfully generated fal.ai images to Telegram.
    Downloads each image locally first and uploads as a file — fal.ai URLs are
    not publicly fetchable by Telegram's servers (causes 400 Bad Request).
    """
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    count = sum(1 for v in visuals if v.get("image_url"))
    log(f"Sending {count}/{len(visuals)} generated image(s) to Telegram via file upload")
    log(f"[DEBUG] sendPhoto endpoint: {api_url}", "DEBUG")

    for i, v in enumerate(visuals, 1):
        image_url = v.get("image_url")
        image_path = v.get("image_path")
        label = v.get("label", f"Frame {i}")
        log(f"[DEBUG] Image {i}/{len(visuals)} — label: {label}, url: {image_url}, local_path: {image_path}", "DEBUG")

        if not image_url:
            log(f"[DEBUG] Skipping {label} — no image_url", "DEBUG")
            continue

        local_exists = image_path and os.path.exists(image_path)
        log(f"[DEBUG] Local file exists: {local_exists} — path: {image_path}", "DEBUG")

        tmp_path = None
        try:
            if local_exists:
                send_path = image_path
                size_kb = os.path.getsize(send_path) // 1024
                log(f"[DEBUG] Using local file: {send_path} ({size_kb} KB)", "DEBUG")
            else:
                log(f"[DEBUG] Local file missing — downloading from URL for {label}", "DEBUG")
                req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = resp.read()
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                send_path = tmp_path
                log(f"[DEBUG] Downloaded to temp file: {tmp_path} ({len(data)//1024} KB)", "DEBUG")

            log(f"[DEBUG] POSTing {label} to Telegram sendPhoto ...", "DEBUG")
            for cid in CHAT_IDS:
                with open(send_path, "rb") as f:
                    resp = requests.post(
                        api_url,
                        data={"chat_id": cid},
                        files={"photo": (f"{label}.jpg", f, "image/jpeg")},
                        timeout=60,
                    )
                log(f"[DEBUG] Telegram response status: {resp.status_code} for {label} (chat {cid})", "DEBUG")
                resp.raise_for_status()
            log(f"Image sent to Telegram — {label} (frame {i})")
        except Exception as e:
            log(f"Telegram image send failed for {label}: {type(e).__name__}: {e}", "ERROR")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                log(f"[DEBUG] Deleting temp file: {tmp_path}", "DEBUG")
                os.unlink(tmp_path)

    log("All generated images dispatched to Telegram")


async def _send_document(file_path: str, filename: str) -> None:
    async with Bot(TOKEN) as bot:
        for cid in CHAT_IDS:
            with open(file_path, "rb") as f:
                await bot.send_document(chat_id=cid, document=f, filename=filename)


def send_document(file_path: str, filename: str) -> None:
    """Send a file as a document to the Telegram chat."""
    size_kb = os.path.getsize(file_path) // 1024 if os.path.exists(file_path) else -1
    log(f"Sending document to Telegram: {filename} ({size_kb} KB)")
    log(f"[DEBUG] Document path: {file_path}, exists: {os.path.exists(file_path)}", "DEBUG")
    asyncio.run(_send_document(file_path, filename))
    log(f"Document sent: {filename}")


