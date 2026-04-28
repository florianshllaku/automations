import io
import os
from pathlib import Path
from time import sleep

import requests
from openai import OpenAI
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GLADIA_KEY = os.getenv("GLADIA_KEY", "")
GLADIA_BASE_URL = "https://api.gladia.io"

TTS_VOICE        = "echo"
TTS_MODEL        = "gpt-4o-mini-tts"
TTS_INSTRUCTIONS = """Voice:
I shpejtë, pak i ashpër, me energji "lodhur por funksional" — si dikush që ka parë shumë gjëra, por vazhdon të flasë drejt e në temë.

Tone:
Pak i bezdisur, pak sarkastik, por gjithmonë praktik dhe i dobishëm. Jep ndjesinë "mos humb kohë, dëgjo këtë".

Dialect / Style:
Shqip urban, i thjeshtë, i drejtpërdrejtë. Përdor shprehje të përditshme si:
"Ça po bën?"
"Seriozisht?"
"Po prit pak…"
"Lëre këtë…"

Pronunciation (IMPORTANT for English voice):
Fjali të shkurtra dhe të qarta
Fjalë të thjeshta që lexohen lehtë nga anglishtja
Shmang fjalët shumë të gjata ose me theks të vështirë
Ritëm i shpejtë, me pauza natyrale (,…)

Features:
Shkon direkt në pikë (no fluff)
Përdor pyetje retorike për engagement
Pak humor i thatë ("po normal që jo…")
Jep ndjesinë urgjence ("duhet ta dish këtë")
Ideale për health tips, food facts, quick info"""


WORDS_PER_SUBTITLE = 11  # ~10-12 words per entry split across 2 lines of 5-6 words each


def _seconds_to_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _utterances_to_srt(utterances: list) -> str:
    # Flatten all words across all utterances
    all_words = []
    for utt in utterances:
        all_words.extend(utt.get("words", []))

    if not all_words:
        # Fallback: use utterance-level text if no word timestamps
        lines = []
        for i, utt in enumerate(utterances, 1):
            start = _seconds_to_srt_time(utt["start"])
            end = _seconds_to_srt_time(utt["end"])
            lines.append(f"{i}\n{start} --> {end}\n{utt.get('text', '').strip()}\n")
        return "\n".join(lines)

    # Group into chunks of WORDS_PER_SUBTITLE
    chunks = [all_words[i:i + WORDS_PER_SUBTITLE] for i in range(0, len(all_words), WORDS_PER_SUBTITLE)]

    lines = []
    for i, chunk in enumerate(chunks, 1):
        start = _seconds_to_srt_time(chunk[0]["start"])
        end = _seconds_to_srt_time(chunk[-1]["end"])
        words = [w.get("word", "").strip() for w in chunk]
        # Split into 2 lines at the midpoint
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        text = f"{line1}\n{line2}" if line1 else line2
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def _correct_srt(srt_content: str, script_text: str) -> str:
    """
    Use GPT to fix any misspelled or wrong words in the SRT against the original script.
    Timing lines and structure are preserved exactly — only subtitle text is corrected.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a subtitle corrector. You will receive an original script and an SRT file. "
                    "The SRT was auto-transcribed and may contain misspelled or misheard words. "
                    "Your job: correct any wrong words in the SRT text to match the original script. "
                    "Rules:\n"
                    "- NEVER change any timing lines (lines with --> in them)\n"
                    "- NEVER change sequence numbers\n"
                    "- NEVER add or remove subtitle entries\n"
                    "- ONLY fix words that are misspelled or wrong compared to the script\n"
                    "- Preserve the 2-line format of each subtitle entry\n"
                    "- Return ONLY the corrected SRT content, nothing else"
                ),
            },
            {
                "role": "user",
                "content": f"ORIGINAL SCRIPT:\n{script_text}\n\nSRT TO CORRECT:\n{srt_content}",
            },
        ],
    )
    return (response.choices[0].message.content or srt_content).strip()


def generate_subtitles(audio_path: str | Path, output_path: str | Path, script_text: str = "") -> str:
    """
    Transcribe the audio file with Gladia and save the result as an SRT file.
    If script_text is provided, GPT corrects any misspelled words against it.
    Returns the output path as a string.
    """
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "x-gladia-key": GLADIA_KEY,
        "accept": "application/json",
    }

    # Upload the file
    with open(audio_path, "rb") as f:
        file_content = f.read()
    files = [("audio", (audio_path.name, file_content, "audio/mpeg"))]
    upload_resp = requests.post(
        GLADIA_BASE_URL + "/v2/upload/", headers=headers, files=files
    )
    upload_resp.raise_for_status()
    audio_url = upload_resp.json().get("audio_url")

    # Submit transcription job
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
    post_resp = requests.post(
        GLADIA_BASE_URL + "/v2/pre-recorded/", headers=headers, json=data
    )
    post_resp.raise_for_status()
    result_url = post_resp.json().get("result_url")

    # Poll until done
    while True:
        poll = requests.get(result_url, headers=headers).json()
        status = poll.get("status")
        if status == "done":
            break
        elif status == "error":
            raise RuntimeError(f"Gladia transcription failed: {poll}")
        sleep(2)

    utterances = (
        poll.get("result", {})
            .get("transcription", {})
            .get("utterances", [])
    )
    srt_content = _utterances_to_srt(utterances)

    if script_text:
        srt_content = _correct_srt(srt_content, script_text)

    output_path.write_text(srt_content, encoding="utf-8")
    return str(output_path)


def generate_audio(text: str, output_path: str | Path = "audio_files/audio.mp3") -> str:
    """
    Convert text to speech using OpenAI TTS (echo voice) and save to output_path.
    Returns the output path as a string.
    Raises RuntimeError on API failure.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=text,
        instructions=TTS_INSTRUCTIONS,
        response_format="mp3",
    ) as response:
        audio_bytes = response.read()

    sound = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    faster = sound.speedup(playback_speed=1.2)
    faster.export(output_path, format="mp3")

    return str(output_path)
