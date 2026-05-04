"""
Full pipeline: ChatGPT brief -> Gemini image prompt -> 4x Fal.ai backgrounds -> text overlay

Outputs 4 variants per run:
  post_NNN_nano_noref.jpg  — nano-banana-pro, no reference images
  post_NNN_nano_ref.jpg    — nano-banana-pro/edit, with reference images
  post_NNN_gpt_noref.jpg   — gpt-image-2, no reference images
  post_NNN_gpt_ref.jpg     — gpt-image-2/edit, with reference images

Temp bg files are deleted after overlay is applied.

Usage:
  py generator.py sharp_group
  py generator.py sharp_group --text "Aktiviteti nuk është progres."
"""

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

from config import HISTORY_DIR, OUTPUT_DIR
from content_brain import (
    generate_content_brief,
    generate_image_prompts,
    pick_reference_images,
)
from fal_image_gen import (
    generate_gpt_no_ref,
    generate_gpt_with_ref,
    generate_nano_no_ref,
    generate_nano_with_ref,
)


def save_to_history(handle: str, brief: dict, image_prompt: str, output_paths: list[Path]):
    path = HISTORY_DIR / f"{handle}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"handle": handle, "posts": []}

    posts   = data["posts"]
    next_id = (max(p["id"] for p in posts) + 1) if posts else 1

    posts.append({
        "id":                 next_id,
        "date":               date.today().isoformat(),
        "post_type":          brief["post_type"],
        "headline":           brief["post_text"],
        "body_text":          "",
        "caption":            brief["caption"],
        "visual_description": image_prompt[:200],
        "image_path":         str(output_paths[0]),
        "image_variants":     [str(p) for p in output_paths],
        "colors_used":        ["#FF8643", "#080808", "#FFFFFF"],
        "engagement":         {"likes": 0, "comments": 0},
    })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Saved to history as post #{next_id}")


def run(handle: str, custom_text: str = None):
    output_dir = OUTPUT_DIR / handle
    output_dir.mkdir(parents=True, exist_ok=True)
    bg_dir = output_dir / "_bg_temp"

    # Determine next post number
    existing = sorted(output_dir.glob("post_*_nano_noref.jpg"))
    next_num = len(existing) + 1

    print(f"\n{'='*55}")
    print(f"  Sharp Group Post Generator -- #{next_num}")
    print(f"{'='*55}\n")

    # -- Step 1: Content brief (ChatGPT or custom) -----------------------------
    if custom_text:
        print("[1/5] Using custom text (skipping ChatGPT)...")
        brief = {
            "post_type": "educational",
            "theme":     custom_text,
            "post_text": custom_text,
            "caption":   "",
        }
        print(f"  Post text: {brief['post_text']}")
    else:
        print("[1/5] Generating content brief via ChatGPT...")
        brief = generate_content_brief(handle)
        print(f"  Theme:     {brief['theme']}")
        print(f"  Post text: {brief['post_text']}")
        print(f"  Post type: {brief['post_type']}")

    # -- Step 2: Pick 3 random reference images --------------------------------
    print("\n[2/5] Picking 3 random reference images...")
    ref_images = pick_reference_images(handle, n=3)
    for r in ref_images:
        print(f"  -> {r.name}")

    # -- Step 3: Generate image prompt via Gemini Vision -----------------------
    print("\n[3/5] Generating image prompt via Gemini Vision...")
    image_prompts = generate_image_prompts(brief["theme"], brief["post_text"], ref_images, handle)
    chosen_prompt = image_prompts[0]
    print(f"  Prompt: {chosen_prompt[:120]}...")

    # -- Step 4: Generate 4 background images via Fal.ai ----------------------
    print("\n[4/5] Generating 4 background images via Fal.ai...")

    bg_nano_noref = generate_nano_no_ref(chosen_prompt, bg_dir)
    bg_nano_ref   = generate_nano_with_ref(chosen_prompt, ref_images, bg_dir)
    bg_gpt_noref  = generate_gpt_no_ref(chosen_prompt, bg_dir)
    bg_gpt_ref    = generate_gpt_with_ref(chosen_prompt, ref_images, bg_dir)

    # -- Step 5: Move generated images to output dir --------------------------
    print("\n[5/5] Saving 4 background images...")
    variants = [
        ("nano_noref", bg_nano_noref),
        ("nano_ref",   bg_nano_ref),
        ("gpt_noref",  bg_gpt_noref),
        ("gpt_ref",    bg_gpt_ref),
    ]

    output_paths = []
    for label, bg_path in variants:
        out = output_dir / f"post_{next_num:03d}_{label}.jpg"
        shutil.move(str(bg_path), str(out))
        output_paths.append(out)
        print(f"  -> {out.name}")

    shutil.rmtree(bg_dir, ignore_errors=True)

    # -- Save to history -------------------------------------------------------
    save_to_history(handle, brief, chosen_prompt, output_paths)

    print(f"\nDone. 4 posts generated:")
    for p in output_paths:
        print(f"  {p}")
    print(f"\n  Caption ready to copy:\n\n{brief['caption']}\n")
    return output_paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("handle", nargs="?", default="sharp_group")
    parser.add_argument("--text", type=str, default=None, help="Custom on-image text (skips ChatGPT)")
    args = parser.parse_args()
    run(args.handle, custom_text=args.text)
