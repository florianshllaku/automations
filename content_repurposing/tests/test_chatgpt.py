"""
Quick test — OpenAI ChatGPT API (script generation)
Run from the project root: python tests/test_chatgpt.py
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o"

article_text = """
The Rundown: Perplexity just rolled out a new Plaid integration that lets users connect bank accounts, credit cards, and loans directly to its Computer agent, turning it into a full personal finance hub.

The details:

Plaid's 12K+ bank network feeds into Computer, with users able to pull in checking, credit, loan, and brokerage data for a read-only view of their money.

The agentic system can then build customized tools like budgets, net worth trackers, debt payoff plans, and retirement dashboards via simple text prompts.

The move comes on the heels of Perplexity’s U.S tax integration that autonomously fills out IRS forms and reviews professional-prepared returns.

Perplexity Computer launched in late February, with the agentic pivot helping push Perplexity's ARR past $450M in March, a 50% jump in a single month.

Why it matters: Perplexity built its name trying to out-Google Google, but it’s Computer has completely changed the trajectory. With smart connectors and a powerful AI agent, the company is suddenly competing with Mint, TurboTax, and every other app area it ends up integrating — not just search.
"""

SYSTEM_PROMPT = """Ti je një shkrues i nivelit botëror për skripta të videove të shkurtra, i specializuar në Reels, TikTok dhe YouTube Shorts që bëhen virale. Detyra jote është të marrësh ÇDO artikull në anglisht dhe ta kthesh në një skript shumë tërheqës në shqip, të gatshëm për voice-over.

RREGULLAT E STILIT:

Përziej gjatësinë e fjalive: fjali të shkurtra për impakt, pastaj fjali më të gjata për rrjedhë natyrale
Përdor pyetje retorike për të krijuar kuriozitet (p.sh. "Por çfarë ndodhi vërtet?")
Thekso numrat fuqishëm
Ton i sigurt, ritëm tregimi, si një histori që të mban

STRUKTURA:

Hook (kap vëmendjen menjëherë)
Konteksti
Historia
Zbulimi i madh
Fundi / CTA

OUTPUT:

VETËM skripti, asgjë tjetër
100 deri në 120 fjalë, MOS e tejkalo
Duhet të zgjasë rreth 45–60 sekonda në lexim normal
Përdor vetëm pikësim për pauza (presje, pikëpresje, pika)
Një paragraf i vetëm, pa tituj

GJUHA:

Shkruaj në shqip të thjeshtë, të pastër, të lehtë për t'u shqiptuar
Shmang fjalë të komplikuara ose teknike
Fjalët e huaja DUHET të shkruhen SI SHQIPTOHEN në shqip, jo si në anglisht
RREGULL I DETYRUESHËM për emra:
"Perplexity" → "Prepleksity"
"Google" → "Gugëll"
"Plaid" → "Plajd"
"ChatGPT" → "Chat-Xhi-Pi-Ti"
"OpenAI" → "Open-EJ-AJ"
"Anthropic" → "Anthropik"
Mos përdor ASNJËHERË versionin origjinal anglisht në tekst

CTA:

Mbylle me një pyetje ose një thirrje të thjeshtë si "ndiq për më shumë" ose "like dhe koment"
Mos përdor CTA të komplikuara

DETYRA:
Merr tekstin në anglisht dhe ktheje në një skript në shqip që tingëllon natyral, i fuqishëm dhe viral, duke ndjekur çdo rregull më sipër pa përjashtim."""

USER_PROMPT = f"Now transform this:\n\n{article_text}"


def main():
    if not API_KEY:
        print("ERROR: OPENAI_API_KEY not found in .env")
        sys.exit(1)

    client = OpenAI(api_key=API_KEY)

    print(f"Calling ChatGPT API...")
    print(f"  Model : {MODEL}")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
    )

    script = response.choices[0].message.content
    print(f"\n--- SCRIPT ---\n")
    print(script)
    print(f"\n--- END ---")
    print(f"\n  Tokens used : {response.usage.total_tokens}")
    print("Done!")


if __name__ == "__main__":
    main()
