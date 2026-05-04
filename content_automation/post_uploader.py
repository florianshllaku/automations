"""
Sharp Group — Post History Uploader
Run: py post_uploader.py
Then open: http://localhost:5050
"""

import os
import json
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

HANDLE = "sharp_group"
HISTORY_PATH = f"history/{HANDLE}.json"
UPLOAD_FOLDER = f"assets/{HANDLE}/uploaded_posts"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_post_type(headline, body_text, caption):
    text = f"{headline} {body_text} {caption}".lower()
    if any(w in text for w in ["result", "rritëm", "rritje", "growth", "case", "klient", "client", "achieved", "arritëm", "nga 0", "from 0"]):
        return "case_study"
    if any(w in text for w in ["testimonial", "tha", "said", "review", "⭐", "★", '"', "faleminderit", "thank"]):
        return "testimonial"
    if any(w in text for w in ["ofert", "offer", "zbritje", "discount", "promo", "free", "falas", "paketa", "package", "çmim", "price"]):
        return "promotional"
    if any(w in text for w in ["tip", "këshillë", "advice", "mëso", "learn", "si të", "how to", "hap", "step", "trick"]):
        return "tip"
    if any(w in text for w in ["trend", "2024", "2025", "2026", "ai ", "artificial", "algorithm", "e ardhme", "future"]):
        return "trend"
    return "educational"


def load_history():
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(data):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/", methods=["GET"])
def index():
    history = load_history()
    posts = sorted(history["posts"], key=lambda p: p["id"])

    posts_html = ""
    for p in posts:
        img_tag = ""
        if p.get("image_path"):
            rel = p["image_path"].replace("\\", "/")
            img_tag = f'<img src="/{rel}" alt="post {p["id"]}">'

        posts_html += f"""
        <div class="post-card">
            <div class="post-img">{img_tag}</div>
            <div class="post-info">
                <div class="post-num">#{p['id']}</div>
                <div class="badge">{p.get('post_type', 'post')}</div>
                <div class="post-headline">{p.get('headline', '')}</div>
                <div class="post-caption">{p.get('caption', '')}</div>
            </div>
            <form method="POST" action="/delete/{p['id']}" onsubmit="return confirm('Delete post #{p['id']}?')">
                <button class="btn-delete" type="submit">✕</button>
            </form>
        </div>
        """

    if not posts_html:
        posts_html = '<p class="empty">No posts yet. Add your first one below.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sharp Group — Post Uploader</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #f5f5f5; color: #080808; }}

  header {{
    background: #080808;
    padding: 20px 40px;
    display: flex;
    align-items: center;
    gap: 14px;
  }}
  header h1 {{ color: #FF8643; font-size: 22px; letter-spacing: 1px; }}
  header span {{ color: #ffffff88; font-size: 13px; }}

  .container {{ max-width: 1100px; margin: 40px auto; padding: 0 24px; }}

  h2 {{ font-size: 16px; font-weight: 600; margin-bottom: 18px; text-transform: uppercase; letter-spacing: 0.5px; color: #080808; }}

  /* FORM */
  .form-card {{
    background: #fff;
    border-radius: 12px;
    padding: 32px;
    margin-bottom: 48px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
  }}
  .form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
  .form-group {{ display: flex; flex-direction: column; gap: 6px; }}
  .form-group.full {{ grid-column: 1 / -1; }}
  label {{ font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px; color: #666; }}
  input[type=text], input[type=number], textarea, select {{
    border: 1.5px solid #e0e0e0;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    font-family: inherit;
    outline: none;
    transition: border-color 0.2s;
    background: #fafafa;
  }}
  input:focus, textarea:focus, select:focus {{ border-color: #FF8643; background: #fff; }}
  textarea {{ resize: vertical; min-height: 90px; }}

  .upload-area {{
    border: 2px dashed #e0e0e0;
    border-radius: 8px;
    padding: 24px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
    background: #fafafa;
    position: relative;
  }}
  .upload-area:hover {{ border-color: #FF8643; background: #fff8f4; }}
  .upload-area input[type=file] {{
    position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; height: 100%;
  }}
  .upload-area .icon {{ font-size: 28px; margin-bottom: 8px; }}
  .upload-area p {{ font-size: 13px; color: #999; }}
  .upload-area strong {{ color: #FF8643; }}
  #file-name {{ margin-top: 8px; font-size: 13px; color: #FF8643; font-weight: 600; }}

  .btn-submit {{
    background: #FF8643;
    color: #fff;
    border: none;
    padding: 14px 36px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    margin-top: 8px;
  }}
  .btn-submit:hover {{ background: #e5722f; }}

  /* POSTS GRID */
  .posts-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
  .post-card {{
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    display: flex;
    flex-direction: column;
    position: relative;
  }}
  .post-img {{ width: 100%; aspect-ratio: 4/5; background: #f0f0f0; overflow: hidden; }}
  .post-img img {{ width: 100%; height: 100%; object-fit: cover; }}
  .post-info {{ padding: 16px; flex: 1; }}
  .post-num {{ font-size: 11px; color: #999; margin-bottom: 4px; }}
  .badge {{
    display: inline-block;
    background: #FF8643;
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 3px 8px;
    border-radius: 4px;
    margin-bottom: 10px;
  }}
  .post-headline {{ font-size: 14px; font-weight: 700; margin-bottom: 6px; }}
  .post-body {{ font-size: 12px; color: #555; margin-bottom: 8px; }}
  .post-caption {{ font-size: 11px; color: #888; line-height: 1.5; border-top: 1px solid #f0f0f0; padding-top: 8px; margin-top: 4px; }}
  .btn-delete {{
    position: absolute; top: 10px; right: 10px;
    background: #080808cc; color: #fff; border: none;
    width: 26px; height: 26px; border-radius: 50%;
    font-size: 11px; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
  }}
  .btn-delete:hover {{ background: #e53e3e; }}

  .empty {{ color: #aaa; font-size: 14px; padding: 40px 0; text-align: center; }}

  .flash {{
    background: #e6f9f0;
    border-left: 4px solid #38a169;
    color: #276749;
    padding: 14px 20px;
    border-radius: 8px;
    margin-bottom: 24px;
    font-size: 14px;
    font-weight: 500;
  }}
  .count-badge {{
    display: inline-block;
    background: #080808;
    color: #fff;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    margin-left: 8px;
    vertical-align: middle;
  }}
</style>
</head>
<body>

<header>
  <h1>SHARP GROUP</h1>
  <span>Post History Uploader</span>
</header>

<div class="container">

  {'<div class="flash">✓ ' + request.args.get('msg') + '</div>' if request.args.get('msg') else ''}

  <div class="form-card">
    <h2>Add New Post</h2>
    <form method="POST" action="/add" enctype="multipart/form-data">
      <div class="form-row">
        <div class="form-group full">
          <label>Post Number</label>
          <input type="number" name="post_id" placeholder="e.g. 1" min="1" required>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group full">
          <label>Text on Post</label>
          <input type="text" name="headline" placeholder="What's written on the image...">
        </div>
      </div>

      <div class="form-row">
        <div class="form-group full">
          <label>Caption (posted on Instagram)</label>
          <textarea name="caption" placeholder="The full Instagram caption including hashtags..."></textarea>
        </div>
      </div>

      <div class="form-row">
        <div class="form-group full">
          <label>Post Image</label>
          <div class="upload-area">
            <input type="file" name="image" accept="image/*" onchange="showFileName(this)">
            <div class="icon">📷</div>
            <p>Click to upload or drag & drop</p>
            <p><strong>PNG, JPG, WEBP</strong> supported</p>
            <div id="file-name"></div>
          </div>
        </div>
      </div>

      <button class="btn-submit" type="submit">Save Post →</button>
    </form>
  </div>

  <h2>Saved Posts <span class="count-badge">{len(posts)}</span></h2>
  <div class="posts-grid">
    {posts_html}
  </div>

</div>

<script>
function showFileName(input) {{
  const name = input.files[0]?.name || '';
  document.getElementById('file-name').textContent = name ? '✓ ' + name : '';
}}
</script>
</body>
</html>"""


@app.route("/add", methods=["POST"])
def add_post():
    history = load_history()
    post_id = int(request.form.get("post_id", 0))

    # Check for duplicate ID
    existing_ids = [p["id"] for p in history["posts"]]
    if post_id in existing_ids:
        return redirect(url_for("index", msg=f"Post #{post_id} already exists. Delete it first."))

    image_path = ""
    file = request.files.get("image")
    if file and file.filename and allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = secure_filename(f"post_{post_id:03d}.{ext}")
        full_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(full_path)
        image_path = f"uploads/{filename}"

    headline = request.form.get("headline", "").strip()
    body_text = ""
    caption = request.form.get("caption", "").strip()
    post_type = detect_post_type(headline, body_text, caption)

    post = {
        "id": post_id,
        "date": "",
        "post_type": post_type,
        "headline": headline,
        "body_text": body_text,
        "caption": caption,
        "visual_description": "",
        "image_path": image_path,
        "colors_used": ["#FF8643", "#080808", "#FFFFFF"],
        "engagement": {"likes": 0, "comments": 0}
    }

    history["posts"].append(post)
    save_history(history)

    return redirect(url_for("index", msg=f"Post #{post_id} saved successfully!"))


@app.route("/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    history = load_history()
    history["posts"] = [p for p in history["posts"] if p["id"] != post_id]
    save_history(history)
    return redirect(url_for("index", msg=f"Post #{post_id} deleted."))


@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    print("\n  Sharp Group Post Uploader")
    print("  → Open in browser: http://localhost:5050\n")
    app.run(debug=False, port=5050)
