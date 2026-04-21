import io
import json
import os
import re
import urllib.request
from pathlib import Path

import fal_client
from PIL import Image
from dotenv import load_dotenv
from logger import log

load_dotenv()

os.environ.setdefault("FAL_KEY", os.getenv("FAL_KEY", ""))

ASSETS_DIR = Path("assets")
REFERENCE_IMAGE_PATH = ASSETS_DIR / "women.png"
REFERENCE_URL_CACHE = ASSETS_DIR / "women_url.txt"

MODEL = "fal-ai/nano-banana-pro"
MODEL_EDIT = "fal-ai/nano-banana-pro/edit"


def _slug(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:40].strip("_")


def _upload_reference_image() -> str | None:
    """
    Upload women.png to fal.ai and cache the URL in assets/women_url.txt.
    On subsequent runs, reuses the cached URL without re-uploading.
    Delete women_url.txt to force a fresh upload.
    """
    if not REFERENCE_IMAGE_PATH.exists():
        log(f"Reference image not found at {REFERENCE_IMAGE_PATH} — skipping character reference", "WARNING")
        return None

    if REFERENCE_URL_CACHE.exists():
        cached_url = REFERENCE_URL_CACHE.read_text(encoding="utf-8").strip()
        if cached_url:
            log(f"Using cached reference image URL: {cached_url}")
            return cached_url

    log(f"Uploading reference image: {REFERENCE_IMAGE_PATH}")
    url = fal_client.upload_file(str(REFERENCE_IMAGE_PATH))
    log(f"Reference image uploaded: {url}")
    ASSETS_DIR.mkdir(exist_ok=True)
    REFERENCE_URL_CACHE.write_text(url, encoding="utf-8")
    log(f"URL cached to {REFERENCE_URL_CACHE}")
    return url


def _submit_image(image_prompt: str, filename_stem: str, reference_url: str | None = None):
    """Submit a single job to fal.ai and return the handler."""
    log(f"fal.ai submit — stem: {filename_stem}")
    log(f"[DEBUG] Prompt preview: {image_prompt[:120]}{'...' if len(image_prompt) > 120 else ''}", "DEBUG")

    arguments = {
        "prompt": image_prompt,
        "num_images": 1,
        "aspect_ratio": "9:16",
        "output_format": "jpeg",
        "resolution": "4K",
    }

    if reference_url:
        arguments["image_urls"] = [reference_url]
        log(f"[DEBUG] Reference image attached: {reference_url}", "DEBUG")
        model = MODEL_EDIT
    else:
        model = MODEL

    log(f"[DEBUG] Using model: {model}", "DEBUG")
    handler = fal_client.submit(model, arguments=arguments)
    log(f"[DEBUG] Handler request_id: {getattr(handler, 'request_id', 'N/A')}", "DEBUG")
    return handler


def _collect_image(handler, filename_stem: str, output_dir: Path = None) -> tuple[str | None, str | None]:
    """Block until job is done, download locally, return (url, local_path)."""
    log(f"[DEBUG] Collecting result for: {filename_stem}", "DEBUG")

    if output_dir is None:
        output_dir = Path("generated_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = handler.get()
        images = result.get("images", [])

        if not images:
            log(f"fal.ai returned no images for {filename_stem}", "ERROR")
            return None, None

        img_meta = images[0]
        image_url = img_meta.get("url")
        if not image_url:
            log(f"fal.ai image missing URL for {filename_stem}", "ERROR")
            return None, None

        width = img_meta.get("width", "?")
        height = img_meta.get("height", "?")
        log(f"fal.ai image ready — {filename_stem} | {width}x{height}")

        dest = output_dir / f"{filename_stem}.jpg"
        try:
            req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            raw_kb = len(data) // 1024
            log(f"[DEBUG] Downloaded {raw_kb} KB", "DEBUG")

            limit_bytes = 10 * 1024 * 1024
            if len(data) <= limit_bytes:
                dest.write_bytes(data)
            else:
                log(f"[DEBUG] Over 10 MB — resizing to 1080px wide", "DEBUG")
                img = Image.open(io.BytesIO(data)).convert("RGB")
                orig_w, orig_h = img.size
                scale = 1080 / orig_w
                img = img.resize((1080, int(orig_h * scale)), Image.LANCZOS)
                for quality in (88, 75, 60, 45, 30):
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=quality, optimize=True)
                    if buf.tell() <= limit_bytes:
                        dest.write_bytes(buf.getvalue())
                        break

            size_kb = dest.stat().st_size // 1024
            log(f"Image saved: {dest} ({size_kb} KB)")
        except Exception as dl_err:
            log(f"Download failed for {filename_stem}: {type(dl_err).__name__}: {dl_err}", "WARNING")
            dest = None

        return image_url, str(dest) if dest else None

    except Exception as e:
        log(f"fal.ai collection failed for {filename_stem}: {type(e).__name__}: {e}", "ERROR")
        return None, None


def generate_images_from_json(json_path: str, style_slug: str = "scene") -> list[dict]:
    """
    Read a visuals JSON file (generated_content/images/{slug}.json),
    generate images one by one via fal.ai, and return updated scenes with image_path.

    Attaches assets/women.png as a reference image if it exists.
    """
    json_path = Path(json_path)
    if not json_path.exists():
        log(f"Visuals JSON not found: {json_path}", "ERROR")
        return []

    data = json.loads(json_path.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])

    if not scenes:
        log("No scenes found in visuals JSON", "WARNING")
        return []

    log(f"Starting image generation — {len(scenes)} scenes from {json_path.name}")

    # Upload reference image once
    reference_url = _upload_reference_image()

    results = []
    for scene in scenes:
        scene_id = scene.get("id", len(results) + 1)
        prompt = scene.get("prompt", "")
        label = _slug(scene.get("script", f"scene_{scene_id}")[:30])
        stem = f"{style_slug}_{scene_id:02d}_{label}"

        log(f"Generating scene {scene_id}/{len(scenes)} — {stem}")

        try:
            scene_ref = reference_url if scene.get("use_character", True) else None
            handler = _submit_image(prompt, stem, reference_url=scene_ref)
            image_url, image_path = _collect_image(handler, stem, output_dir=json_path.parent)
        except Exception as e:
            log(f"Scene {scene_id} failed: {type(e).__name__}: {e}", "ERROR")
            image_url, image_path = None, None

        results.append({**scene, "image_url": image_url, "image_path": image_path})

    succeeded = sum(1 for r in results if r.get("image_url"))
    log(f"Image generation complete — {succeeded}/{len(scenes)} succeeded")
    return results
