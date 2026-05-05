"""
Generates background images via Fal.ai using GPT-Image-2 only.
  - openai/gpt-image-2       (no reference images)
  - openai/gpt-image-2/edit  (with reference images)
"""

import os
import time
import uuid
import urllib.request
from pathlib import Path

import fal_client
from config import FAL_KEY

os.environ["FAL_KEY"] = FAL_KEY

GPT_MODEL      = "fal-ai/gpt-image-2"
GPT_EDIT_MODEL = "fal-ai/gpt-image-2/edit"

_MAX_RETRIES = 3
_RETRY_DELAY = 8


def _upload_references(image_paths: list[Path]) -> list[str]:
    urls = []
    for path in image_paths:
        url = fal_client.upload_file(str(path))
        print(f"    Uploaded: {path.name} -> {url}")
        urls.append(url)
    return urls


def _download(url: str, out_path: Path) -> Path:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        out_path.write_bytes(resp.read())
    return out_path


def _full_prompt(prompt: str) -> str:
    return prompt + " No text, no letters, no logos, no watermarks anywhere in the image."


def _run(model: str, arguments: dict, out_path: Path) -> Path:
    last_err = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            result = fal_client.subscribe(model, arguments=arguments)
            images = result.get("images", [])
            if not images:
                raise RuntimeError(f"Fal.ai ({model}) returned no images")
            return _download(images[0]["url"], out_path)
        except Exception as e:
            last_err = e
            if attempt < _MAX_RETRIES:
                print(f"  [retry {attempt}/{_MAX_RETRIES}] {model} failed: {e}. Retrying in {_RETRY_DELAY}s...")
                time.sleep(_RETRY_DELAY)
    raise last_err


# ── gpt-image-2 ───────────────────────────────────────────────────────────────

def generate_gpt_no_ref(prompt: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"gpt_noref_{uuid.uuid4().hex[:8]}.jpg"
    print("  [gpt-image-2] Generating WITHOUT reference images...")
    return _run(GPT_MODEL, {
        "prompt": _full_prompt(prompt),
        "aspect_ratio": "4:5",
        "num_images": 1,
        "output_format": "jpeg",
    }, out_path)


def generate_gpt_with_ref(prompt: str, ref_paths: list[Path], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"gpt_ref_{uuid.uuid4().hex[:8]}.jpg"
    print("  [gpt-image-2/edit] Uploading refs and generating WITH reference images...")
    ref_urls = _upload_references(ref_paths)
    return _run(GPT_EDIT_MODEL, {
        "prompt": _full_prompt(prompt),
        "image_urls": ref_urls,
        "aspect_ratio": "4:5",
        "num_images": 1,
        "output_format": "jpeg",
    }, out_path)
