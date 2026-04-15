import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

audio_file = open("test_openai_tts_echo.mp3", "rb")
transcript = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    temperature=0,
    response_format="srt",
    prompt="Ky është një tekst në gjuhën shqipe që trajton tema të shëndetit dhe mirëqenies, duke përfshirë kujdesin për trupin, ushqyerjen e balancuar, aktivitetin fizik, shëndetin mendor dhe mënyrat për të përmirësuar cilësinë e jetës në përditshmëri.",
)

print(transcript.text)
/