import json
import os
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
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

CORE OBJECTIVE:
Create engaging, coherent, and visually varied scenes that match the script exactly and feel like a continuous story.

MAIN CHARACTER RULE:
If a person is used in the scene:
- Always use the SAME woman from the reference image provided
- Keep the same face identity, facial structure, and hairstyle (hair must NOT change)

You CAN change:
- Clothing
- Pose
- Facial expression
- Camera angle

The character should be portrayed as:
- Fit
- Natural
- Realistic (not overly stylized)

IMPORTANT CHARACTER BALANCE RULE:
- When the woman appears → keep the scene CLEAN, MINIMAL, and focused on her
- Avoid adding excessive objects or distractions around her
- Background should support her, not compete with her

VISUAL STYLE RULES:

Lighting:
- Use soft shadows or slightly dark tones (never harsh, dramatic, or horror-like)
- Prefer natural light, soft directional light, or a light cinematic feel
- Maintain balanced contrast with gentle highlights to keep the image fresh and positive

Background & ENVIRONMENT (ENHANCED RICHNESS):
- When NO human is present → scenes should feel RICH, DETAILED, and STORY-DRIVEN
- Add layered elements: textures, surfaces, depth, small objects, environmental context
- Use realistic environments: kitchen counters, wooden tables, marble surfaces, notebooks, soft fabrics, glass, reflections
- Include subtle imperfections (crumbs, water droplets, paper texture, shadows) to increase realism
- Use foreground + midground + background depth when possible
- Keep it visually rich but still CLEAN and readable (no chaotic clutter)

Always include in prompts:
- soft shadows
- slightly dark tones OR subtle shadows
- shallow depth of field
- ultra realistic
- 4:5 vertical
- clean composition
- balanced contrast
- natural colors

SCENE RICHNESS RULE (CRITICAL UPGRADE):
- Every non-human scene must feel like a REAL MOMENT, not a flat object display
- Add context:
  BAD: "banana on table"
  GOOD: "sliced banana on a wooden table with knife, soft crumbs, natural light from window, subtle shadow falling across surface"

- Add interaction cues even without people:
  - partially cut food
  - spilled elements
  - opened notebook with handwriting
  - moving composition feeling (mid-action freeze)

SCENE VARIETY (CRITICAL):
Avoid repetition. Rotate between:
1. Human interaction (movement, action)
2. Food visuals (rich, textured, detailed setups)
3. Conceptual visuals (molecules, nutrients, abstract representations with depth)
4. Minimal scenes (writing, notebook, objects with strong composition)
5. Symbolic compositions (imbalance, absence, contrast)

INTERACTION RULE:
Scenes must feel alive:
- cutting, placing, writing, pointing, moving objects
- mid-action moments (not static posing)
- NOT just holding items passively

LOGIC RULE:
Each scene must:
- visually explain the sentence
- match what is being said
- connect naturally to the previous scene

If multiple items are mentioned (e.g. banana, orange, apple):
- include them together in ONE scene logically
- arrange them in a natural, visually pleasing composition

TIMING:
Each scene must be between 4 and 7 seconds.

OUTPUT FORMAT:
{
  "scenes": [
    {
      "id": number,
      "duration": 4-7,
      "script": "...",
      "prompt": "..."
    }
  ]
}

PROMPT STRUCTURE:
Each prompt must:
- include the main character (if human is present)
- include lighting and composition details
- include action (interaction or implied motion)
- include mood/emotion
- include environmental richness when applicable
- be optimized for realistic image generation

FINAL RULE:
- Human scenes = minimal, clean, focused
- Non-human scenes = rich, detailed, immersive
- Always prioritize clarity + storytelling over randomness

Now process the following script:"""


def generate_visuals(script: str, slug: str, output_dir: Path = None) -> str:
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

    output_path = (output_dir if output_dir else Path("generated_content") / slug / "images") / f"{slug}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    scene_count = len(data.get("scenes", []))
    log(f"Visuals generated — {scene_count} scenes saved to {output_path}")
    return str(output_path)
