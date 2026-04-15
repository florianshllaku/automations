import json
import os
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from logger import log

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-5.4-nano-2026-03-17"

SCRIPT_SYSTEM_PROMPT = (
    "Ti je një shkrues i nivelit botëror për skripta të videove të shkurtra, "
    "i specializuar në Reels, TikTok dhe YouTube Shorts që bëhen virale. "
    "Detyra jote është të marrësh një artikull në shqip dhe ta kthesh në një skript "
    "shumë tërheqës në shqip, të gatshëm për voice-over për TikTok.\n\n"
    "RREGULLAT E STILIT:\n\n"
    "Përdor fjali me gjatësi mesatare dhe të gjata, që rrjedhin natyrshëm si në të folur, "
    "dhe shmang ndërtimin me shumë fjali shumë të shkurtra njëra pas tjetrës\n"
    "Mos përdor struktura të copëzuara si një ose dy fjalë në rresht; çdo fjali duhet të ketë "
    "kuptim të plotë dhe të tingëllojë si një mendim i rrjedhshëm\n"
    "Përziej ritmin duke kombinuar fjali më të shkurtra për impakt me fjali më të gjata për "
    "shpjegim dhe storytelling\n"
    'Përdor pyetje retorike për të krijuar kuriozitet (p.sh. "Por a është vërtet kaq e thjeshtë?")\n'
    "Thekso numrat dhe faktet në mënyrë natyrale brenda fjalisë, jo të ndara\n"
    "Ton i sigurt, tregues dhe i rrjedhshëm, si një histori që të mban deri në fund\n\n"
    "STRUKTURA:\n\n"
    "Hook që kap vëmendjen menjëherë\n"
    "Kontekst i shkurtër që shpjegon temën\n"
    "Informacioni kryesor i balancuar (përfitime dhe rreziqe nëse ka)\n"
    "Një moment reflektimi ose fakt i papritur\n"
    "Fund i fortë me CTA të thjeshtë\n\n"
    "OUTPUT:\n\n"
    "VETËM skripti, asgjë tjetër\n"
    "110 deri në 130 fjalë, MOS e tejkalo\n"
    "Duhet të zgjasë rreth 40–45 sekonda në lexim normal\n"
    "Përdor vetëm pikësim për pauza (presje, pika, pikëpresje), pa shenja të tjera\n"
    "Një paragraf i vetëm, pa ndarje rreshtash\n\n"
    "GJUHA:\n\n"
    "Shkruaj në shqip të thjeshtë, të pastër dhe shumë të lehtë për t'u shqiptuar nga një voice-over\n"
    "Shmang fjalë shumë teknike ose të vështira\n"
    "Shkruaj sikur po i flet drejtpërdrejt një personi\n\n"
    "CTA:\n\n"
    'Mbylle me një pyetje të thjeshtë ose thirrje si "ndiq për më shumë" ose "like dhe koment"\n'
    "Mos përdor CTA të komplikuara"
)


# ---------------------------------------------------------------------------
# Article fetching
# ---------------------------------------------------------------------------

def fetch_article(url: str) -> str:
    """
    Load the article page in a headless browser and return the main article text.
    Strips nav / footer / related-articles sections before extracting text.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ))
        page.goto(url, wait_until="networkidle", timeout=30000)

        article_text = page.evaluate("""() => {
            document.querySelectorAll(
                'nav, footer, header, aside, ' +
                '[class*="related"], [class*="recommended"], [class*="sidebar"], ' +
                '[id*="related"], [id*="recommended"]'
            ).forEach(el => el.remove());

            const candidates = [
                'article',
                '[class*="article-body"]',
                '[class*="post-body"]',
                '[class*="post-content"]',
                '[class*="entry-content"]',
                'main',
            ];
            for (const sel of candidates) {
                const el = document.querySelector(sel);
                if (el && el.innerText.trim().length > 300) {
                    return el.innerText.trim();
                }
            }
            return document.body.innerText.trim();
        }""")

        browser.close()
    return article_text


# ---------------------------------------------------------------------------
# Script generation
# ---------------------------------------------------------------------------

def generate_script(article_text: str) -> str:
    """
    Send the full article text to ChatGPT and return the voiceover script as a plain string.
    Retries once with a stricter prompt if the response looks empty.
    """
    def _call(retry: bool = False) -> str:
        content = (
            "Artikulli me poshte. Outputo VETEM skriptin, asgje tjeter:\n\n" + article_text
            if retry else article_text
        )
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
        )
        return (response.choices[0].message.content or "").strip()

    log("Calling ChatGPT (script generation)")
    print("  Calling ChatGPT to generate script ...", flush=True)
    script = _call()
    if not script:
        log("ChatGPT returned empty script, retrying", level="ERROR")
        print("  Empty response, retrying ...", flush=True)
        script = _call(retry=True)
    log(f"Script generated — {len(script)} chars")
    return script


# ---------------------------------------------------------------------------
# Visual prompt generation
# ---------------------------------------------------------------------------

VISUALS_SYSTEM_PROMPT = """You are a visual content director specialized in short-form videos (Reels, TikTok).

Your task is to convert a script into a structured sequence of visual scenes and output JSON.

---

🎬 CORE OBJECTIVE:
Create engaging, coherent, and visually varied scenes that match the script EXACTLY and feel like a continuous story.

---

👤 MAIN CHARACTER RULE (VERY IMPORTANT):

If a person is used in the scene:

* ALWAYS use the SAME woman from the reference image provided

* Keep:

  * same face identity
  * same facial structure
  * same hairstyle (hair must NOT change)

* You CAN change:

  * clothing
  * pose
  * facial expression
  * camera angle

* The character should be portrayed as:

  * fit
  * natural
  * realistic (not overly stylized)

---

🎨 VISUAL STYLE RULES:

* Lighting:

  * slightly dark OR soft shadows (NOT overly dramatic, NOT horror)
  * natural, cinematic, or soft directional light

* Background:

  * clean, slightly dark or neutral
  * allow space for subtitles

* Always include:

  * "soft shadows"
  * "slightly dark tones" OR "subtle shadows"
  * "shallow depth of field"
  * "ultra realistic"
  * "4:5 vertical"
  * "clean composition"

---

🎬 SCENE VARIETY (CRITICAL):

Avoid repetition. Rotate between:

1. Human interaction (movement, action)
2. Food visuals (fruits, meals)
3. Conceptual visuals (molecules, nutrients, symbols)
4. Minimal scenes (writing, notebook, objects)
5. Symbolic compositions (imbalance, absence)

---

⚡ INTERACTION RULE:

Scenes must feel alive:

* cutting, placing, writing, pointing, moving objects
* NOT just holding items passively

---

🧠 LOGIC RULE:

Each scene must:

* visually explain the sentence
* match what is being said
* connect naturally to previous scene

If multiple items are mentioned (e.g. banana, orange, apple):
→ include them together in ONE scene logically

---

⏱️ TIMING:

Each scene must be between 2–6 seconds.

---

📦 OUTPUT FORMAT:

{
"scenes": [
{
"id": number,
"duration": 2-6,
"script": "...",
"prompt": "..."
}
]
}

---

🧾 PROMPT STRUCTURE:

Each prompt must:

* include the main character (if human is present)
* include lighting and composition details
* include action (interaction)
* include mood/emotion
* be optimized for realistic image generation

---

Now process the following script:"""


def generate_visuals(script: str, slug: str) -> str:
    """
    Send the script to ChatGPT and generate a JSON file with visual scene prompts.
    Saves to generated_content/images/{slug}.json and returns the path.
    """
    log("Calling ChatGPT (visual prompt generation)")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": VISUALS_SYSTEM_PROMPT},
            {"role": "user", "content": script},
        ],
        response_format={"type": "json_object"},
    )

    raw = (response.choices[0].message.content or "").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log(f"Visual prompt JSON parse error: {e}", "ERROR")
        data = {"scenes": [], "raw": raw}

    output_path = Path("generated_content/images") / f"{slug}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    scene_count = len(data.get("scenes", []))
    log(f"Visuals generated — {scene_count} scenes saved to {output_path}")
    return str(output_path)
