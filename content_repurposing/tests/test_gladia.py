import os
import sys
from pathlib import Path
from time import sleep

import requests
from dotenv import load_dotenv

load_dotenv()

GLADIA_KEY = os.getenv("GLADIA_KEY", "")
GLADIA_BASE_URL = "https://api.gladia.io"
AUDIO_FILE = Path(__file__).parent.parent / "generated_content" / "audio" / "a_sht_e_sigurt_t_ushqeheni_vet_m_me_frut.mp3"


WORDS_PER_SUBTITLE = 11  # ~10-12 words per entry split across 2 lines of 5-6 words each


def seconds_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def utterances_to_srt(utterances: list) -> str:
    all_words = []
    for utt in utterances:
        all_words.extend(utt.get("words", []))

    if not all_words:
        lines = []
        for i, utt in enumerate(utterances, 1):
            start = seconds_to_srt_time(utt["start"])
            end = seconds_to_srt_time(utt["end"])
            lines.append(f"{i}\n{start} --> {end}\n{utt.get('text', '').strip()}\n")
        return "\n".join(lines)

    chunks = [all_words[i:i + WORDS_PER_SUBTITLE] for i in range(0, len(all_words), WORDS_PER_SUBTITLE)]
    lines = []
    for i, chunk in enumerate(chunks, 1):
        start = seconds_to_srt_time(chunk[0]["start"])
        end = seconds_to_srt_time(chunk[-1]["end"])
        words = [w.get("word", "").strip() for w in chunk]
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        text = f"{line1}\n{line2}" if line1 else line2
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


if not AUDIO_FILE.exists():
    print(f"- File does not exist: {AUDIO_FILE}")
    sys.exit(1)
print(f"- File exists: {AUDIO_FILE}")

headers = {
    "x-gladia-key": GLADIA_KEY,
    "accept": "application/json",
}

# Step 1: Upload
with open(AUDIO_FILE, "rb") as f:
    file_content = f.read()
files = [("audio", (AUDIO_FILE.name, file_content, "audio/mpeg"))]

print("- Uploading file to Gladia...")
upload_resp = requests.post(GLADIA_BASE_URL + "/v2/upload/", headers=headers, files=files)
print(f"  Status: {upload_resp.status_code}")
upload_data = upload_resp.json()
print(f"  Response: {upload_data}")
audio_url = upload_data.get("audio_url")

if not audio_url:
    print("- Upload failed, no audio_url returned")
    sys.exit(1)

# Step 2: Submit transcription
headers["Content-Type"] = "application/json"
data = {
    "audio_url": audio_url,
    "language_config": {
        "languages": ["sq"],
        "code_switching": False,
    },
    "diarization": False,
    "punctuation_enhanced": False,
}

print("- Sending transcription request...")
post_resp = requests.post(GLADIA_BASE_URL + "/v2/pre-recorded/", headers=headers, json=data)
print(f"  Status: {post_resp.status_code}")
post_data = post_resp.json()
print(f"  Response: {post_data}")
result_url = post_data.get("result_url")

if not result_url:
    print("- No result_url returned")
    sys.exit(1)

# Step 3: Poll
print("- Polling for results...")
while True:
    poll = requests.get(result_url, headers=headers).json()
    status = poll.get("status")
    print(f"  Status: {status}")
    if status == "done":
        break
    elif status == "error":
        print(f"- Transcription failed: {poll}")
        sys.exit(1)
    sleep(2)

# Step 4: Convert to SRT
utterances = poll.get("result", {}).get("transcription", {}).get("utterances", [])
print(f"\n- Got {len(utterances)} utterances")

srt = utterances_to_srt(utterances)
out_path = Path(__file__).parent / "output" / "test_gladia.srt"
out_path.parent.mkdir(exist_ok=True)
out_path.write_text(srt, encoding="utf-8")
print(f"- SRT saved to: {out_path}")
print("\n--- SRT Preview ---")
print(srt[:500])
