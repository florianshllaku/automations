"""
Content Studio — SQLite Database Layer
File: studio.db

Schema
------
  users        business accounts with hashed passwords
  post_types   lookup: 1=normal, 2=carousel, 3=story
  posts        every piece of generated content
  post_files   extra files per post (carousel slides)
  captions     caption options per post
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = Path(__file__).parent / "studio.db"


# ── Connection ────────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ── Schema ────────────────────────────────────────────────────────────────────

SCHEMA = """
-- Business accounts
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    email         TEXT             DEFAULT '',
    password_hash TEXT    NOT NULL,
    business_name TEXT    NOT NULL DEFAULT '',
    created_at    TEXT             DEFAULT (datetime('now'))
);

-- Post format lookup (seeded once, never changes)
CREATE TABLE IF NOT EXISTS post_types (
    id   INTEGER PRIMARY KEY,
    name TEXT    NOT NULL UNIQUE   -- 'normal' | 'carousel' | 'story'
);

-- All content posts, unified across businesses
CREATE TABLE IF NOT EXISTS posts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
    post_type_id INTEGER NOT NULL REFERENCES post_types(id),
    filename     TEXT             DEFAULT '',
    created_at   TEXT             DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_posts_user    ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_type    ON posts(post_type_id);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC);

-- Extra files per post (carousel slides beyond the cover)
CREATE TABLE IF NOT EXISTS post_files (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id  INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    filename TEXT    NOT NULL,
    position INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_post_files_post ON post_files(post_id);

-- Caption options generated for a post
CREATE TABLE IF NOT EXISTS captions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id    INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    text       TEXT    NOT NULL,
    created_at TEXT             DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_captions_post ON captions(post_id);
CREATE INDEX IF NOT EXISTS idx_captions_user ON captions(user_id);
"""

POST_TYPES_SEED = [
    (1, "normal"),
    (2, "carousel"),
    (3, "story"),
]


def init_db() -> None:
    """Create tables, seed lookup data. Safe to call on every startup."""
    with _connect() as conn:
        conn.executescript(SCHEMA)
        for pt_id, pt_name in POST_TYPES_SEED:
            conn.execute(
                "INSERT OR IGNORE INTO post_types (id, name) VALUES (?, ?)",
                (pt_id, pt_name),
            )
    print(f"  [DB] Ready: {DB_PATH}")


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(
    username: str,
    password: str,
    business_name: str,
    email: str = "",
) -> int:
    """Create a user and return their new ID."""
    pw_hash = generate_password_hash(password)
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, business_name)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, pw_hash, business_name),
        )
        return cur.lastrowid


def get_user_by_username(username: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def verify_login(username: str, password: str) -> dict | None:
    """Return user dict if credentials are valid, else None."""
    user = get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def update_password(user_id: int, new_password: str) -> None:
    pw_hash = generate_password_hash(new_password)
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (pw_hash, user_id),
        )


# ── Posts ─────────────────────────────────────────────────────────────────────

POST_TYPE_IDS   = {"normal": 1, "carousel": 2, "story": 3}
POST_TYPE_NAMES = {v: k for k, v in POST_TYPE_IDS.items()}


def create_post(
    user_id: int,
    post_type: str,               # 'normal' | 'carousel' | 'story'
    filename: str = "",
    extra_files: list[str] | None = None,   # carousel slides (excluding cover)
) -> int:
    """Insert a new post and return its ID."""
    pt_id = POST_TYPE_IDS.get(post_type, 1)

    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO posts (user_id, post_type_id, filename) VALUES (?, ?, ?)",
            (user_id, pt_id, filename),
        )
        post_id = cur.lastrowid

        for i, fn in enumerate(extra_files or []):
            conn.execute(
                "INSERT INTO post_files (post_id, filename, position) VALUES (?, ?, ?)",
                (post_id, fn, i),
            )

    return post_id


def get_post(post_id: int) -> dict | None:
    """Fetch a single post with its files and captions."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT p.*, pt.name AS post_type, u.username, u.business_name
            FROM posts p
            JOIN post_types pt ON pt.id = p.post_type_id
            JOIN users u       ON u.id  = p.user_id
            WHERE p.id = ?
            """,
            (post_id,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["files"]    = _get_post_files(conn, post_id)
        d["captions"] = _get_captions(conn, post_id)
    return d


def get_posts(user_id: int) -> list[dict]:
    """Return all posts for a user, newest first, with files and captions."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT p.*, pt.name AS post_type
            FROM posts p
            JOIN post_types pt ON pt.id = p.post_type_id
            WHERE p.user_id = ?
            ORDER BY p.id DESC
            """,
            (user_id,),
        ).fetchall()

        result = []
        for row in rows:
            d = dict(row)
            d["files"]    = _get_post_files(conn, d["id"])
            d["captions"] = _get_captions(conn, d["id"])
            result.append(d)

    return result


def _get_post_files(conn: sqlite3.Connection, post_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT filename FROM post_files WHERE post_id = ? ORDER BY position",
        (post_id,),
    ).fetchall()
    return [r["filename"] for r in rows]


# ── Captions ──────────────────────────────────────────────────────────────────

def save_caption(post_id: int, user_id: int, text: str) -> int:
    """Save a caption for a post. Returns caption ID."""
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO captions (post_id, user_id, text) VALUES (?, ?, ?)",
            (post_id, user_id, text),
        )
        return cur.lastrowid


def get_captions(post_id: int) -> list[dict]:
    with _connect() as conn:
        return _get_captions(conn, post_id)


def _get_captions(conn: sqlite3.Connection, post_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM captions WHERE post_id = ? ORDER BY id",
        (post_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats(user_id: int) -> dict:
    with _connect() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE user_id = ?", (user_id,)
        ).fetchone()[0]

        by_type = conn.execute(
            """
            SELECT pt.name, COUNT(*) as n
            FROM posts p JOIN post_types pt ON pt.id = p.post_type_id
            WHERE p.user_id = ?
            GROUP BY pt.id
            """,
            (user_id,),
        ).fetchall()

        recent = conn.execute(
            "SELECT created_at FROM posts WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    return {
        "total":       total,
        "by_type":     {r["name"]: r["n"] for r in by_type},
        "recent_date": (recent["created_at"] or "")[:10] if recent else "-",
    }
