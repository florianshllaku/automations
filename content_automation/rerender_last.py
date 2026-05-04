"""
Quick re-render of the last post using the existing background image.
Skips GPT, Fal.ai — just redraws text + logo with current settings.
"""
from pathlib import Path
from text_overlay import overlay_text_and_logo

BG_PATH    = Path("output/sharp_group/bg/bg_3eae4048.jpg")
POST_TEXT  = "Strategjia e qartë sjell sukses!"

placement = {'text_vertical': 'top', 'text_color': 'black', 'needs_overlay': False, 'overlay_vertical': 'top'}

for out in ["output/sharp_group/post_001.jpg", "output/sharp_group/post_001.png"]:
    overlay_text_and_logo(BG_PATH, POST_TEXT, placement, Path(out))

print("Done! Check output/sharp_group/post_001.jpg and post_001.png")
