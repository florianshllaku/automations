"""
Quick test — Narakeet TTS API
Run from the project root: python tests/test_narakeet.py
Output saved to: tests/output/test_narakeet.m4a
"""

import os
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.getenv("NARAKEET_API_KEY", "")
VOICE = "linda"
LANGUAGE = "Albanian"
SPEED = 1.0
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "test_narakeet.m4a"

TEXT = (
    "Sam Altman parashikoi që AI do krijonte kompaninë e parë miliardëshe me një person — "
    "dhe kjo tashmë po ndodh. Një sipërmarrës ndërtoi një biznes që gjeneron qindra miliona "
    "vetëm me ndihmën e AI, pa ekip të madh apo investitorë. Pyetja nuk është më nëse AI po "
    "ndryshon lojën, por nëse po vepron ndërkohë që të tjerët vetëm po flasin."
)


def main():
    if not API_KEY:
        print("ERROR: NARAKEET_API_KEY not found in .env")
        sys.exit(1)

    url = f"https://api.narakeet.com/text-to-speech/m4a?voice={VOICE}&voice-speed={SPEED}&language={LANGUAGE}"

    print(f"Calling Narakeet API...")
    print(f"  Voice    : {VOICE}")
    print(f"  Language : {LANGUAGE}")
    print(f"  Speed    : {SPEED}")
    print(f"  Chars : {len(TEXT)}")
    print(f"  URL   : {url}")

    response = requests.post(
        url,
        headers={
            "Accept": "application/octet-stream",
            "Content-Type": "text/plain",
            "x-api-key": API_KEY,
        },
        data=TEXT.encode("utf-8"),
    )

    print(f"  Status: {response.status_code}")

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        print(f"ERROR: {e}")
        print(f"Response: {response.text}")
        sys.exit(1)

    OUTPUT_FILE.write_bytes(response.content)
    size_kb = OUTPUT_FILE.stat().st_size // 1024
    print(f"  Saved : {OUTPUT_FILE} ({size_kb} KB)")
    print("Done!")


if __name__ == "__main__":
    main()
