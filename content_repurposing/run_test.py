"""
One-shot test pipeline runner.
Runs the full pipeline for a hardcoded Albanian text and saves
everything under generated_content/test/.
"""
import sys
from pathlib import Path

# Make sure imports resolve from this directory
sys.path.insert(0, str(Path(__file__).parent))

from pipeline import generate_script, generate_visuals
from image_gen import generate_images_from_json
from voice import generate_audio, generate_subtitles
from video import generate_video
from logger import log

ARTICLE_TEXT = (
    "Magnezi është thelbësor për shumë funksione në trup dhe ndikon në shëndetin e përgjithshëm. "
    "Shumë njerëz nuk marrin mjaftueshëm, por kjo mund të përmirësohet përmes ushqimit."
)

SLUG = "test"
BASE = Path("generated_content") / SLUG

def main():
    print("\n" + "="*60)
    print("  TEST PIPELINE — Magnezi")
    print("="*60 + "\n")

    # 1. Generate script
    print("[1/5] Generating script ...")
    script = generate_script(ARTICLE_TEXT)
    script_path = BASE / "scripts" / f"{SLUG}.txt"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(script, encoding="utf-8")
    print(f"  Script saved: {script_path}")
    print(f"  Preview: {script[:120]}...\n")

    # 2. Generate visual prompts JSON
    print("[2/5] Generating visual scene prompts ...")
    visuals_path = generate_visuals(script, SLUG, output_dir=BASE / "images")
    print(f"  Visuals JSON saved: {visuals_path}\n")

    # 3. Generate images from JSON
    print("[3/5] Generating images via fal.ai ...")
    scenes = generate_images_from_json(visuals_path, style_slug=SLUG)
    succeeded = sum(1 for s in scenes if s.get("image_path"))
    print(f"  Images: {succeeded}/{len(scenes)} generated\n")

    # 4. Generate audio
    print("[4/5] Generating audio ...")
    audio_path = generate_audio(script, output_path=str(BASE / "audio" / f"{SLUG}.mp3"))
    print(f"  Audio saved: {audio_path}\n")

    # 5. Generate subtitles
    print("[5/5] Generating subtitles ...")
    srt_path = generate_subtitles(
        audio_path,
        output_path=str(BASE / "subtitles" / f"{SLUG}.srt"),
        script_text=script,
    )
    print(f"  Subtitles saved: {srt_path}\n")

    # 6. Stitch video
    print("[6/6] Stitching video ...")
    if scenes and srt_path:
        visuals_for_video = [
            {
                "image_path": s.get("image_path"),
                "voiceover":  s.get("script", ""),
                "label":      str(s.get("id", i)),
            }
            for i, s in enumerate(scenes)
        ]
        video_out = str(BASE / "video.mp4")
        Path(video_out).parent.mkdir(parents=True, exist_ok=True)
        result = generate_video(visuals_for_video, audio_path, srt_path, SLUG, output_path=video_out)
        if result:
            print(f"  Video saved: {result}")
        else:
            print("  [ERROR] generate_video returned None")
    else:
        print("  Skipping video — missing scenes or subtitles")

    print("\n" + "="*60)
    print("  DONE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
