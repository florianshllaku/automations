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
    "Pije pa limit gjatë vakteve",
    "Pishina",
    "Transporti hotel-plazh-hotel",
]

BASE_DIR    = Path(__file__).parent
OUTPUT_DIR  = BASE_DIR / "output" / "turizem"
HISTORY_FILE = BASE_DIR / "history" / "turizem.json"
UPLOAD_DIR  = BASE_DIR / "uploads" / "turizem"
PASSWORD    = "ventura2026"

app = Flask(__name__, template_folder="turizem_web/templates")
app.secret_key = "vt_xK9#mL2$pQ7nR4"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── Caption generator ────────────────────────────────────────────────────────

def generate_caption(event_badge, destination, hotel_name, nights, days, price, includes_raw):
    includes_lines = [l.strip() for l in includes_raw.splitlines() if l.strip()]
    includes_str = "\n".join(f"✅ {item}" for item in includes_lines) if includes_lines else ""

    city_tag = destination.lower().replace(" ", "")

    name_of_offer = f"{event_badge} ~ {destination}" if event_badge else destination

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
    selected       = request.form.getlist("services")

    # Compute package_type for the image
    if set(selected) >= set(ALL_SERVICES):
        package_type = "PAKETA ALL INCLUSIVE"
    elif selected:
        package_type = " • ".join(selected)
    else:
        package_type = ""

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

    caption = generate_caption(event_badge, destination, hotel_name, nights, days, price, includes_raw)

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
        "caption":      caption,
        "filename":     output_filename,
    }
    history = load_history()
    history.insert(0, entry)
    save_history(history)

    return jsonify({
        "success":   True,
        "image_url": url_for("serve_output", filename=output_filename),
        "filename":  output_filename,
        "caption":   caption,
        "entry":     entry,
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
