import io
import os
import re
import time
import urllib.request
from pathlib import Path

import fal_client
from PIL import Image
from dotenv import load_dotenv
from logger import log

load_dotenv()

os.environ.setdefault("FAL_KEY", os.getenv("FAL_KEY", ""))

GENERATED_DIR = Path("generated_images")
GENERATED_DIR.mkdir(exist_ok=True)

MODEL = "fal-ai/nano-banana-pro"


def _slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:40].strip("_")


def _submit_image(image_prompt: str, filename_stem: str):
    """Submit a job to fal.ai and return the handler immediately (non-blocking)."""
    log(f"[DEBUG] fal.ai submit — stem: {filename_stem}, model: {MODEL}, prompt chars: {len(image_prompt)}", "DEBUG")
    log(f"[DEBUG] Prompt preview: {image_prompt[:120]}{'...' if len(image_prompt) > 120 else ''}", "DEBUG")
    log(f"[DEBUG] Params — aspect_ratio: 9:16, output_format: png, resolution: 4K, num_images: 1", "DEBUG")

    handler = fal_client.submit(
        MODEL,
        arguments={
            "prompt": image_prompt,
            "num_images": 1,
            "aspect_ratio": "9:16",
            "output_format": "jpeg",
            "resolution": "4K",
        },
    )
    log(f"fal.ai job submitted — stem: {filename_stem}")
    log(f"[DEBUG] Handler request_id: {getattr(handler, 'request_id', 'N/A')}", "DEBUG")
    return handler


def _collect_image(handler, filename_stem: str) -> tuple[str | None, str | None]:
    """Block until the fal.ai job is done, download locally, return (url, local_path)."""
    log(f"[DEBUG] Collecting result for: {filename_stem} (blocking until ready)", "DEBUG")

    try:
        result = handler.get()
        log(f"[DEBUG] fal.ai raw result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}", "DEBUG")

        images = result.get("images", [])
        log(f"[DEBUG] Images in result: {len(images)}", "DEBUG")

        if not images:
            log(f"fal.ai returned no images for {filename_stem}", "ERROR")
            return None, None

        img_meta = images[0]
        log(f"[DEBUG] Image metadata: {img_meta}", "DEBUG")

        image_url = img_meta.get("url")
        if not image_url:
            log(f"fal.ai image missing URL for {filename_stem}", "ERROR")
            return None, None

        width = img_meta.get("width", "?")
        height = img_meta.get("height", "?")
        log(f"fal.ai image ready — {filename_stem} | {width}x{height} | URL: {image_url}")

        # Download JPEG directly from fal.ai, resize if over 10 MB
        dest = GENERATED_DIR / f"{filename_stem}.jpg"
        log(f"[DEBUG] Downloading JPEG to: {dest}", "DEBUG")
        try:
            req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            raw_kb = len(data) // 1024
            log(f"[DEBUG] Downloaded {raw_kb} KB", "DEBUG")

            limit_bytes = 10 * 1024 * 1024
            if len(data) <= limit_bytes:
                # Already under 10 MB — save as-is
                dest.write_bytes(data)
                log(f"[DEBUG] Under 10 MB — saved as-is", "DEBUG")
            else:
                # Too large — resize and re-compress with Pillow
                log(f"[DEBUG] Over 10 MB — resizing to 1080px wide", "DEBUG")
                img = Image.open(io.BytesIO(data)).convert("RGB")
                orig_w, orig_h = img.size
                scale = 1080 / orig_w
                img = img.resize((1080, int(orig_h * scale)), Image.LANCZOS)
                log(f"[DEBUG] Resized from {orig_w}x{orig_h} to {img.size[0]}x{img.size[1]}", "DEBUG")

                for quality in (88, 75, 60, 45, 30):
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=quality, optimize=True)
                    size = buf.tell()
                    log(f"[DEBUG] Quality={quality} → {size // 1024} KB", "DEBUG")
                    if size <= limit_bytes:
                        dest.write_bytes(buf.getvalue())
                        break

            size_kb = dest.stat().st_size // 1024
            log(f"[DEBUG] Final saved: {size_kb} KB at {dest}", "DEBUG")
            log(f"Image saved locally: {dest} ({size_kb} KB)")
        except Exception as dl_err:
            log(f"Local download failed for {filename_stem}: {type(dl_err).__name__}: {dl_err}", "WARNING")
            dest = None

        return image_url, str(dest) if dest else None

    except Exception as e:
        log(f"fal.ai collection failed for {filename_stem}: {type(e).__name__}: {e}", "ERROR")
        return None, None


def generate_images_for_visuals(visuals: list[dict], article_title: str, style_slug: str = "") -> list[dict]:
    """
    Submit all fal.ai jobs 5 seconds apart (non-blocking), then collect all results.
    style_slug is prepended to filenames to keep styles separate.
    """
    title_slug = _slug(article_title)
    log(f"Starting image generation — {len(visuals)} frames, article: '{article_title}', style: '{style_slug}'")
    log(f"[DEBUG] Visuals to generate: {[v.get('label') for v in visuals]}", "DEBUG")

    # Phase 1: submit all jobs with 5s gap
    handlers = []
    for i, v in enumerate(visuals, 1):
        label_slug = _slug(v.get("label", f"frame_{i}"))
        stem = f"{style_slug}_{title_slug}_{i:02d}_{label_slug}" if style_slug else f"{title_slug}_{i:02d}_{label_slug}"
        v["_stem"] = stem
        log(f"[DEBUG] Submitting image {i}/{len(visuals)} — label: {v.get('label')}, stem: {stem}", "DEBUG")

        try:
            handler = _submit_image(v["image_prompt"], stem)
            handlers.append((v, handler))
            log(f"[DEBUG] Submit {i} OK — handler acquired", "DEBUG")
        except Exception as e:
            log(f"fal.ai submit failed for {stem}: {type(e).__name__}: {e}", "ERROR")
            handlers.append((v, None))

        if i < len(visuals):
            log(f"[DEBUG] Sleeping 5s before next submission ({i+1}/{len(visuals)})", "DEBUG")
            time.sleep(5)

    log(f"All {len(visuals)} jobs submitted — now collecting results")

    # Phase 2: collect in order
    for i, (v, handler) in enumerate(handlers, 1):
        stem = v.pop("_stem")
        log(f"[DEBUG] Collecting image {i}/{len(handlers)} — stem: {stem}", "DEBUG")
        if handler is None:
            log(f"[DEBUG] Skipping collect for {stem} — submit failed", "DEBUG")
            v["image_url"], v["image_path"] = None, None
        else:
            v["image_url"], v["image_path"] = _collect_image(handler, stem)
            log(f"[DEBUG] Collect {i} result — url: {v['image_url']}, path: {v['image_path']}", "DEBUG")

    succeeded = sum(1 for v in visuals if v.get("image_url"))
    log(f"Image generation complete — {succeeded}/{len(visuals)} succeeded")

    log("[DEBUG] Final image summary:", "DEBUG")
    for v in visuals:
        label = v.get("label", "")
        url = v.get("image_url")
        path = v.get("image_path")
        log(f"[DEBUG]   [{label}] url={url} | path={path}", "DEBUG")

    return visuals
