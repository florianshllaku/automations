"""
Ventura Travel — Post Generator Web App
Run: python turizem_app.py
Open: http://localhost:5050
Password: ventura2026
"""

import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path

from flask import (Flask, jsonify, redirect, render_template,
                   request, send_from_directory, session, url_for)

ALL_SERVICES = [
    "Akomodimi",
    "Mëngjesi",
    "Dreka",
    "Darka",
    "Pije",
    "Pishina",
    "Transporti hotel-plazh-hotel",
    "Fitness",
    "Spa",
    "Jacuzzi",
    "Plazhë",
]

BASE_DIR    = Path(__file__).parent
OUTPUT_DIR  = BASE_DIR / "output" / "turizem"
HISTORY_FILE = BASE_DIR / "history" / "turizem.json"
UPLOAD_DIR  = BASE_DIR / "uploads" / "turizem"
PASSWORD    = "ventura2026"

app = Flask(__name__, template_folder="turizem_web/templates")
app.secret_key = "vt_xK9#mL2$pQ7nR4"
app.config["TEMPLATES_AUTO_RELOAD"] = True

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── Caption generator ────────────────────────────────────────────────────────

def generate_caption(event_badge, destination, hotel_name, nights, days, price, includes_raw, month=""):
    includes_lines = [l.strip() for l in includes_raw.splitlines() if l.strip()]
    includes_str = "\n".join(f"✅ {item}" for item in includes_lines) if includes_lines else ""

    city_tag = destination.lower().replace(" ", "")

    month_str = f" ({month})" if month else ""
    name_of_offer = f"{event_badge} ~ {destination}{month_str}" if event_badge else f"{destination}{month_str}"

    caption = (
        f"✨ {name_of_offer} ✨\n\n"
        f"HOTEL  {hotel_name}\n"
        f"{nights} net / {days} ditë vetëm {price}€ për person\n\n"
        f"✅Transport deri tek Hoteli🏨\n\n"
        f"Në çmim përfshihet:\n"
        f"{includes_str}\n\n"
        f"❗Verejtje: Bileta extra 20€ kthyese.\n"
        f"• Pagesa bëhet përmes llogarisë bankare apo onefour ose në zyret tona.\n\n"
        f"📍Na vizitoni:\n"
        f"• Prishtinë (te sheshi Nena Tereze, perball kafes Corner)\n\n"
        f"📞 Kontakt:\n"
        f"038 / 232 323\n"
        f"044 / 242 252 (Viber/WhatsApp)\n"
        f"049 / 242 252\n\n\n"
        f"📧 venturatravel@gmail.com\n"
        f"🌐 venturatravel.net\n\n"
        f"Ventura Travel - Gjithmonë pranë jush! ❤️\n\n"
        f"#venturatravel #{city_tag} #hotel #oferta #udhetime"
    )
    return caption


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return []


def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Fjalëkalim i gabuar. Provo përsëri."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Main ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html", history=load_history())


# ── Generate ──────────────────────────────────────────────────────────────────

@app.route("/generate", methods=["POST"])
def generate():
    if not session.get("logged_in"):
        return jsonify({"error": "Not authenticated"}), 401

    event_badge    = request.form.get("event_badge", "").strip()
    hotel_label    = request.form.get("hotel_label", "HOTEL").strip() or "HOTEL"
    hotel_name     = request.form.get("hotel_name", "").strip()
    destination    = request.form.get("destination", "").strip()
    days           = request.form.get("days", "1").strip()
    nights         = request.form.get("nights", "1").strip()
    price          = request.form.get("price", "").strip()
    month          = request.form.get("month", "").strip()
    selected       = request.form.getlist("services")

    # Compute package_type for the image (comma-separated)
    package_type = ", ".join(selected) if selected else ""

    # Compute includes for the caption
    includes_raw = "\n".join(selected)

    bg_file = request.files.get("background")
    if not bg_file or bg_file.filename == "":
        return jsonify({"error": "Imazhi i sfondit është i detyrueshëm."}), 400

    suffix     = Path(bg_file.filename).suffix.lower() or ".jpg"
    bg_path    = UPLOAD_DIR / f"bg_{uuid.uuid4().hex[:10]}{suffix}"
    bg_file.save(str(bg_path))

    post_id        = uuid.uuid4().hex[:10]
    output_filename = f"post_{post_id}.jpg"
    output_path    = OUTPUT_DIR / output_filename

    try:
        from turizem_renderer import render_post
        render_post(
            bg_path=bg_path,
            output_path=output_path,
            hotel_name=hotel_name,
            destination=destination,
            days=days,
            nights=nights,
            package_type=package_type,
            price=price,
            event_badge=event_badge,
            hotel_label=hotel_label,
        )
    except Exception as e:
        bg_path.unlink(missing_ok=True)
        return jsonify({"error": str(e)}), 500
    finally:
        bg_path.unlink(missing_ok=True)

    caption = generate_caption(event_badge, destination, hotel_name, nights, days, price, includes_raw, month)

    # Save caption as .txt alongside the image
    caption_filename = f"post_{post_id}.txt"
    caption_path = OUTPUT_DIR / caption_filename
    caption_path.write_text(caption, encoding="utf-8")

    entry = {
        "id":           post_id,
        "timestamp":    datetime.now().strftime("%d %b %Y  %H:%M"),
        "event_badge":  event_badge,
        "hotel_label":  hotel_label,
        "hotel_name":   hotel_name,
        "destination":  destination,
        "days":         days,
        "nights":       nights,
        "services":     selected,
        "package_type": package_type,
        "price":        price,
        "caption":          caption,
        "filename":         output_filename,
        "caption_filename": caption_filename,
    }
    history = load_history()
    history.insert(0, entry)
    save_history(history)

    return jsonify({
        "success":          True,
        "image_url":        url_for("serve_output", filename=output_filename),
        "filename":         output_filename,
        "caption_url":      url_for("serve_output", filename=caption_filename),
        "caption_filename": caption_filename,
        "caption":          caption,
        "entry":            entry,
    })


@app.route("/generate_carousel", methods=["POST"])
def generate_carousel():
    if not session.get("logged_in"):
        return jsonify({"error": "Not authenticated"}), 401

    event_badge = request.form.get("event_badge", "").strip()
    hotel_label = request.form.get("hotel_label", "HOTEL").strip() or "HOTEL"
    hotel_name  = request.form.get("hotel_name", "").strip()
    destination = request.form.get("destination", "").strip()
    days        = request.form.get("days", "1").strip()
    nights      = request.form.get("nights", "1").strip()
    price       = request.form.get("price", "").strip()
    date_from   = request.form.get("date_from", "").strip()
    date_to     = request.form.get("date_to", "").strip()
    month       = request.form.get("c_month", "").strip()
    season_tag  = request.form.get("season_tag", "VERA").strip() or "VERA"
    year_tag    = request.form.get("year_tag", "2026").strip() or "2026"
    selected    = request.form.getlist("c_services")

    bg_files = request.files.getlist("backgrounds")
    valid_bgs = [f for f in bg_files if f and f.filename != ""]
    if not valid_bgs:
        return jsonify({"error": "Të paktën një imazh është i detyrueshëm."}), 400

    saved_bgs = []
    for f in valid_bgs:
        suffix = Path(f.filename).suffix.lower() or ".jpg"
        bg_path = UPLOAD_DIR / f"cbg_{uuid.uuid4().hex[:8]}{suffix}"
        f.save(str(bg_path))
        saved_bgs.append(bg_path)

    post_id = uuid.uuid4().hex[:10]
    includes_raw = "\n".join(selected)
    package_type = ", ".join(selected) if selected else ""
    rendered_slides = []

    try:
        from turizem_carousel_renderer import render_carousel_cover, render_carousel_slide

        cover_filename = f"carousel_{post_id}_01.jpg"
        render_carousel_cover(
            template_name="turizem_carousel_cover_v2.html",
            bg_path=saved_bgs[0],
            output_path=OUTPUT_DIR / cover_filename,
            hotel_name=hotel_name,
            destination=destination,
            days=days,
            nights=nights,
            price=price,
            date_from=date_from,
            date_to=date_to,
            event_badge=event_badge,
            hotel_label=hotel_label,
            season_tag=season_tag,
            year_tag=year_tag,
            month=month,
            logo_variant="auto",
        )
        rendered_slides.append(cover_filename)

        for i, bg_path in enumerate(saved_bgs[1:], start=2):
            slide_filename = f"carousel_{post_id}_{i:02d}.jpg"
            render_carousel_slide(
                bg_path=bg_path,
                output_path=OUTPUT_DIR / slide_filename,
                slide_title=destination,
                slide_subtitle=f"{season_tag} {year_tag}",
                logo_variant="white",
                border_variant=2,
            )
            rendered_slides.append(slide_filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for p in saved_bgs:
            p.unlink(missing_ok=True)

    caption = generate_caption(event_badge, destination, hotel_name, nights, days, price, includes_raw)
    caption_filename = f"carousel_{post_id}.txt"
    (OUTPUT_DIR / caption_filename).write_text(caption, encoding="utf-8")

    import zipfile
    zip_filename = f"carousel_{post_id}.zip"
    zip_path = OUTPUT_DIR / zip_filename
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        for fn in rendered_slides:
            zf.write(str(OUTPUT_DIR / fn), fn)
        zf.write(str(OUTPUT_DIR / caption_filename), caption_filename)

    entry = {
        "id":               post_id,
        "type":             "carousel",
        "timestamp":        datetime.now().strftime("%d %b %Y  %H:%M"),
        "event_badge":      event_badge,
        "hotel_label":      hotel_label,
        "hotel_name":       hotel_name,
        "destination":      destination,
        "days":             days,
        "nights":           nights,
        "price":            price,
        "services":         selected,
        "package_type":     package_type,
        "slides":           rendered_slides,
        "filename":         rendered_slides[0],
        "caption":          caption,
        "caption_filename": caption_filename,
        "zip_filename":     zip_filename,
    }
    history = load_history()
    history.insert(0, entry)
    save_history(history)

    return jsonify({
        "success":          True,
        "slides":           [{"url": url_for("serve_output", filename=fn), "filename": fn} for fn in rendered_slides],
        "caption":          caption,
        "caption_url":      url_for("serve_output", filename=caption_filename),
        "caption_filename": caption_filename,
        "zip_url":          url_for("serve_output", filename=zip_filename),
        "zip_filename":     zip_filename,
        "entry":            entry,
    })


# ── Generate Story ────────────────────────────────────────────────────────────

@app.route("/generate_story", methods=["POST"])
def generate_story():
    if not session.get("logged_in"):
        return jsonify({"error": "Not authenticated"}), 401

    event_badge   = request.form.get("s_event_badge", "").strip()
    destination   = request.form.get("s_destination", "").strip()
    price         = request.form.get("s_price", "").strip()
    selected      = request.form.getlist("s_services")
    template_name = request.form.get("s_template", "turizem_story.html").strip()
    # whitelist — only allow known story templates
    allowed = {"turizem_story.html", "turizem_story_v2.html"}
    if template_name not in allowed:
        template_name = "turizem_story.html"

    includes_text = " • ".join(s.upper() for s in selected) if selected else ""
    includes_raw  = "\n".join(selected)

    bg_file = request.files.get("s_background")
    if not bg_file or bg_file.filename == "":
        return jsonify({"error": "Imazhi i sfondit është i detyrueshëm."}), 400

    suffix  = Path(bg_file.filename).suffix.lower() or ".jpg"
    bg_path = UPLOAD_DIR / f"sbg_{uuid.uuid4().hex[:10]}{suffix}"
    bg_file.save(str(bg_path))

    post_id  = uuid.uuid4().hex[:10]
    out_fn   = f"story_{post_id}.jpg"
    out_path = OUTPUT_DIR / out_fn

    try:
        from turizem_story_renderer import render_story
        render_story(
            bg_path       = bg_path,
            output_path   = out_path,
            destination   = destination,
            price         = price,
            event_badge   = event_badge,
            includes_text = includes_text,
            template_name = template_name,
        )
    except Exception as e:
        bg_path.unlink(missing_ok=True)
        return jsonify({"error": str(e)}), 500
    finally:
        bg_path.unlink(missing_ok=True)

    caption = generate_caption(
        event_badge  = event_badge,
        destination  = destination,
        hotel_name   = destination,
        nights       = "1",
        days         = "1",
        price        = price,
        includes_raw = includes_raw,
    )

    caption_fn   = f"story_{post_id}.txt"
    caption_path = OUTPUT_DIR / caption_fn
    caption_path.write_text(caption, encoding="utf-8")

    entry = {
        "id":               post_id,
        "type":             "story",
        "template":         template_name,
        "timestamp":        datetime.now().strftime("%d %b %Y  %H:%M"),
        "event_badge":      event_badge,
        "destination":      destination,
        "price":            price,
        "services":         selected,
        "filename":         out_fn,
        "caption":          caption,
        "caption_filename": caption_fn,
    }
    history = load_history()
    history.insert(0, entry)
    save_history(history)

    return jsonify({
        "success":          True,
        "image_url":        url_for("serve_output", filename=out_fn),
        "filename":         out_fn,
        "caption_url":      url_for("serve_output", filename=caption_fn),
        "caption_filename": caption_fn,
        "caption":          caption,
        "entry":            entry,
    })


# ── Static output ─────────────────────────────────────────────────────────────

@app.route("/output/<filename>")
def serve_output(filename):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return send_from_directory(str(OUTPUT_DIR), filename)


if __name__ == "__main__":
    print("\n  Ventura Travel Generator")
    print("  http://localhost:5050")
    print(f"  Password: {PASSWORD}\n")
    app.run(debug=False, port=5050)
