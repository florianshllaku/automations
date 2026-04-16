#!/usr/bin/env python3
"""
Test pipeline — paste a short script, run the full pipeline, get a video.

Usage:
  1. Edit SLUG and SCRIPT below
  2. cd content_repurposing
  3. python test_pipeline.py

All output goes to:  test_output/{SLUG}/
  ├── images/         ← scene JSON + generated JPGs
  ├── audio/          ← MP3 (1.2x speed)
  ├── subtitles/      ← SRT file
  └── video.mp4       ← final stitched video
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Edit these two things ─────────────────────────────────────────────────────
SLUG = "test_uji_naten"

SCRIPT = """
A e pini ujin që ka qëndruar gjithë natën? Edhe pse duket i sigurt, pas disa orësh mund të kontaminohet. Deri në 12 orë është OK… por pas 24 orësh, më mirë pini ujë të freskët.
"""
# ─────────────────────────────────────────────────────────────────────────────


def step(n: int, label: str):
    print(f"\n{'=' * 54}\n[{n}/5] {label}\n{'=' * 54}")


def main():
    script = SCRIPT.strip()

    if not script or script.startswith("Paste your"):
        print("ERROR: Edit SCRIPT at the top of this file before running.")
        sys.exit(1)

    base = Path("test_output") / SLUG
    images_dir  = base / "images"
    audio_dir   = base / "audio"
    srt_dir     = base / "subtitles"
    video_path  = str(base / "video.mp4")

    for d in (images_dir, audio_dir, srt_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"\nTest pipeline — slug : {SLUG}")
    print(f"Output folder        : test_output/{SLUG}/")
    print(f"Script ({len(script.split())} words):\n{script}\n")

    # 1. Visual prompts JSON
    step(1, "Generating visual prompts (ChatGPT)")
    from pipeline import generate_visuals
    json_path = Path(generate_visuals(script, SLUG, output_dir=images_dir))
    print(f"  Saved: {json_path}")

    # 2. Images
    step(2, "Generating images (fal.ai)")
    from image_gen import generate_images_from_json
    scenes = generate_images_from_json(json_path, style_slug=SLUG)
    ok = sum(1 for s in scenes if s.get("image_path"))
    print(f"  Generated: {ok}/{len(scenes)} images")

    if ok == 0:
        print("ERROR: No images were generated. Aborting.")
        sys.exit(1)

    # 3. Audio
    step(3, "Generating audio (OpenAI TTS, 1.2x speed)")
    from voice import generate_audio
    audio_path = str(audio_dir / f"{SLUG}.mp3")
    generate_audio(script, output_path=audio_path)
    print(f"  Saved: {audio_path}")

    # 4. Subtitles
    step(4, "Generating subtitles (Gladia + GPT correction)")
    from voice import generate_subtitles
    srt_path = str(srt_dir / f"{SLUG}.srt")
    generate_subtitles(audio_path, output_path=srt_path, script_text=script)
    print(f"  Saved: {srt_path}")

    # 5. Stitch video
    step(5, "Stitching video (ffmpeg)")
    from video import generate_video
    visuals = [
        {
            "image_path": s.get("image_path"),
            "voiceover":  s.get("script", ""),
            "label":      str(s.get("id", i)),
        }
        for i, s in enumerate(scenes)
    ]
    result = generate_video(visuals, audio_path, srt_path, SLUG, output_path=video_path)

    print("\n" + "=" * 54)
    if result:
        print(f"SUCCESS — test_output/{SLUG}/video.mp4")
    else:
        print("FAILED — check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
