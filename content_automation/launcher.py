"""
Content Studio Launcher
Run: python launcher.py
Open: http://localhost:5000  → choose Sharp Group or Ventura Travel
"""

import threading
from flask import Flask, render_template_string
from werkzeug.serving import make_server

# ── Import both apps ──────────────────────────────────────────────────────────

from web_app import app as sharp_app          # port 5051
from turizem_app import app as turizem_app    # port 5050

# ── Landing page ──────────────────────────────────────────────────────────────

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Content Studio</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #0d0d0d;
    font-family: 'Segoe UI', system-ui, sans-serif;
  }

  .wrap {
    text-align: center;
  }

  .title {
    color: #f0f0f0;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 48px;
    opacity: 0.45;
  }

  .cards {
    display: flex;
    gap: 24px;
  }

  .card {
    display: block;
    text-decoration: none;
    width: 260px;
    padding: 40px 32px 36px;
    border-radius: 16px;
    background: #161616;
    border: 1px solid #242424;
    transition: border-color 0.2s, transform 0.2s;
    cursor: pointer;
  }

  .card:hover {
    transform: translateY(-4px);
  }

  .card.sharp:hover  { border-color: #FF680B; }
  .card.ventura:hover { border-color: #00b4d8; }

  .card .icon {
    font-size: 40px;
    margin-bottom: 20px;
  }

  .card .name {
    font-size: 18px;
    font-weight: 700;
    color: #f0f0f0;
    margin-bottom: 8px;
  }

  .card .sub {
    font-size: 12px;
    color: #555;
    letter-spacing: 0.04em;
  }

  .card.sharp  .name { color: #FF680B; }
  .card.ventura .name { color: #00b4d8; }

  .port {
    margin-top: 14px;
    font-size: 11px;
    color: #333;
    letter-spacing: 0.06em;
  }
</style>
</head>
<body>
<div class="wrap">
  <p class="title">Content Studio</p>
  <div class="cards">

    <a class="card sharp" href="http://localhost:5051" target="_blank">
      <div class="icon">⚡</div>
      <div class="name">Sharp Group</div>
      <div class="sub">AI Content · Instagram</div>
      <div class="port">localhost:5051</div>
    </a>

    <a class="card ventura" href="http://localhost:5050" target="_blank">
      <div class="icon">✈️</div>
      <div class="name">Ventura Travel</div>
      <div class="sub">Post Generator · Turizem</div>
      <div class="port">localhost:5050</div>
    </a>

  </div>
</div>
</body>
</html>"""

launcher = Flask(__name__)

@launcher.route("/")
def index():
    return render_template_string(LANDING_HTML)


# ── App runners ───────────────────────────────────────────────────────────────

def run_app(app, port, name):
    print(f"  [{name}] → http://localhost:{port}")
    srv = make_server("0.0.0.0", port, app)
    srv.serve_forever()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  Content Studio Launcher")
    print("  ─────────────────────────────────")

    threading.Thread(
        target=run_app, args=(sharp_app, 5051, "Sharp Group"), daemon=True
    ).start()

    threading.Thread(
        target=run_app, args=(turizem_app, 5050, "Ventura Travel"), daemon=True
    ).start()

    print("  Launcher      → http://localhost:5000")
    print("  ─────────────────────────────────\n")

    launcher.run(host="0.0.0.0", port=5000, debug=False)
