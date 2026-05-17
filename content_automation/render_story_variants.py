import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import ASSETS_DIR, OUTPUT_DIR
from turizem_story_renderer import render_story

ASSETS = ASSETS_DIR / "turizem"
bg = ASSETS / "background.jpg"

for i in range(1, 11):
    out = OUTPUT_DIR / "turizem" / f"story_variant_{i:02d}.jpg"
    print(f"Rendering variant {i}...")
    render_story(
        template_name = f"turizem_story_v{i}.html",
        bg_path       = bg,
        output_path   = out,
        destination   = "VERONA",
        price         = "159",
        includes_text = "BILETA • HOTELI • TAKSAT",
        event_badge   = "",
    )
    print(f"  -> {out}")

print("All done!")
