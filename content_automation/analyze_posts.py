"""
Analyzes uploaded Sharp Group posts with GPT-4o Vision
to extract the visual design pattern.
"""

import base64
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

UPLOAD_DIR = Path("assets/sharp_group/uploaded_posts")
images = sorted(UPLOAD_DIR.glob("*.jpg")) + sorted(UPLOAD_DIR.glob("*.png"))

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

print(f"Found {len(images)} images. Sending to GPT-4o Vision...\n")

content = [
    {
        "type": "text",
        "text": """Analyze these Instagram posts from a digital marketing agency called Sharp Group.

For each post, describe in detail:
1. Background (color, texture, gradient, image, pattern)
2. Layout structure (how elements are arranged top to bottom)
3. Typography (font sizes roughly, weight, color, alignment)
4. How the headline/text is positioned and styled
5. Use of orange color — where exactly, how much
6. Logo placement and size
7. Any graphic elements (lines, bars, shapes, icons, overlays)
8. Overall spacing and padding feel

Then at the end, give a UNIFIED DESIGN PATTERN that describes what ALL posts have in common — the repeatable template structure."""
    }
]

for img_path in images:
    b64 = encode_image(img_path)
    content.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{b64}",
            "detail": "high"
        }
    })

response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=3000,
    messages=[{"role": "user", "content": content}]
)

result = response.choices[0].message.content
print(result)

with open("vision_analysis.txt", "w", encoding="utf-8") as f:
    f.write(result)

print("\n\nSaved to vision_analysis.txt")
