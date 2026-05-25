"""
Content Studio — Unified Web App
Single login, multi-business (Sharp Group + Ventura Travel)
Run: python main_app.py  |  Port: 5000
"""
from __future__ import annotations

import json
import os
import re
import threading
import uuid
import zipfile
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, jsonify, redirect, render_template,
    request, send_file, send_from_directory, session, url_for,
)
from openai import OpenAI
from PIL import Image
from google import genai as google_genai

from config import (
    ASSETS_DIR, GEMINI_API_KEY,
    OPENAI_API_KEY, OPENAI_MODEL, OUTPUT_DIR,
)
from content_brain import COMPOSITION_RULES, generate_content_brief, pick_reference_images
from fal_image_gen import generate_gpt_no_ref
from html_renderer import render_post as sg_render_post
from database import (
    init_db, verify_login, get_user_by_id,
    get_posts, get_stats, create_post, save_caption,
)

ALL_VENTURA_SERVICES = [
    "Akomodimi", "Mëngjesi", "Dreka", "Darka", "Pije", "Pishina",
    "Transporti hotel-plazh-hotel", "Fitness", "Spa", "Jacuzzi", "Plazhë",
]

BASE_DIR   = Path(__file__).parent
VT_OUTPUT  = OUTPUT_DIR / "turizem"
VT_UPLOAD  = BASE_DIR / "uploads" / "turizem"
SG_OUTPUT  = OUTPUT_DIR / "sharp_group"

VT_OUTPUT.mkdir(parents=True, exist_ok=True)
VT_UPLOAD.mkdir(parents=True, exist_ok=True)
SG_OUTPUT.mkdir(parents=True, exist_ok=True)


# ── App Setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__, template_folder="templates/main")
app.secret_key = os.getenv("SECRET_KEY", "studio-unified-2025-secret-key")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL_ID = "gemini-3-flash-preview"

# In-memory job store (Sharp Group async generation)
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


_THEMES = {
    "sharp_group": {"color": "#123abc", "dim": "rgba(18,58,188,0.07)", "glow": "rgba(18,58,188,0.15)"},
    "ventura":     {"color": "#123abc", "dim": "rgba(18,58,188,0.07)", "glow": "rgba(18,58,188,0.15)"},
}


def get_biz() -> dict:
    """Return the current user's profile dict for templates."""
    user_id = session.get("user_id")
    if not user_id:
        return {}
    user = get_user_by_id(user_id)
    if not user:
        return {}
    theme = _THEMES.get(user["username"], {"color": "#ffffff", "dim": "rgba(255,255,255,0.1)", "glow": "rgba(255,255,255,0.2)"})
    return {
        "id":    user["username"],
        "name":  user["business_name"],
        "sub":   "Content Studio" if user["username"] == "sharp_group" else "Post Generator",
        "color": theme["color"],
        "dim":   theme["dim"],
        "glow":  theme["glow"],
    }


app.jinja_env.globals["get_biz"] = get_biz


def _current_username() -> str:
    """Return the logged-in user's username, or empty string."""
    uid = session.get("user_id")
    if not uid:
        return ""
    user = get_user_by_id(uid)
    return user["username"] if user else ""


# Ensure DB tables exist on startup
init_db()


# ── Image URL helpers ─────────────────────────────────────────────────────────

def image_url_for_sg(image_path: str) -> str:
    if not image_path:
        return ""
    p = Path(image_path)
    if p.is_absolute():
        try:
            rel = str(p.relative_to(OUTPUT_DIR)).replace("\\", "/")
            return url_for("serve_output", filepath=rel)
        except ValueError:
            pass
        try:
            rel = str(p.relative_to(ASSETS_DIR)).replace("\\", "/")
            return url_for("serve_asset", filepath=rel)
        except ValueError:
            return ""
    if image_path.startswith("uploads/"):
        filename = image_path[len("uploads/"):]
        return url_for("serve_asset", filepath=f"sharp_group/uploaded_posts/{filename}")
    return url_for("serve_output", filepath=image_path)


app.jinja_env.globals["image_url_for_sg"] = image_url_for_sg


def _resolve_image_path(post_data: dict) -> str:
    """Convert absolute final_path to a path relative to OUTPUT_DIR."""
    abs_final = post_data.get("final_path", "")
    if not abs_final:
        return post_data.get("image_path", "")
    try:
        return str(Path(abs_final).relative_to(OUTPUT_DIR)).replace("\\", "/")
    except ValueError:
        return abs_final


# ── Sharp Group Generation ────────────────────────────────────────────────────

def sg_brief_from_topic(topic: str) -> dict:
    brand = (ASSETS_DIR / "sharp_group" / "BRAND.md").read_text(encoding="utf-8")
    resp = openai_client.chat.completions.create(
        model=OPENAI_MODEL, max_tokens=800,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are an expert Instagram content strategist for Sharp Group, a digital marketing agency. Return valid JSON only."},
            {"role": "user", "content": (
                f"Follow this brand guide (especially section 15 — Copywriting Direction):\n---\n{brand}\n---\n"
                f'User topic: "{topic}"\n\n'
                "Create a Sharp Group Instagram post.\n"
                "Rules:\n"
                '- post_text: Albanian, max 15 words, goes ON the image. Wrap 1-3 key words in <span class="hl"> </span>. '
                "Use \\n only to separate distinct thought units (max 1 newline). NEVER use <br>.\n"
                '- caption: Albanian, 60-120 words, emotionally intelligent. Include hashtags. End with "Behu me i mprehte me ne."\n'
                "- theme: short English description\n"
                "- post_type: tip|educational|promotional|trend\n\n"
                'Return: {"post_type":"...","theme":"...","post_text":"...","caption":"..."}'
            )},
        ],
    )
    return json.loads(resp.choices[0].message.content)


def sg_brief_from_text(text: str) -> dict:
    brand = (ASSETS_DIR / "sharp_group" / "BRAND.md").read_text(encoding="utf-8")
    resp = openai_client.chat.completions.create(
        model=OPENAI_MODEL, max_tokens=700,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are an expert Instagram content strategist for Sharp Group. Return valid JSON only."},
            {"role": "user", "content": (
                f"Brand guide (section 15):\n---\n{brand}\n---\n"
                f'User text: "{text}"\n\n'
                "Use this as post_text. Improve to match section 15 style (max 15 words, Albanian). "
                'Wrap 1-3 key words in <span class="hl"> </span>.\n'
                "Generate:\n"
                "- theme: short English description\n"
                '- caption: Albanian (60-120 words). Include hashtags. End with "Behu me i mprehte me ne."\n'
                "- post_type: tip|educational|promotional|trend\n\n"
                'Return: {"post_type":"...","theme":"...","post_text":"...","caption":"..."}'
            )},
        ],
    )
    return json.loads(resp.choices[0].message.content)


def sg_generate_prompt(theme: str, post_text: str, ref_images: list, layout: str, style: str) -> str:
    brand = (ASSETS_DIR / "sharp_group" / "BRAND.md").read_text(encoding="utf-8")
    pil_images = [Image.open(p) for p in ref_images]
    style_instructions = {
        "3d_graphics": (
            "STYLE REQUIREMENT: Use Style A — premium 3D abstract/geometric/symbolic composition. "
            "No people, no photographs. Symbolic objects (chess pieces, targets, arrows, graphs, funnels) "
            "inside rich visual scenes with geometric depth, layered elements, repeating patterns. "
            "Follow section 7 and 16 of the brand guide exactly."
        ),
        "real_person": (
            "STYLE REQUIREMENT: Use Style B — photorealistic person in business/digital context. "
            "Studio quality, seamless off-white background. Full figure visible in bottom 40-50% of frame. "
            "Smart casual or professional clothing in neutral/dark tones. Orange accent details. "
            "MANDATORY: If phone/tablet/laptop visible, screen MUST show real social media app icons. "
            "Follow section 16 of the brand guide exactly."
        ),
    }
    comp_rule = COMPOSITION_RULES.get(layout, COMPOSITION_RULES["default"])
    prompt_text = (
        "You are a creative director for a digital marketing agency. "
        "Write one Fal.ai image generation prompt strictly grounded in the brand guide below.\n\n"
        f"---\nBRAND GUIDE:\n{brand}\n---\n\n"
        f'Post theme: "{theme}"\n'
        f'Text that will be placed on the image: "{post_text}"\n\n'
        f"{style_instructions.get(style, style_instructions['3d_graphics'])}\n\n"
        "Non-negotiable rules:\n"
        "- Absolutely NO text, NO letters, NO words anywhere in the image\n"
        "- Orange (#FF680B) as dominant accent on key objects\n"
        "- Black for depth and contrast\n"
        "- Vertical composition 4:5 ratio (1080x1350px)\n"
        "- Feel: modern, premium, minimal, professional\n"
        f"{comp_rule}\n\n"
        'Respond with ONLY valid JSON:\n{"visual_concept":"one sentence","prompt":"full detailed Fal.ai prompt"}'
    )
    contents = [prompt_text] + pil_images
    for attempt in range(3):
        try:
            resp = gemini_client.models.generate_content(model=GEMINI_MODEL_ID, contents=contents)
            raw = resp.text.strip()
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                raw = m.group(0)
            data = json.loads(raw)
            print(f"  [prompt] concept: {data['visual_concept']}")
            return data["prompt"]
        except Exception as e:
            print(f"  Gemini attempt {attempt+1}/3 failed: {e}")
    raise RuntimeError("Gemini failed to return valid prompt after 3 attempts")


def sg_generate_captions(post_text: str, theme: str) -> list[str]:
    brand = (ASSETS_DIR / "sharp_group" / "BRAND.md").read_text(encoding="utf-8")
    resp = openai_client.chat.completions.create(
        model=OPENAI_MODEL, max_tokens=1400,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a social media strategist for Sharp Group. Return valid JSON only."},
            {"role": "user", "content": (
                f"Brand guide (section 15):\n---\n{brand}\n---\n\n"
                f"Post theme: {theme}\nText on image: {post_text}\n\n"
                "Generate 3 DISTINCT Instagram captions in Albanian.\nEach caption must:\n"
                "- Psychologically sharp, observational, emotionally intelligent (section 15 style)\n"
                "- 60-120 words\n"
                "- 8-12 hashtags at end\n"
                '- End with "Behu me i mprehte me ne."\n'
                "- Completely different angle from the other 2\n\n"
                'Return: {"captions":["caption1","caption2","caption3"]}'
            )},
        ],
    )
    return json.loads(resp.choices[0].message.content)["captions"]


def _sg_run_job(job_id: str, mode: str, user_input: str, bg_color: str, cta_text: str) -> None:
    with jobs_lock:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["progress"] = "Building content brief..."
    try:
        if mode == "ai":
            brief = generate_content_brief("sharp_group")
        elif mode == "topic":
            brief = sg_brief_from_topic(user_input)
        else:
            brief = sg_brief_from_text(user_input)

        theme     = brief["theme"]
        post_text = brief["post_text"]
        caption   = brief.get("caption", "")
        post_type = brief.get("post_type", "promotional")

        with jobs_lock:
            jobs[job_id]["progress"] = "Picking reference images..."
        ref_images = pick_reference_images("sharp_group", 3)

        layout   = "orange" if bg_color == "orange" else "default"
        template = layout

        option_configs = [
            {"layout": layout, "style": "3d_graphics", "template": template, "label": "3D Graphic — V1"},
            {"layout": layout, "style": "real_person",  "template": template, "label": "Real Person"},
            {"layout": layout, "style": "3d_graphics",  "template": template, "label": "3D Graphic — V2"},
        ]

        SG_OUTPUT.mkdir(parents=True, exist_ok=True)
        options: list[dict | None]      = [None, None, None]
        option_errors: list[str | None] = [None, None, None]

        def generate_one(idx: int, cfg: dict) -> None:
            try:
                with jobs_lock:
                    jobs[job_id]["progress"] = f"Generating option {idx+1}/3 ({cfg['label']})..."
                fal_prompt = sg_generate_prompt(theme, post_text, ref_images, cfg["layout"], cfg["style"])
                bg_path    = generate_gpt_no_ref(fal_prompt, SG_OUTPUT)
                final_path = SG_OUTPUT / f"ui_{job_id}_opt{idx}_final.jpg"
                sg_render_post(
                    bg_path, post_text, final_path,
                    cta_text=cta_text if cta_text else None,
                    template=cfg["template"],
                )
                options[idx] = {
                    "bg_path":    str(bg_path),
                    "final_path": str(final_path),
                    "post_text":  post_text,
                    "theme":      theme,
                    "caption":    caption,
                    "post_type":  post_type,
                    "template":   cfg["template"],
                    "style":      cfg["style"],
                    "label":      cfg["label"],
                    "bg_color":   bg_color,
                    "cta_text":   cta_text,
                }
            except Exception as e:
                option_errors[idx] = str(e)
                print(f"  Option {idx+1} failed: {e}")

        threads = [
            threading.Thread(target=generate_one, args=(i, cfg), daemon=True)
            for i, cfg in enumerate(option_configs)
        ]
        for t in threads: t.start()
        for t in threads: t.join()

        with jobs_lock:
            jobs[job_id]["status"]   = "done"
            jobs[job_id]["options"]  = options
            jobs[job_id]["errors"]   = option_errors
            jobs[job_id]["progress"] = "Done"

    except Exception as e:
        with jobs_lock:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"]  = str(e)
        print(f"  Job {job_id} failed: {e}")


# ── Ventura Caption ───────────────────────────────────────────────────────────

def vt_generate_caption(event_badge, destination, hotel_name, nights, days, price, includes_raw, month=""):
    includes_lines = [l.strip() for l in includes_raw.splitlines() if l.strip()]
    includes_str   = "\n".join(f"✅ {item}" for item in includes_lines) if includes_lines else ""
    city_tag       = destination.lower().replace(" ", "")
    month_str      = f" ({month})" if month else ""
    name           = f"{event_badge} ~ {destination}{month_str}" if event_badge else f"{destination}{month_str}"
    return (
        f"✨ {name} ✨\n\n"
        f"HOTEL  {hotel_name}\n"
        f"{nights} net / {days} ditë vetëm {price}€ për person\n\n"
        f"✅Transport deri tek Hoteli🏨\n\n"
        f"Në çmim përfshihet:\n{includes_str}\n\n"
        f"❗Verejtje: Bileta extra 20€ kthyese.\n"
        f"• Pagesa bëhet përmes llogarisë bankare apo onefour ose në zyret tona.\n\n"
        f"📍Na vizitoni:\n• Prishtinë (te sheshi Nena Tereze, perball kafes Corner)\n\n"
        f"📞 Kontakt:\n038 / 232 323\n044 / 242 252 (Viber/WhatsApp)\n049 / 242 252\n\n\n"
        f"📧 venturatravel@gmail.com\n🌐 venturatravel.net\n\n"
        f"Ventura Travel - Gjithmonë pranë jush! ❤️\n\n"
        f"#venturatravel #{city_tag} #hotel #oferta #udhetime"
    )


# ── Core Routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = verify_login(username, password)
        if user:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        error = "Kredencialet e gabuara. Provo perseri."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    biz   = get_biz()
    posts = get_posts(session["user_id"])
    stats = get_stats(session["user_id"])
    return render_template("dashboard.html", biz=biz, posts=posts, stats=stats, active="dashboard")


@app.route("/create")
@login_required
def create():
    biz = get_biz()
    tab = request.args.get("tab", "normal")
    return render_template("create.html", biz=biz, tab=tab, active="create",
                           services=ALL_VENTURA_SERVICES)


@app.route("/scheduling")
@login_required
def scheduling():
    biz = get_biz()
    return render_template("scheduling.html", biz=biz, active="scheduling")


@app.route("/history")
@login_required
def history():
    biz   = get_biz()
    posts = get_posts(session["user_id"])
    return render_template("history.html", biz=biz, posts=posts, active="history")


@app.route("/analytics")
@login_required
def analytics():
    biz   = get_biz()
    posts = get_posts(session["user_id"])
    stats = get_stats(session["user_id"])
    return render_template("analytics.html", biz=biz, posts=posts, stats=stats, active="analytics")


@app.route("/profile")
@login_required
def profile():
    biz = get_biz()
    return render_template("profile.html", biz=biz, active="profile")


# ── Sharp Group API ───────────────────────────────────────────────────────────

@app.route("/api/sg/generate", methods=["POST"])
@login_required
def sg_api_generate():
    if _current_username() != "sharp_group":
        abort(403)
    data       = request.get_json(force=True)
    mode       = data.get("mode", "ai")
    user_input = data.get("input", "").strip()
    bg_color   = data.get("bg_color", "white")
    cta_text   = data.get("cta_text", "").strip()

    if mode in ("topic", "text") and not user_input:
        return jsonify({"error": "Input required for this mode"}), 400
    if bg_color not in ("white", "orange"):
        bg_color = "white"

    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {
            "status": "pending", "progress": "Queued...",
            "options": None, "errors": None, "error": None,
        }
    threading.Thread(
        target=_sg_run_job,
        args=(job_id, mode, user_input, bg_color, cta_text),
        daemon=True,
    ).start()
    return jsonify({"job_id": job_id})


@app.route("/api/sg/status/<job_id>")
@login_required
def sg_api_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "status":   job["status"],
        "progress": job.get("progress", ""),
        "error":    job.get("error"),
    })


@app.route("/select/<job_id>")
@login_required
def select_post(job_id):
    if _current_username() != "sharp_group":
        abort(403)
    with jobs_lock:
        job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return redirect(url_for("create"))
    options     = job.get("options", [])
    option_urls = []
    for opt in options:
        if opt:
            try:
                rel = str(Path(opt["final_path"]).relative_to(OUTPUT_DIR)).replace("\\", "/")
                img_url = url_for("serve_output", filepath=rel)
            except ValueError:
                img_url = ""
            option_urls.append(img_url)
        else:
            option_urls.append(None)
    biz = get_biz()
    return render_template("select.html", job_id=job_id, options=options,
                           option_urls=option_urls, biz=biz, active="create")


@app.route("/caption/<job_id>/<int:option_idx>")
@login_required
def caption_page(job_id, option_idx):
    if _current_username() != "sharp_group":
        abort(403)
    with jobs_lock:
        job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return redirect(url_for("dashboard"))
    options = job.get("options", [])
    if option_idx >= len(options) or not options[option_idx]:
        return redirect(url_for("select_post", job_id=job_id))
    option = options[option_idx]
    try:
        rel     = str(Path(option["final_path"]).relative_to(OUTPUT_DIR)).replace("\\", "/")
        img_url = url_for("serve_output", filepath=rel)
    except ValueError:
        img_url = ""
    biz = get_biz()
    return render_template("caption.html", job_id=job_id, option_idx=option_idx,
                           option=option, img_url=img_url, biz=biz, active="create")


@app.route("/api/sg/captions", methods=["POST"])
@login_required
def sg_api_captions():
    if _current_username() != "sharp_group":
        abort(403)
    data       = request.get_json(force=True)
    job_id     = data.get("job_id")
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
        captions = sg_generate_captions(opt["post_text"], opt["theme"])
        return jsonify({"captions": captions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/sg/save", methods=["POST"])
@login_required
def sg_api_save():
    if _current_username() != "sharp_group":
        abort(403)
    data           = request.get_json(force=True)
    job_id         = data.get("job_id")
    option_idx     = int(data.get("option_idx", 0))
    sel_caption    = data.get("caption", "")
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    options = job.get("options", [])
    if option_idx >= len(options) or not options[option_idx]:
        return jsonify({"error": "Option not available"}), 400
    option            = dict(options[option_idx])
    option["caption"] = sel_caption
    image_path        = _resolve_image_path(option)

    post_id = create_post(
        user_id=session["user_id"],
        post_type="normal",
        filename=image_path,
    )
    if sel_caption:
        save_caption(post_id, session["user_id"], sel_caption)
    return jsonify({"success": True, "post_id": post_id})


# ── Ventura Routes ────────────────────────────────────────────────────────────

@app.route("/api/vt/generate", methods=["POST"])
@login_required
def vt_generate():
    if _current_username() != "ventura":
        abort(403)
    event_badge  = request.form.get("event_badge", "").strip()
    hotel_label  = request.form.get("hotel_label", "HOTEL").strip() or "HOTEL"
    hotel_name   = request.form.get("hotel_name", "").strip()
    destination  = request.form.get("destination", "").strip()
    days         = request.form.get("days", "1").strip()
    nights       = request.form.get("nights", "1").strip()
    price        = request.form.get("price", "").strip()
    month        = request.form.get("month", "").strip()
    selected     = request.form.getlist("services")
    package_type = ", ".join(selected) if selected else ""
    includes_raw = "\n".join(selected)

    bg_file = request.files.get("background")
    if not bg_file or bg_file.filename == "":
        return jsonify({"error": "Imazhi i sfondit është i detyrueshëm."}), 400

    suffix  = Path(bg_file.filename).suffix.lower() or ".jpg"
    bg_path = VT_UPLOAD / f"bg_{uuid.uuid4().hex[:10]}{suffix}"
    bg_file.save(str(bg_path))

    post_id = uuid.uuid4().hex[:10]
    out_fn  = f"post_{post_id}.jpg"
    out_path = VT_OUTPUT / out_fn

    try:
        from turizem_renderer import render_post as vt_render
        vt_render(
            bg_path=bg_path, output_path=out_path,
            hotel_name=hotel_name, destination=destination,
            days=days, nights=nights, package_type=package_type, price=price,
            event_badge=event_badge, hotel_label=hotel_label,
        )
    except Exception as e:
        bg_path.unlink(missing_ok=True)
        return jsonify({"error": str(e)}), 500
    finally:
        bg_path.unlink(missing_ok=True)

    caption    = vt_generate_caption(event_badge, destination, hotel_name, nights, days, price, includes_raw, month)
    caption_fn = f"post_{post_id}.txt"
    (VT_OUTPUT / caption_fn).write_text(caption, encoding="utf-8")

    entry = {
        "id": post_id, "type": "post",
        "timestamp": datetime.now().strftime("%d %b %Y  %H:%M"),
        "event_badge": event_badge, "hotel_label": hotel_label,
        "hotel_name": hotel_name, "destination": destination,
        "days": days, "nights": nights, "services": selected,
        "package_type": package_type, "price": price,
        "caption": caption, "filename": out_fn, "caption_filename": caption_fn,
    }
    db_post_id = create_post(
        user_id=session["user_id"],
        post_type="normal",
        filename=out_fn,
    )
    if caption:
        save_caption(db_post_id, session["user_id"], caption)

    return jsonify({
        "success": True,
        "image_url":        url_for("serve_vt_output", filename=out_fn),
        "filename":         out_fn,
        "caption_url":      url_for("serve_vt_output", filename=caption_fn),
        "caption_filename": caption_fn,
        "caption":          caption,
        "entry":            entry,
    })


@app.route("/api/vt/generate_carousel", methods=["POST"])
@login_required
def vt_generate_carousel():
    if _current_username() != "ventura":
        abort(403)
    event_badge  = request.form.get("event_badge", "").strip()
    hotel_label  = request.form.get("hotel_label", "HOTEL").strip() or "HOTEL"
    hotel_name   = request.form.get("hotel_name", "").strip()
    destination  = request.form.get("destination", "").strip()
    days         = request.form.get("days", "1").strip()
    nights       = request.form.get("nights", "1").strip()
    price        = request.form.get("price", "").strip()
    date_from    = request.form.get("date_from", "").strip()
    date_to      = request.form.get("date_to", "").strip()
    month        = request.form.get("c_month", "").strip()
    season_tag   = request.form.get("season_tag", "VERA").strip() or "VERA"
    year_tag     = request.form.get("year_tag", "2026").strip() or "2026"
    selected     = request.form.getlist("c_services")
    includes_raw = "\n".join(selected)
    package_type = ", ".join(selected) if selected else ""

    bg_files  = request.files.getlist("backgrounds")
    valid_bgs = [f for f in bg_files if f and f.filename != ""]
    if not valid_bgs:
        return jsonify({"error": "Të paktën një imazh është i detyrueshëm."}), 400

    saved_bgs = []
    for f in valid_bgs:
        suffix = Path(f.filename).suffix.lower() or ".jpg"
        bp     = VT_UPLOAD / f"cbg_{uuid.uuid4().hex[:8]}{suffix}"
        f.save(str(bp))
        saved_bgs.append(bp)

    post_id        = uuid.uuid4().hex[:10]
    rendered_slides = []

    try:
        from turizem_carousel_renderer import render_carousel_cover, render_carousel_slide
        cover_fn = f"carousel_{post_id}_01.jpg"
        render_carousel_cover(
            template_name="turizem_carousel_cover_v2.html",
            bg_path=saved_bgs[0], output_path=VT_OUTPUT / cover_fn,
            hotel_name=hotel_name, destination=destination,
            days=days, nights=nights, price=price,
            date_from=date_from, date_to=date_to,
            event_badge=event_badge, hotel_label=hotel_label,
            season_tag=season_tag, year_tag=year_tag, month=month,
            logo_variant="auto",
        )
        rendered_slides.append(cover_fn)
        for i, bp in enumerate(saved_bgs[1:], start=2):
            slide_fn = f"carousel_{post_id}_{i:02d}.jpg"
            render_carousel_slide(
                bg_path=bp, output_path=VT_OUTPUT / slide_fn,
                slide_title=destination,
                slide_subtitle=f"{season_tag} {year_tag}",
                logo_variant="white", border_variant=2,
            )
            rendered_slides.append(slide_fn)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for p in saved_bgs:
            p.unlink(missing_ok=True)

    caption    = vt_generate_caption(event_badge, destination, hotel_name, nights, days, price, includes_raw)
    caption_fn = f"carousel_{post_id}.txt"
    (VT_OUTPUT / caption_fn).write_text(caption, encoding="utf-8")

    zip_fn = f"carousel_{post_id}.zip"
    with zipfile.ZipFile(str(VT_OUTPUT / zip_fn), "w") as zf:
        for fn in rendered_slides:
            zf.write(str(VT_OUTPUT / fn), fn)
        zf.write(str(VT_OUTPUT / caption_fn), caption_fn)

    entry = {
        "id": post_id, "type": "carousel",
        "timestamp": datetime.now().strftime("%d %b %Y  %H:%M"),
        "event_badge": event_badge, "hotel_label": hotel_label,
        "hotel_name": hotel_name, "destination": destination,
        "days": days, "nights": nights, "price": price,
        "services": selected, "package_type": package_type,
        "slides": rendered_slides,
        "filename": rendered_slides[0] if rendered_slides else "",
        "caption": caption, "caption_filename": caption_fn, "zip_filename": zip_fn,
    }
    db_post_id = create_post(
        user_id=session["user_id"],
        post_type="carousel",
        filename=rendered_slides[0] if rendered_slides else "",
        extra_files=rendered_slides[1:],
    )
    if caption:
        save_caption(db_post_id, session["user_id"], caption)

    return jsonify({
        "success": True,
        "slides": [{"url": url_for("serve_vt_output", filename=fn), "filename": fn} for fn in rendered_slides],
        "caption": caption,
        "caption_url":      url_for("serve_vt_output", filename=caption_fn),
        "caption_filename": caption_fn,
        "zip_url":          url_for("serve_vt_output", filename=zip_fn),
        "zip_filename":     zip_fn,
        "entry":            entry,
    })


@app.route("/api/vt/generate_story", methods=["POST"])
@login_required
def vt_generate_story():
    if _current_username() != "ventura":
        abort(403)
    event_badge   = request.form.get("s_event_badge", "").strip()
    destination   = request.form.get("s_destination", "").strip()
    price         = request.form.get("s_price", "").strip()
    selected      = request.form.getlist("s_services")
    template_name = request.form.get("s_template", "turizem_story.html").strip()
    if template_name not in {"turizem_story.html", "turizem_story_v2.html"}:
        template_name = "turizem_story.html"
    includes_text = " • ".join(s.upper() for s in selected) if selected else ""
    includes_raw  = "\n".join(selected)

    bg_file = request.files.get("s_background")
    if not bg_file or bg_file.filename == "":
        return jsonify({"error": "Imazhi i sfondit është i detyrueshëm."}), 400

    suffix  = Path(bg_file.filename).suffix.lower() or ".jpg"
    bg_path = VT_UPLOAD / f"sbg_{uuid.uuid4().hex[:10]}{suffix}"
    bg_file.save(str(bg_path))

    post_id  = uuid.uuid4().hex[:10]
    out_fn   = f"story_{post_id}.jpg"
    out_path = VT_OUTPUT / out_fn

    try:
        from turizem_story_renderer import render_story
        render_story(
            bg_path=bg_path, output_path=out_path,
            destination=destination, price=price,
            event_badge=event_badge, includes_text=includes_text,
            template_name=template_name,
        )
    except Exception as e:
        bg_path.unlink(missing_ok=True)
        return jsonify({"error": str(e)}), 500
    finally:
        bg_path.unlink(missing_ok=True)

    entry = {
        "id": post_id, "type": "story", "template": template_name,
        "timestamp": datetime.now().strftime("%d %b %Y  %H:%M"),
        "destination": destination, "price": price,
        "services": selected, "filename": out_fn,
    }
    db_post_id = create_post(
        user_id=session["user_id"],
        post_type="story",
        filename=out_fn,
    )

    return jsonify({
        "success":   True,
        "image_url": url_for("serve_vt_output", filename=out_fn),
        "filename":  out_fn,
        "entry":     entry,
    })


# ── Static File Serving ───────────────────────────────────────────────────────

@app.route("/img/output/<path:filepath>")
@login_required
def serve_output(filepath):
    base = OUTPUT_DIR.resolve()
    full = (base / filepath).resolve()
    if not str(full).startswith(str(base)):
        abort(403)
    if not full.exists():
        abort(404)
    return send_file(str(full), mimetype="image/jpeg")


@app.route("/img/asset/<path:filepath>")
@login_required
def serve_asset(filepath):
    base = ASSETS_DIR.resolve()
    full = (base / filepath).resolve()
    if not str(full).startswith(str(base)):
        abort(403)
    if not full.exists():
        abort(404)
    return send_file(str(full))


@app.route("/vt/output/<filename>")
@login_required
def serve_vt_output(filename):
    return send_from_directory(str(VT_OUTPUT), filename)


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  Content Studio - Unified")
    print("  -------------------------")
    print("  http://localhost:5000")
    print("  Businesses: sharp_group | ventura")
    print("  -------------------------\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
