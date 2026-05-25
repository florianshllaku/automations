"""
One-time migration: SQLite (studio.db) -> Railway PostgreSQL
Run once: py migrate_to_postgres.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from database import _connect as pg_connect, init_db
from werkzeug.security import generate_password_hash

SQLITE_PATH = Path(__file__).parent / "studio.db"


def migrate():
    if not SQLITE_PATH.exists():
        print("  [!] studio.db not found — nothing to migrate.")
        return

    print("  Connecting to SQLite...")
    sq = sqlite3.connect(str(SQLITE_PATH))
    sq.row_factory = sqlite3.Row

    print("  Initialising PostgreSQL schema...")
    init_db()

    pg = pg_connect()
    cur = pg.cursor()

    # ── Users ─────────────────────────────────────────────────────────────────
    users = sq.execute("SELECT * FROM users").fetchall()
    print(f"  Migrating {len(users)} users...")
    for u in users:
        cur.execute(
            """
            INSERT INTO users (id, username, email, password_hash, business_name, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
            """,
            (u["id"], u["username"], u["email"] or "",
             u["password_hash"], u["business_name"] or "", u["created_at"]),
        )

    # ── Posts ─────────────────────────────────────────────────────────────────
    posts = sq.execute("SELECT * FROM posts").fetchall()
    print(f"  Migrating {len(posts)} posts...")
    for p in posts:
        cur.execute(
            """
            INSERT INTO posts (id, user_id, post_type_id, filename, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (p["id"], p["user_id"], p["post_type_id"], p["filename"] or "", p["created_at"]),
        )

    # ── Post files ────────────────────────────────────────────────────────────
    files = sq.execute("SELECT * FROM post_files").fetchall()
    print(f"  Migrating {len(files)} post files...")
    for f in files:
        cur.execute(
            """
            INSERT INTO post_files (id, post_id, filename, position)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (f["id"], f["post_id"], f["filename"], f["position"]),
        )

    # ── Captions ──────────────────────────────────────────────────────────────
    captions = sq.execute("SELECT * FROM captions").fetchall()
    print(f"  Migrating {len(captions)} captions...")
    for c in captions:
        cur.execute(
            """
            INSERT INTO captions (id, post_id, user_id, text, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (c["id"], c["post_id"], c["user_id"], c["text"].replace("\x00", ""), c["created_at"]),
        )

    # Fix sequences so new inserts get correct auto-increment IDs
    for table, col in [("users", "id"), ("posts", "id"), ("post_files", "id"), ("captions", "id")]:
        cur.execute(f"SELECT MAX({col}) FROM {table}")
        max_id = cur.fetchone()[0] or 0
        cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), %s)", (max(max_id, 1),))

    pg.commit()
    cur.close()
    pg.close()
    sq.close()

    print("  Done. All data migrated to PostgreSQL.")


if __name__ == "__main__":
    print("\n  SQLite -> PostgreSQL Migration")
    print("  --------------------------------")
    migrate()
