"""
Sharp Group Content Studio — Web UI
Run: python web_app.py
Default password: set UI_PASSWORD in .env  (fallback: sharpgroup2024)
"""
from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from openai import OpenAI
from PIL import Image
from google import genai as google_genai

from config import (
    ASSETS_DIR,
    GEMINI_API_KEY,
    HISTORY_DIR,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OUTPUT_DIR,
)
from content_brain import COMPOSITION_RULES, generate_content_brief, pick_reference_images
from fal_image_gen import generate_gpt_no_ref
from html_renderer import render_post

# ── App setup ─────────────────────────────────────────────────────────────────

HANDLE = "sharp_group"
GEMINI_MODEL_ID = "gemini-3-flash-preview"

UI_PASSWORD = os.getenv("UI_PASSWORD", "sharpgroup2024")

app = Flask(__name__, template_folder="templates/ui")
app.secret_key = os.getenv("SECRET_KEY", "sharp-group-studio-secret-2024")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)

# In-memory job store (keyed by job_id)
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── History helpers ───────────────────────────────────────────────────────────

def load_full_history() -> list[dict]:
    path = HISTORY_DIR / f"{HANDLE}.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return list(reversed(data.get("posts", [])))


def save_post_to_history(post_data: dict) -> int:
    path = HISTORY_DIR / f"{HANDLE}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"handle": HANDLE, "posts": []}

    posts = data.get("posts", [])
    new_id = (max(p["id"] for p in posts) + 1) if posts else 1

    # Store path relative to OUTPUT_DIR so it's portable
    abs_final = post_data.get("final_path", "")
    try:
        rel_path = str(Path(abs_final).relative_to(OUTPUT_DIR)).replace("\\", "/")
    except ValueError:
        rel_path = abs_final

    entry = {
        "id": new_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "post_type": post_data.get("post_type", "promotional"),
        "headline": post_data.get("post_text", ""),
        "body_text": "",
        "caption": post_data.get("caption", ""),
        "visual_description": post_data.get("theme", ""),
        "image_path": rel_path,
        "colors_used": ["#FF680B", "#080808", "#F9F9F9"],
        "engagement": {"likes": 0, "comments": 0},
    }
    posts.append(entry)
    data["posts"] = posts
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return new_id


def image_url_for_post(image_path: str) -> str:
    """Convert a history image_path to a URL for display."""
    if not image_path:
        return ""
    p = Path(image_path)
    if p.is_absolute():
        try:
            rel = str(p.relative_to(OUTPUT_DIR)).replace("\\", "/")
            return url_for("serve_output_image", filepath=rel)
        except ValueError:
            pass
        try:
            rel = str(p.relative_to(ASSETS_DIR)).replace("\\", "/")
            return url_for("serve_asset_image", filepath=rel)
        except ValueError:
            return ""
    # Relative path (from history JSON)
    if image_path.startswith("uploads/"):
        filename = image_path[len("uploads/"):]
        return url_for("serve_asset_image", filepath=f"sharp_group/uploaded_posts/{filename}")
    # Assume relative to OUTPUT_DIR
    return url_for("serve_output_image", filepath=image_path)


# Register as a Jinja2 global so templates can call it
app.jinja_env.globals["image_url_for_post"] = image_url_for_post


# ── Content generation helpers ────────────────────────────────────────────────

def brief_from_topic(topic: str) -> dict:
    brand_brain = (ASSETS_DIR / HANDLE / "BRAND.md").read_text(encoding="utf-8")
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=800,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Instagram content strategist for Sharp Group, "
                    "a digital marketing agency. Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": f"""Follow this brand guide exactly (especially section 15 — Copywriting Direction):
---
{brand_brain}
---
User topic: "{topic}"

Create a Sharp Group Instagram post based on this topic.
Rules:
- post_text: Albanian, max 15 words, goes ON the image. Psychologically sharp, observational tone (section 15 style). Wrap 1-3 key words in <span class="hl"> </span>. Use \\n only to separate distinct thought units (max 1 newline). NEVER use <br>.
- caption: Albanian Instagram caption, 60-120 words, same emotionally intelligent tone. No corporate language. Include hashtags. End with "Behu me i mprehte me ne."
- theme: short English internal description of what the post communicates
- post_type: one of tip|educational|promotional|trend

Return exactly:
{{"post_type": "...", "theme": "...", "post_text": "...", "caption": "..."}}""",
            },
        ],
    )
    return json.loads(response.choices[0].message.content)


def brief_from_text(text: str) -> dict:
    brand_brain = (ASSETS_DIR / HANDLE / "BRAND.md").read_text(encoding="utf-8")
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=700,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Instagram content strategist for Sharp Group. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": f"""Follow this brand guide (especially section 15 — Copywriting Direction):
---
{brand_brain}
---
The user has written this post text: "{text}"

Use this text as post_text. Improve it to match section 15 style if needed (max 15 words total, Albanian).
Wrap 1-3 key words in <span class="hl"> </span>.
Generate:
- theme: short English description of what this communicates
- caption: Albanian Instagram caption (60-120 words), emotionally intelligent tone. Include hashtags. End with "Behu me i mprehte me ne."
- post_type: tip|educational|promotional|trend

Return:
{{"post_type": "...", "theme": "...", "post_text": "...", "caption": "..."}}""",
            },
        ],
    )
    return json.loads(response.choices[0].message.content)


def _generate_prompt_for_style(
    theme: str, post_text: str, ref_images: list, layout: str, style: str
) -> str:
    """Call Gemini Vision to produce a Fal.ai image prompt with an explicit visual style."""
    brand_brain = (ASSETS_DIR / HANDLE / "BRAND.md").read_text(encoding="utf-8")
    pil_images = [Image.open(p) for p in ref_images]

    style_instructions = {
        "3d_graphics": (
            "STYLE REQUIREMENT: Use Style A — a premium 3D abstract/geometric/symbolic composition. "
            "No people, no photographs. Use symbolic objects (chess pieces, targets, arrows, graphs, "
            "funnels, etc.) inside rich visual scenes with geometric depth, layered elements, and "
            "repeating patterns. Follow section 7 and 16 of the brand guide exactly."
        ),
        "real_person": (
            "STYLE REQUIREMENT: Use Style B — a photorealistic person in a business or digital context. "
            "Studio quality, seamless off-white background. Full figure visible in the bottom 40-50% "
            "of the frame only, leaving the top clean. Smart casual or professional clothing in neutral/"
            "dark tones. Orange accent details in the environment. MANDATORY: If phone/tablet/laptop "
            "is visible, the screen MUST show real social media app icons (Instagram pink-orange gradient, "
            "TikTok black with cyan/pink, Facebook blue 'f', YouTube red play, LinkedIn blue 'in', "
            "WhatsApp green). Follow section 16 of the brand guide exactly."
        ),
    }

    style_instr = style_instructions.get(style, style_instructions["3d_graphics"])
    comp_rule = COMPOSITION_RULES.get(layout, COMPOSITION_RULES["default"])

    prompt_text = f"""You are a creative director for a digital marketing agency. Write one Fal.ai image generation prompt strictly grounded in the brand guide below.

---
BRAND GUIDE:
{brand_brain}
---

Post theme: "{theme}"
Text that will be placed on the image: "{post_text}"

{style_instr}

The 3 reference images show the agency's existing posts — study the visual quality and level, but your prompt must follow the BRAND GUIDE above.

Non-negotiable rules:
- Absolutely NO text, NO letters, NO words, NO captions, NO logos anywhere in the image
- Orange (#FF680B) as the dominant accent on key objects
- Black for depth and contrast
- Matte or semi-gloss 3D objects, clean lighting, soft dramatic shadows
- Vertical composition 4:5 ratio (1080x1350px)
- Feel: modern, premium, minimal, professional
{comp_rule}

Respond with ONLY valid JSON:
{{"visual_concept": "one sentence explaining the creative choice", "prompt": "the full detailed Fal.ai generation prompt"}}"""

    contents = [prompt_text] + pil_images

    for attempt in range(3):
        try:
            resp = gemini_client.models.generate_content(
                model=GEMINI_MODEL_ID,
                contents=contents,
            )
            raw = resp.text.strip()
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                raw = m.group(0)
            data = json.loads(raw)
            print(f"  [opt] concept: {data['visual_concept']}")
            return data["prompt"]
        except Exception as e:
            print(f"  Gemini prompt gen attempt {attempt+1}/3 failed: {e}")

    raise RuntimeError("Gemini failed to return a valid image prompt after 3 attempts")


def generate_captions(post_text: str, theme: str) -> list[str]:
    """Generate 3 Instagram caption options with hashtags for the selected post."""
    brand_brain = (ASSETS_DIR / HANDLE / "BRAND.md").read_text(encoding="utf-8")
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=1400,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a social media strategist for Sharp Group. Return valid JSON only.",
            },
            {
                "role": "user",
                "content": f"""Brand guide (focus on section 15 — Copywriting Direction):
---
{brand_brain}
---

Post theme: {theme}
Text on image: {post_text}

Generate 3 DISTINCT Instagram caption options in Albanian.
Each caption must:
- Follow Sharp Group's copywriting direction (section 15): psychologically sharp, observational, emotionally intelligent, creates tension or perspective shifts
- Be 60-120 words
- Include 8-12 hashtags at the end (mix: Albanian niche + English marketing + #sharpgroup)
- End with "Behu me i mprehte me ne."
- Feel completely different from the other 2 options (different angle/hook/opening)
- NOT sound generic, corporate, or motivational in a shallow way

Return:
{{"captions": ["caption1 text + hashtags", "caption2 text + hashtags", "caption3 text + hashtags"]}}""",
            },
        ],
    )
    return json.loads(response.choices[0].message.content)["captions"]


# ── Background generation job ─────────────────────────────────────────────────

def _run_generation(job_id: str, mode: str, user_input: str, bg_color: str = "white", cta_text: str = "") -> None:
    """Runs in a background thread. Generates 3 post options."""
    with jobs_lock:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["progress"] = "Building content brief..."

    try:
        # Step 1: Content brief
        if mode == "ai":
            brief = generate_content_brief(HANDLE)
        elif mode == "topic":
            brief = brief_from_topic(user_input)
        else:  # mode == "text"
            brief = brief_from_text(user_input)

        theme = brief["theme"]
        post_text = brief["post_text"]
        caption = brief.get("caption", "")
        post_type = brief.get("post_type", "promotional")

        with jobs_lock:
            jobs[job_id]["progress"] = "Picking reference images..."

        ref_images = pick_reference_images(HANDLE, 3)

        # Step 2: Build 3 option configs based on chosen background
        # All 3 options use the user's chosen bg; vary visual style between them
        layout_map   = {"white": "default", "orange": "orange"}
        template_map = {"white": "default",  "orange": "orange"}

        layout   = layout_map.get(bg_color, "default")
        template = template_map.get(bg_color, "default")

        option_configs = [
            {"layout": layout, "style": "3d_graphics", "template": template, "label": "3D Graphic — V1"},
            {"layout": layout, "style": "real_person",  "template": template, "label": "Real Person"},
            {"layout": layout, "style": "3d_graphics",  "template": template, "label": "3D Graphic — V2"},
        ]

        out_dir = OUTPUT_DIR / HANDLE
        out_dir.mkdir(parents=True, exist_ok=True)

        options: list[dict | None] = [None, None, None]
        option_errors: list[str | None] = [None, None, None]

        def generate_one(idx: int, cfg: dict) -> None:
            try:
                with jobs_lock:
                    jobs[job_id]["progress"] = f"Generating option {idx + 1}/3 ({cfg['label']})..."

                fal_prompt = _generate_prompt_for_style(
                    theme, post_text, ref_images, cfg["layout"], cfg["style"]
                )
                bg_path = generate_gpt_no_ref(fal_prompt, out_dir)
                final_path = out_dir / f"ui_{job_id}_opt{idx}_final.jpg"
                render_post(
                    bg_path, post_text, final_path,
                    cta_text=cta_text if cta_text else None,
                    template=cfg["template"],
                )

                options[idx] = {
                    "bg_path": str(bg_path),
                    "final_path": str(final_path),
                    "post_text": post_text,
                    "theme": theme,
                    "caption": caption,
                    "post_type": post_type,
                    "template": cfg["template"],
                    "style": cfg["style"],
                    "label": cfg["label"],
                    "bg_color": bg_color,
                    "cta_text": cta_text,
                }
            except Exception as e:
                option_errors[idx] = str(e)
                print(f"  Option {idx + 1} failed: {e}")

        threads = [
            threading.Thread(target=generate_one, args=(i, cfg), daemon=True)
            for i, cfg in enumerate(option_configs)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        with jobs_lock:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["options"] = options
            jobs[job_id]["errors"] = option_errors
            jobs[job_id]["progress"] = "Done"

    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)
        print(f"  Job {job_id} failed: {e}")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("logged_in") else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password", "") == UI_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        error = "Fjalëkalimi i gabuar. Provo përsëri."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    posts = load_full_history()
    return render_template("dashboard.html", posts=posts)


@app.route("/create")
@login_required
def create():
    return render_template("create.html")


@app.route("/api/generate", methods=["POST"])
@login_required
def api_generate():
    data = request.get_json(force=True)
    mode       = data.get("mode", "ai")
    user_input = data.get("input", "").strip()
    bg_color   = data.get("bg_color", "white")   # "white" | "orange"
    cta_text   = data.get("cta_text", "").strip()

    if mode in ("topic", "text") and not user_input:
        return jsonify({"error": "Input required for this mode"}), 400

    if bg_color not in ("white", "orange"):
        bg_color = "white"

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {
            "status": "pending",
            "progress": "Queued...",
            "options": None,
            "errors": None,
            "error": None,
        }

    threading.Thread(
        target=_run_generation,
        args=(job_id, mode, user_input, bg_color, cta_text),
        daemon=True,
    ).start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
@login_required
def api_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "status": job["status"],
        "progress": job.get("progress", ""),
        "error": job.get("error"),
    })


@app.route("/select/<job_id>")
@login_required
def select_post(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return redirect(url_for("create"))
    options = job.get("options", [])
    # Build image URLs for each option
    option_urls = []
    for opt in options:
        if opt:
            try:
                rel = str(Path(opt["final_path"]).relative_to(OUTPUT_DIR)).replace("\\", "/")
                img_url = url_for("serve_output_image", filepath=rel)
            except ValueError:
                img_url = ""
            option_urls.append(img_url)
        else:
            option_urls.append(None)
    return render_template("select.html", job_id=job_id, options=options, option_urls=option_urls)


@app.route("/caption/<job_id>/<int:option_idx>")
@login_required
def caption_page(job_id, option_idx):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return redirect(url_for("dashboard"))
    options = job.get("options", [])
    if option_idx >= len(options) or not options[option_idx]:
        return redirect(url_for("select_post", job_id=job_id))
    option = options[option_idx]
    try:
        rel = str(Path(option["final_path"]).relative_to(OUTPUT_DIR)).replace("\\", "/")
        img_url = url_for("serve_output_image", filepath=rel)
    except ValueError:
        img_url = ""
    return render_template(
        "caption.html",
        job_id=job_id,
        option_idx=option_idx,
        option=option,
        img_url=img_url,
    )


@app.route("/api/captions", methods=["POST"])
@login_required
def api_captions():
    data = request.get_json(force=True)
    job_id = data.get("job_id")
    option_idx = int(data.get("option_idx", 0))

    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    options = job.get("options", [])
    if option_idx >= len(options) or not options[option_idx]:
        return jsonify({"error": "Option not available"}), 400

    opt = options[option_idx]
    try:
        captions = generate_captions(opt["post_text"], opt["theme"])
        return jsonify({"captions": captions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/save", methods=["POST"])
@login_required
def api_save():
    data = request.get_json(force=True)
    job_id = data.get("job_id")
    option_idx = int(data.get("option_idx", 0))
    selected_caption = data.get("caption", "")

    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    options = job.get("options", [])
    if option_idx >= len(options) or not options[option_idx]:
        return jsonify({"error": "Option not available"}), 400

    option = dict(options[option_idx])
    option["caption"] = selected_caption
    post_id = save_post_to_history(option)
    return jsonify({"success": True, "post_id": post_id})


@app.route("/img/output/<path:filepath>")
@login_required
def serve_output_image(filepath):
    base = OUTPUT_DIR.resolve()
    full = (base / filepath).resolve()
    if not str(full).startswith(str(base)):
        abort(403)
    if not full.exists():
        abort(404)
    return send_file(str(full), mimetype="image/jpeg")


@app.route("/img/asset/<path:filepath>")
@login_required
def serve_asset_image(filepath):
    base = ASSETS_DIR.resolve()
    full = (base / filepath).resolve()
    if not str(full).startswith(str(base)):
        abort(403)
    if not full.exists():
        abort(404)
    return send_file(str(full))


if __name__ == "__main__":
    print("\n  Sharp Group Content Studio")
    print("  http://localhost:5051\n")
    app.run(host="0.0.0.0", port=5051, debug=False)
