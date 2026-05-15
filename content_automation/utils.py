import re
import base64
import json
from pathlib import Path

import numpy as np
from PIL import Image


def encode_image(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_json_from_text(text: str) -> dict:
    """Parse JSON from an LLM response, stripping markdown fences and finding the first {...} block."""
    text = re.sub(r"^```[a-z]*\n?", "", text.strip())
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        text = m.group(0)
    return json.loads(text)


def file_url(path: Path) -> str:
    return path.resolve().as_uri()


def strip_white_bg(src: Path, dst: Path, threshold: int = 240) -> Path:
    """Remove near-white background from a PNG logo, crop internal padding, save to dst."""
    img  = Image.open(src).convert("RGBA")
    data = np.array(img, dtype=np.uint8)
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
    white_mask = (r >= threshold) & (g >= threshold) & (b >= threshold)
    data[:, :, 3] = np.where(white_mask, 0, a)
    result = Image.fromarray(data)
    bbox = result.getbbox()
    if bbox:
        result = result.crop(bbox)
    result.save(dst)
    return dst
