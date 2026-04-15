from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

script = """Ushqimi i bazuar vetëm në fruta mund të sjellë fibra, vitamina dhe pak kalori, por njëkohësisht mund të shkaktojë mungesë proteinash, mineralesh dhe lëndësh të tjera jetike për organizmin"""

instructions = """Voice:
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

for voice in ["ash", "echo"]:
    output_path = Path(__file__).parent / f"test_openai_tts_{voice}.mp3"
    print(f"Generating voice: {voice} ...")
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=voice,
        input=script,
        instructions=instructions,
        response_format="mp3",
    ) as response:
        response.stream_to_file(output_path)
    size_kb = output_path.stat().st_size // 1024
    print(f"  Saved: {output_path} ({size_kb} KB)")
