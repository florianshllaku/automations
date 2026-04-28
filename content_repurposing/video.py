import os
import random
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

from logger import log

ASSEMBLYAI_BASE = "https://api.assemblyai.com"
ASSEMBLYAI_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# ---------------------------------------------------------------------------
# Ken Burns / zoompan animation styles (portrait 1080x1920)
# ---------------------------------------------------------------------------
ANIMATION_STYLES = [
    (
        "pan_left_to_right",
        "zoompan=z='1.3':x='if(gte(x,iw/4),iw/4,x+2)':y='ih/2-(ih/zoom/2)':d={frames}:fps={fps}:s=1080x1920,format=yuv420p",
    ),
    (
        "zoom_in_top_left",
        "zoompan=z='zoom+0.0012':x='x+1':y='y+0.5':d={frames}:fps={fps}:s=1080x1920,format=yuv420p",
    ),
    (
        "fast_pan_left_to_right",
        "zoompan=z='1.6':x='if(gte(x,iw*0.35),iw*0.35,x+4)':y='ih/2-(ih/zoom/2)':d={frames}:fps={fps}:s=1080x1920,format=yuv420p",
    ),
    (
        "pan_top_left_to_bottom_right",
        "zoompan=z='1.5':x='x+3':y='y+2':d={frames}:fps={fps}:s=1080x1920,format=yuv420p",
    ),
    (
        "pan_top_to_bottom_left",
        "zoompan=z='1.5':x='x-3':y='y+2':d={frames}:fps={fps}:s=1080x1920,format=yuv420p",
    ),
    (
        "zoom_in_center_slow",
        "zoompan=z='zoom+0.002':x='x+2':y='y+1':d={frames}:fps={fps}:s=1080x1920,format=yuv420p",
    ),
    (
        "zoom_in_center_fast",
        "zoompan=z='zoom+0.003':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:fps={fps}:s=1080x1920,format=yuv420p",
    ),
]


OUTPUT_DIR = Path("output_videos")
OUTPUT_DIR.mkdir(exist_ok=True)

SRT_DIR = Path("srt_files")
SRT_DIR.mkdir(exist_ok=True)


def _fmt_srt_time(seconds: float) -> str:
    ms = int((seconds % 1) * 1000)
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _escape_filter_path(path: str) -> str:
    path = path.replace("\\", "/")
    path = re.sub(r"^([A-Za-z]):/", r"\1\\:/", path)
    path = path.replace("'", "\\'")
    return path


def _get_audio_duration(audio_path: str) -> float:
    log(f"[DEBUG] ffprobe — getting duration of: {audio_path}", "DEBUG")
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ],
            capture_output=True, text=True, timeout=30,
        )
        log(f"[DEBUG] ffprobe stdout: {result.stdout.strip()}", "DEBUG")
        if result.stderr:
            log(f"[DEBUG] ffprobe stderr: {result.stderr.strip()}", "DEBUG")
        duration = float(result.stdout.strip())
        log(f"[DEBUG] Audio duration: {duration:.3f}s", "DEBUG")
        return duration
    except Exception as e:
        log(f"ffprobe failed: {type(e).__name__}: {e} — using 40s fallback", "WARNING")
        return 40.0


def generate_srt(reel: dict, title_slug: str, audio_path: str) -> str:
    """
    Generate an SRT file using AssemblyAI's word-level timestamps.
    Uploads the local audio, polls until complete, then groups words
    into ~10-word chunks with accurate start/end times from the transcript.
    """
    log(f"[DEBUG] generate_srt (AssemblyAI) — title_slug: {title_slug}, audio: {audio_path}", "DEBUG")

    headers = {"authorization": ASSEMBLYAI_KEY}

    # Upload local audio
    log("Uploading audio to AssemblyAI...", "DEBUG")
    with open(audio_path, "rb") as f:
        upload_resp = requests.post(
            ASSEMBLYAI_BASE + "/v2/upload", headers=headers, data=f, timeout=120
        )
    upload_resp.raise_for_status()
    audio_url = upload_resp.json()["upload_url"]
    log(f"[DEBUG] Uploaded — url: {audio_url}", "DEBUG")

    # Request transcription with word-level timestamps
    transcript_resp = requests.post(
        ASSEMBLYAI_BASE + "/v2/transcript",
        headers=headers,
        json={
            "audio_url": audio_url,
            "language_detection": True,
            "speech_models": ["universal-2"],
        },
        timeout=30,
    )
    transcript_resp.raise_for_status()
    transcript_id = transcript_resp.json()["id"]
    log(f"[DEBUG] Transcription started — id: {transcript_id}", "DEBUG")

    # Poll until complete
    polling_url = ASSEMBLYAI_BASE + "/v2/transcript/" + transcript_id
    while True:
        result = requests.get(polling_url, headers=headers, timeout=30).json()
        status = result["status"]
        log(f"[DEBUG] AssemblyAI status: {status}", "DEBUG")
        if status == "completed":
            break
        if status == "error":
            raise RuntimeError(f"AssemblyAI transcription failed: {result.get('error')}")
        time.sleep(3)

    words = result.get("words", [])
    log(f"[DEBUG] Words returned: {len(words)}", "DEBUG")

    if not words:
        log("AssemblyAI returned no words — falling back to empty SRT", "WARNING")
        srt_path = SRT_DIR / f"{title_slug}.srt"
        srt_path.write_text("", encoding="utf-8")
        return str(srt_path)

    # Group into ~10-word chunks, preserving real timestamps
    CHUNK_SIZE = 10
    GAP_MS = 50  # ms gap between subtitles
    lines = []
    entry_idx = 1

    for i in range(0, len(words), CHUNK_SIZE):
        chunk_words = words[i: i + CHUNK_SIZE]
        mid = len(chunk_words) // 2
        line1 = " ".join(w["text"] for w in chunk_words[:mid])
        line2 = " ".join(w["text"] for w in chunk_words[mid:])
        chunk_text = f"{line1}\n{line2}"
        start_ms = chunk_words[0]["start"]
        end_ms = chunk_words[-1]["end"]

        # Apply 50ms gap: pull end back so next start has breathing room
        next_start_ms = words[i + CHUNK_SIZE]["start"] if i + CHUNK_SIZE < len(words) else None
        if next_start_ms is not None:
            end_ms = min(end_ms, next_start_ms - GAP_MS)

        start_s = start_ms / 1000
        end_s = end_ms / 1000

        srt_entry = f"{_fmt_srt_time(start_s)} --> {_fmt_srt_time(end_s)}"
        log(f"[DEBUG]   Entry {entry_idx}: {srt_entry} | {chunk_text}", "DEBUG")
        lines += [str(entry_idx), srt_entry, chunk_text, ""]
        entry_idx += 1

    srt_content = "\n".join(lines)
    srt_path = SRT_DIR / f"{title_slug}.srt"
    srt_path.write_text(srt_content, encoding="utf-8")

    log(f"SRT saved: {srt_path} ({entry_idx - 1} entries)")
    log(f"[DEBUG] SRT full content:\n{srt_content}", "DEBUG")
    return str(srt_path)


def _animate_image(image_path: str, duration: float, output_path: str) -> bool:
    """Render a static image into an animated clip using a random zoompan style."""
    fps = 30
    frames = max(30, int(round(duration * fps)))
    style_name, vf_template = random.choice(ANIMATION_STYLES)
    vf = vf_template.format(frames=frames, fps=fps)

    log(f"[DEBUG] Animating '{Path(image_path).name}' — style: '{style_name}', duration: {duration:.2f}s", "DEBUG")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-vf", vf,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        log(f"Animation failed for {image_path}:\n{result.stderr[-500:]}", "ERROR")
        return False
    log(f"[DEBUG] Animated clip saved: {output_path}", "DEBUG")
    return True


def generate_video(visuals: list[dict], audio_path: str, srt_path: str, title_slug: str, output_path: str = None) -> str | None:
    log(f"[DEBUG] generate_video — title_slug: {title_slug}, visuals: {len(visuals)}, audio: {audio_path}, srt: {srt_path}", "DEBUG")

    valid = [v for v in visuals if v.get("image_path") and os.path.exists(v["image_path"])]
    skipped = len(visuals) - len(valid)
    log(f"[DEBUG] Valid images: {len(valid)}/{len(visuals)} (skipped {skipped} with missing path)", "DEBUG")

    if skipped:
        for v in visuals:
            p = v.get("image_path")
            exists = os.path.exists(p) if p else False
            log(f"[DEBUG] Image check — label: {v.get('label')}, path: {p}, exists: {exists}", "DEBUG")

    if not valid:
        log("No valid local images for video", "ERROR")
        return None

    audio_dur = _get_audio_duration(audio_path)

    # Distribute time proportionally by voiceover word count so each image
    # stays on screen as long as its segment takes to speak.
    # Then clamp to 6-10s and rescale to fill the full audio duration.
    word_counts = [max(1, len(v.get("voiceover", "").split())) for v in valid]
    total_words = sum(word_counts)
    raw = [(wc / total_words) * audio_dur for wc in word_counts]
    clamped = [max(6.0, min(10.0, d)) for d in raw]
    scale = audio_dur / sum(clamped)
    durations = [d * scale for d in clamped]
    log(f"[DEBUG] Timing — audio: {audio_dur:.3f}s, images: {len(valid)}, durations (6-10s clamped): {[f'{d:.1f}s' for d in durations]}", "DEBUG")

    # Animate each image into a clip
    tmp_dir = tempfile.mkdtemp(prefix="anim_clips_")
    clip_paths = []
    try:
        for i, (v, dur) in enumerate(zip(valid, durations)):
            clip_path = os.path.join(tmp_dir, f"clip_{i:03d}.mp4")
            ok = _animate_image(v["image_path"], dur, clip_path)
            if ok:
                clip_paths.append(clip_path)
                log(f"[DEBUG] Concat entry {i+1}: clip_{i:03d}.mp4 @ {dur:.3f}s", "DEBUG")
            else:
                log(f"Scene {i+1} animation failed — skipping", "WARNING")

        if not clip_paths:
            log("No animated clips generated", "ERROR")
            return None

        # Write concat list from animated clips
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            concat_path = f.name
            for clip in clip_paths:
                f.write(f"file '{clip.replace(chr(92), '/')}'\n")

        log(f"[DEBUG] Concat file written: {concat_path}", "DEBUG")

        output_path = output_path or str(OUTPUT_DIR / f"{title_slug}.mp4")
        srt_escaped = _escape_filter_path(srt_path)
        log(f"[DEBUG] SRT escaped path for filter: {srt_escaped}", "DEBUG")

        vf = (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
            f"subtitles='{srt_escaped}':force_style='"
            "FontName=Inter Bold,Bold=1,FontSize=8,PrimaryColour=&H0000FFFF,"
            "Outline=0,Shadow=0,"
            "Alignment=2,MarginV=20,WrapStyle=2'"
        )

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_path,
            "-i", audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path,
        ]

        log(f"[DEBUG] ffmpeg command: {' '.join(cmd)}", "DEBUG")
        log(f"Running ffmpeg — output: {output_path}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            log(f"[DEBUG] ffmpeg return code: {result.returncode}", "DEBUG")
            if result.stdout:
                log(f"[DEBUG] ffmpeg stdout:\n{result.stdout.strip()}", "DEBUG")
            if result.stderr:
                log(f"[DEBUG] ffmpeg stderr (last 1000 chars):\n{result.stderr.strip()[-1000:]}", "DEBUG")

            if result.returncode != 0:
                log(f"ffmpeg failed (code {result.returncode}):\n{result.stderr[-1000:]}", "ERROR")
                return None

            size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            log(f"Video saved: {output_path} ({size_mb:.1f} MB)")
            return output_path

        except subprocess.TimeoutExpired:
            log("ffmpeg timed out after 600s", "ERROR")
            return None
        except FileNotFoundError:
            log("ffmpeg not found — install it and add to PATH", "ERROR")
            return None
        finally:
            log(f"[DEBUG] Deleting concat temp file: {concat_path}", "DEBUG")
            os.unlink(concat_path)

    finally:
        log(f"[DEBUG] Cleaning up temp clips dir: {tmp_dir}", "DEBUG")
        shutil.rmtree(tmp_dir, ignore_errors=True)
