"""
Quick test — Narakeet list available voices
Run from the project root: python tests/test_narakeet_voices.py
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.getenv("NARAKEET_API_KEY", "")


def main():
    if not API_KEY:
        print("ERROR: NARAKEET_API_KEY not found in .env")
        sys.exit(1)

    url = "https://api.narakeet.com/voices"

    print(f"Fetching available voices from Narakeet...")
    print(f"  URL: {url}\n")

    response = requests.get(
        url,
        headers={
            "x-api-key": API_KEY,
        },
    )

    print(f"  Status: {response.status_code}\n")

    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        print(f"ERROR: {e}")
        print(f"Response: {response.text}")
        sys.exit(1)

    voices = response.json()

    output_file = Path(__file__).parent / "output" / "narakeet_voices.json"
    output_file.write_text(json.dumps(voices, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Saved {len(voices)} voices to {output_file}")


if __name__ == "__main__":
    main()
