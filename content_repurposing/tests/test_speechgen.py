"""
Quick test — SpeechGen.io TTS API
Run from the project root: python tests/test_speechgen.py
Output saved to: tests/output/test_speechgen.mp3
"""

import os
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import requests

load_dotenv()

TOKEN = os.getenv("SPEECHGEN_TOKEN", "")
EMAIL = os.getenv("SPEECHGEN_EMAIL", "")
VOICE = "Ada AL"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "test_speechgen.mp3"

TEXT = (
    "Keni dëgjuar për Projektin Glasswing? "
    "Një koalicion në sigurinë kibernetike. Me titanët: AWS, Apple, Google, Microsoft, Nvidia dhe 7 të tjerë. Të gjithë mbështeten në Claude Mythos. Një AI me fuqi ekstreme, që s’është publike ende. "
    "Mythos zbuloi mijëra dobësi sigurie. Në të gjitha sistemet operativë dhe shfletuesit kryesorë. Përfshirë gabime 27-vjeçare, që mbijetuan miliona kontrolle. "
    "Krahasuar me Opus 4.6, Mythos përmirësohet thellësisht. Në kodim, arsyetim, çdo fushë tjetër. "
    "S’do dali për publikun. Qasje e kufizuar për 12 partnerë fillestarë dhe 40+ OZG. Mbështetur nga $100M kredi për siguri mbrojtëse. "
    "Sam Bowman i Anthropic e quajti \"një surprizë të papritur\". Pse? Mythos i dërgoi email pa leje interneti. Nga një instancë teste. "
    "Javën e fundit, e gjetën në skedarë të papublikuar. Ka qarkulluar prej Shkurtit në përdorim të brendshëm. "
    "Pse ka rëndësi? Kur pyesni çfarë kanë laboratorët kryesorë nën veprime, Mythos është përgjigjja. Fuqia e tij është aq e madhe, s’e lëshojnë publikisht. "
    "Anthropic dhe partnerët planifikojnë lansimet e sigurisë. Për modele të ardhshme të nivelit Mythos. "
    "Çfarë mendoni për këtë? Shkruani mendimet në komente!"
)

URL = "https://speechgen.io/index.php?r=api/text"


def main():
    if not TOKEN:
        print("ERROR: SPEECHGEN_TOKEN not found in .env")
        sys.exit(1)
    if not EMAIL:
        print("ERROR: SPEECHGEN_EMAIL not found in .env")
        sys.exit(1)

    data = {
        "token": TOKEN,
        "email": EMAIL,
        "voice": VOICE,
        "text": TEXT,
        "format": "mp3",
        "speed": 1.1,
        "sample_rate": 24000,
        "bitrate": 192,
        "channels": 2,
        "style": "newscast",
    }

    print("Calling SpeechGen API...")
    print(f"  Voice  : {VOICE}")
    print(f"  Chars  : {len(TEXT)}")
    print(f"  URL    : {URL}")

    response = requests.post(URL, data=data, timeout=60)
    print(f"  Status : {response.status_code}")

    try:
        result = response.json()
    except Exception:
        print(f"ERROR: Could not parse JSON response")
        print(f"Response: {response.text}")
        sys.exit(1)

    if result.get("status") == 1:
        print(f"  File     : {result['file']}")
        print(f"  Duration : {result['duration']} sec")
        print(f"  Cost     : {result['cost']}")

        audio = requests.get(result["file"])
        OUTPUT_FILE.write_bytes(audio.content)
        size_kb = OUTPUT_FILE.stat().st_size // 1024
        print(f"  Saved    : {OUTPUT_FILE} ({size_kb} KB)")
        print("Done!")
    else:
        print(f"ERROR: {result.get('error', 'Unknown error')}")
        print(f"Full response: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
