"""
One-time DB reshape: remove theme columns from users, remove headline/meta from posts.
Run once: python slim_db.py
Safe to delete afterwards.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "studio.db"

conn = sqlite3.connect(str(DB_PATH))
conn.execute("PRAGMA foreign_keys = OFF")
conn.execute("PRAGMA journal_mode = WAL")

print("Reshaping users table...")
conn.executescript("""
    CREATE TABLE users_new (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT    NOT NULL UNIQUE,
        email         TEXT             DEFAULT '',
        password_hash TEXT    NOT NULL,
        business_name TEXT    NOT NULL DEFAULT '',
        created_at    TEXT             DEFAULT (datetime('now'))
    );
    INSERT INTO users_new (id, username, email, password_hash, business_name, created_at)
        SELECT id, username, email, password_hash, business_name, created_at FROM users;
    DROP TABLE users;
    ALTER TABLE users_new RENAME TO users;
""")

print("Reshaping posts table...")
conn.executescript("""
    CREATE TABLE posts_new (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        post_type_id INTEGER NOT NULL REFERENCES post_types(id),
        filename     TEXT             DEFAULT '',
        created_at   TEXT             DEFAULT (datetime('now'))
    );
    INSERT INTO posts_new (id, user_id, post_type_id, filename, created_at)
        SELECT id, user_id, post_type_id, filename, created_at FROM posts;
    DROP TABLE posts;
    ALTER TABLE posts_new RENAME TO posts;
""")

conn.execute("PRAGMA foreign_keys = ON")
conn.commit()
conn.close()

print("Done. studio.db is now on the slim schema.")
