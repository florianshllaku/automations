"""
Content Studio — PostgreSQL Database Layer

Schema
------
  users        business accounts with hashed passwords
  post_types   lookup: 1=normal, 2=carousel, 3=story
  posts        every piece of generated content
  post_files   extra files per post (carousel slides)
  captions     caption options per post
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv(Path(__file__).parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")


# ── Connection ────────────────────────────────────────────────────────────────

def _connect() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn


# ── Schema ────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables and seed lookup data. Safe to call on every startup."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            SERIAL PRIMARY KEY,
                    username      TEXT    NOT NULL UNIQUE,
                    email         TEXT             DEFAULT '',
                    password_hash TEXT    NOT NULL,
                    business_name TEXT    NOT NULL DEFAULT '',
                    created_at    TIMESTAMPTZ      DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS post_types (
                    id   INTEGER PRIMARY KEY,
                    name TEXT    NOT NULL UNIQUE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id           SERIAL PRIMARY KEY,
                    user_id      INTEGER NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
                    post_type_id INTEGER NOT NULL REFERENCES post_types(id),
                    filename     TEXT             DEFAULT '',
                    created_at   TIMESTAMPTZ      DEFAULT NOW()
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_user    ON posts(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_type    ON posts(post_type_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC)")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS post_files (
                    id       SERIAL PRIMARY KEY,
                    post_id  INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                    filename TEXT    NOT NULL,
                    position INTEGER NOT NULL DEFAULT 0
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_post_files_post ON post_files(post_id)")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS captions (
                    id         SERIAL PRIMARY KEY,
                    post_id    INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                    user_id    INTEGER NOT NULL REFERENCES users(id),
                    text       TEXT    NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_captions_post ON captions(post_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_captions_user ON captions(user_id)")

            # Seed post_types
            for pt_id, pt_name in [(1, "normal"), (2, "carousel"), (3, "story")]:
                cur.execute(
                    "INSERT INTO post_types (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (pt_id, pt_name),
                )
        conn.commit()
    print("  [DB] PostgreSQL ready")


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(
    username: str,
    password: str,
    business_name: str,
    email: str = "",
) -> int:
    pw_hash = generate_password_hash(password)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, business_name)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (username, email, pw_hash, business_name),
            )
            user_id = cur.fetchone()[0]
        conn.commit()
    return user_id


def get_user_by_username(username: str) -> dict | None:
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
    return dict(row) if row else None


def verify_login(username: str, password: str) -> dict | None:
    user = get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def update_password(user_id: int, new_password: str) -> None:
    pw_hash = generate_password_hash(new_password)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (pw_hash, user_id),
            )
        conn.commit()


# ── Posts ─────────────────────────────────────────────────────────────────────

POST_TYPE_IDS   = {"normal": 1, "carousel": 2, "story": 3}
POST_TYPE_NAMES = {v: k for k, v in POST_TYPE_IDS.items()}


def create_post(
    user_id: int,
    post_type: str,
    filename: str = "",
    extra_files: list[str] | None = None,
) -> int:
    pt_id = POST_TYPE_IDS.get(post_type, 1)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO posts (user_id, post_type_id, filename) VALUES (%s, %s, %s) RETURNING id",
                (user_id, pt_id, filename),
            )
            post_id = cur.fetchone()[0]
            for i, fn in enumerate(extra_files or []):
                cur.execute(
                    "INSERT INTO post_files (post_id, filename, position) VALUES (%s, %s, %s)",
                    (post_id, fn, i),
                )
        conn.commit()
    return post_id


def get_post(post_id: int) -> dict | None:
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT p.*, pt.name AS post_type, u.username, u.business_name
                FROM posts p
                JOIN post_types pt ON pt.id = p.post_type_id
                JOIN users u       ON u.id  = p.user_id
                WHERE p.id = %s
                """,
                (post_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["files"]    = _get_post_files(cur, post_id)
            d["captions"] = _get_captions(cur, post_id)
    return d


def get_posts(user_id: int) -> list[dict]:
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT p.*, pt.name AS post_type
                FROM posts p
                JOIN post_types pt ON pt.id = p.post_type_id
                WHERE p.user_id = %s
                ORDER BY p.id DESC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["files"]    = _get_post_files(cur, d["id"])
                d["captions"] = _get_captions(cur, d["id"])
                result.append(d)
    return result


def _get_post_files(cur, post_id: int) -> list[str]:
    cur.execute(
        "SELECT filename FROM post_files WHERE post_id = %s ORDER BY position",
        (post_id,),
    )
    return [r["filename"] for r in cur.fetchall()]


# ── Captions ──────────────────────────────────────────────────────────────────

def save_caption(post_id: int, user_id: int, text: str) -> int:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO captions (post_id, user_id, text) VALUES (%s, %s, %s) RETURNING id",
                (post_id, user_id, text),
            )
            caption_id = cur.fetchone()[0]
        conn.commit()
    return caption_id


def get_captions(post_id: int) -> list[dict]:
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            return _get_captions(cur, post_id)


def _get_captions(cur, post_id: int) -> list[dict]:
    cur.execute(
        "SELECT * FROM captions WHERE post_id = %s ORDER BY id",
        (post_id,),
    )
    return [dict(r) for r in cur.fetchall()]


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats(user_id: int) -> dict:
    with _connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT COUNT(*) AS n FROM posts WHERE user_id = %s", (user_id,)
            )
            total = cur.fetchone()["n"]

            cur.execute(
                """
                SELECT pt.name, COUNT(*) AS n
                FROM posts p JOIN post_types pt ON pt.id = p.post_type_id
                WHERE p.user_id = %s
                GROUP BY pt.id, pt.name
                """,
                (user_id,),
            )
            by_type = {r["name"]: r["n"] for r in cur.fetchall()}

            cur.execute(
                "SELECT created_at FROM posts WHERE user_id = %s ORDER BY id DESC LIMIT 1",
                (user_id,),
            )
            recent = cur.fetchone()

    return {
        "total":       total,
        "by_type":     by_type,
        "recent_date": str(recent["created_at"])[:10] if recent else "-",
    }
