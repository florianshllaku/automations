import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from jinja2 import Environment, FileSystemLoader
from config import TEMPLATES_DIR, OUTPUT_DIR, INSTAGRAM_WIDTH, INSTAGRAM_HEIGHT


def get_template_for_layout(layout: str, color_mood: str) -> str:
    """Map layout + mood to a template file."""
    mapping = {
        ("text_only", "dark"):   "text_only_dark.html",
        ("text_only", "light"):  "text_only_light.html",
        ("text_only", "accent"): "text_only_accent.html",
        ("image_bg",  "dark"):   "image_bg_dark.html",
        ("image_bg",  "light"):  "image_bg_light.html",
        ("image_bg",  "accent"): "image_bg_accent.html",
        ("split",     "dark"):   "split_dark.html",
        ("split",     "light"):  "split_light.html",
        ("split",     "accent"): "split_accent.html",
    }
    key = (layout, color_mood)
    return mapping.get(key, "text_only_dark.html")


async def render_post(brief: dict, profile: dict, bg_image_path: str = None) -> Path:
    """
    Renders the HTML template to a PNG and saves it.
    Returns the output file path.
    """
    handle = profile["business"]["handle"]
    output_dir = OUTPUT_DIR / handle
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find next post number
    existing = sorted(output_dir.glob("post_*.png"))
    next_num = len(existing) + 1
    output_path = output_dir / f"post_{next_num:03d}.png"

    template_name = get_template_for_layout(brief["layout"], brief["color_mood"])

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template(template_name)

    html = template.render(
        headline=brief["headline"],
        body_text=brief["body_text"],
        brand=profile["brand"],
        business=profile["business"],
        logo_path=(Path.cwd() / profile["assets"]["logo"]).as_uri(),
        bg_image_path=Path(bg_image_path).as_uri() if bg_image_path else "",
        width=INSTAGRAM_WIDTH,
        height=INSTAGRAM_HEIGHT,
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            viewport={"width": INSTAGRAM_WIDTH, "height": INSTAGRAM_HEIGHT}
        )
        await page.set_content(html, wait_until="networkidle")
        await page.screenshot(path=str(output_path), full_page=False)
        await browser.close()

    print(f"Rendered: {output_path}")
    return output_path


def render_post_sync(brief: dict, profile: dict, bg_image_path: str = None) -> Path:
    return asyncio.run(render_post(brief, profile, bg_image_path))
