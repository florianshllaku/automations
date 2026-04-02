import os
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from logger import log

load_dotenv()

_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

AUDIO_DIR = Path("audio_files")
AUDIO_DIR.mkdir(exist_ok=True)


def generate_audio(text: str, output_path: str | Path = "audio_files/audio.mp3") -> str:
    """
    Convert text to speech using ElevenLabs and save to output_path.
    Returns the output path as a string.
    Raises RuntimeError on API failure.
    """
    output_path = Path(output_path)

    log(f"[DEBUG] ElevenLabs TTS — voice_id: {_VOICE_ID}, model: eleven_multilingual_v2, chars: {len(text)}", "DEBUG")
    log(f"[DEBUG] Script preview: {text[:120]}{'...' if len(text) > 120 else ''}", "DEBUG")
    log(f"ElevenLabs TTS call started — voice_id={_VOICE_ID}, chars={len(text)}")

    audio = _client.text_to_speech.convert(
        voice_id=_VOICE_ID,
        text=text,
        model_id="eleven_multilingual_v2",
    )

    log(f"[DEBUG] ElevenLabs response received — writing chunks to {output_path}", "DEBUG")
    chunk_count = 0
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
            chunk_count += 1

    size_kb = output_path.stat().st_size // 1024
    log(f"[DEBUG] Audio written — {chunk_count} chunks, {size_kb} KB, path: {output_path}", "DEBUG")
    log(f"ElevenLabs TTS complete — saved to {output_path} ({size_kb} KB)")
    return str(output_path)
