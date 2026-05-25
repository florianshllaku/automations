"""
Content Studio — Full Migration to New Schema
Run: python migrate.py

Steps:
  1. Creates new tables (users, post_types, posts, post_files, captions)
  2. Seeds the two business user accounts
  3. Migrates old sg_posts -> posts  (for sharp_group user)
  4. Migrates old vt_posts -> posts  (for ventura user)
  5. Old tables are renamed with _old suffix (safe to DROP later)
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from database import (
    DB_PATH, POST_TYPE_IDS, create_user, create_post, get_user_by_username,
    init_db, save_caption,
)

BASE = Path(__file__).parent


# ── Helpers ───────────────────────────────────────────────────────────────────

def _raw_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")  # off during migration
    return conn


def old_table_exists(conn, name: str) -> bool:
    r = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return r is not None


# ── Seed users ────────────────────────────────────────────────────────────────

def seed_users() -> dict[str, int]:
    """Create the two business accounts. Return {username: user_id}."""
    users = {}

    configs = [
        {
            "username":      "sharp_group",
            "password":      os.getenv("SHARP_PASSWORD", "sharpgroup2024"),
            "business_name": "Sharp Group",
        },
        {
            "username":      "ventura",
            "password":      os.getenv("VENTURA_PASSWORD", "ventura2026"),
            "business_name": "Ventura Travel",
        },
    ]

    for cfg in configs:
        existing = get_user_by_username(cfg["username"])
        if existing:
            users[cfg["username"]] = existing["id"]
            print(f"  [users] '{cfg['username']}' already exists (id={existing['id']})")
        else:
            uid = create_user(**cfg)
            users[cfg["username"]] = uid
            print(f"  [users] Created '{cfg['username']}' (id={uid})")

    return users


# ── Migrate Sharp Group ───────────────────────────────────────────────────────

def migrate_sg(conn: sqlite3.Connection, user_id: int) -> int:
    if not old_table_exists(conn, "sg_posts"):
        print("  [SG] No old sg_posts table found.")
        return 0

    rows = conn.execute("SELECT * FROM sg_posts").fetchall()
    count = 0

    for r in rows:
        filename = r["filename"] if "filename" in r.keys() else (r["image_path"] or "")
        post_id = create_post(
            user_id=user_id,
            post_type="normal",
            filename=filename,
        )
        if r["caption"]:
            save_caption(post_id, user_id, r["caption"])
        count += 1

    print(f"  [SG] Migrated {count} posts from sg_posts.")
    return count


# ── Migrate Ventura ───────────────────────────────────────────────────────────

def migrate_vt(conn: sqlite3.Connection, user_id: int) -> int:
    if not old_table_exists(conn, "vt_posts"):
        print("  [VT] No old vt_posts table found.")
        return 0

    rows = conn.execute("SELECT * FROM vt_posts").fetchall()
    count = 0

    for r in rows:
        old_type  = r["type"] or "post"
        post_type = {"post": "normal", "carousel": "carousel", "story": "story"}.get(old_type, "normal")

        slide_rows = conn.execute(
            "SELECT filename FROM vt_slides WHERE post_id = ? ORDER BY position",
            (r["id"],),
        ).fetchall()
        slides = [s["filename"] for s in slide_rows]

        post_id = create_post(
            user_id=user_id,
            post_type=post_type,
            filename=r["filename"] or "",
            extra_files=slides,
        )

        if r["caption"]:
            save_caption(post_id, user_id, r["caption"])

        count += 1

    print(f"  [VT] Migrated {count} posts from vt_posts.")
    return count


# ── Rename old tables ─────────────────────────────────────────────────────────

def archive_old_tables(conn: sqlite3.Connection):
    for name in ["sg_posts", "vt_posts", "vt_services", "vt_slides"]:
        if old_table_exists(conn, name):
            conn.execute(f"ALTER TABLE {name} RENAME TO {name}_old")
            print(f"  [archive] {name} -> {name}_old")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  Content Studio - Migration v2: New Schema")
    print("  ------------------------------------------")

    # 1. Create new tables
    init_db()

    # 2. Seed users
    print("\n  Creating user accounts...")
    users = seed_users()

    # 3. Migrate data using raw connection (old tables still exist)
    print("\n  Migrating posts...")
    with _raw_connect() as conn:
        sg_count = migrate_sg(conn, users["sharp_group"])
        vt_count = migrate_vt(conn, users["ventura"])

    # 4. Archive old tables
    print("\n  Archiving old tables...")
    with _raw_connect() as conn:
        archive_old_tables(conn)

    print(f"\n  Done. {sg_count + vt_count} posts migrated to new schema.")
    print("  Old tables renamed to *_old (safe to DROP anytime).")
    print()
