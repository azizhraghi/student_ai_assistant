"""
Collab Database — manages study rooms, members, uploads, and shared chat.
Uses SQLite for persistent multi-student collaboration.
"""

import sqlite3
import os
import json
import random
import string
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "collab.db")
# Resolves to project_root/data/collab.db


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
    return conn


def init_collab_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS rooms (
            code        TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            graph_cache TEXT DEFAULT NULL,
            graph_built_at TEXT DEFAULT NULL
        );

        CREATE TABLE IF NOT EXISTS members (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code   TEXT NOT NULL,
            username    TEXT NOT NULL,
            joined_at   TEXT DEFAULT (datetime('now')),
            is_active   INTEGER DEFAULT 1,
            UNIQUE(room_code, username)
        );

        CREATE TABLE IF NOT EXISTS uploads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code   TEXT NOT NULL,
            username    TEXT NOT NULL,
            filename    TEXT NOT NULL,
            content     TEXT NOT NULL,
            uploaded_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            room_code   TEXT NOT NULL,
            username    TEXT NOT NULL,
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            agent       TEXT DEFAULT 'general',
            created_at  TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


# ── Room Operations ────────────────────────────────────────────────────────────

def generate_room_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def create_room(name: str) -> dict:
    conn = get_connection()
    code = generate_room_code()
    # Ensure uniqueness
    while conn.execute("SELECT 1 FROM rooms WHERE code=?", (code,)).fetchone():
        code = generate_room_code()
    conn.execute("INSERT INTO rooms (code, name) VALUES (?,?)", (code, name))
    conn.commit()
    row = dict(conn.execute("SELECT * FROM rooms WHERE code=?", (code,)).fetchone())
    conn.close()
    return row


def get_room(code: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM rooms WHERE code=?", (code.upper(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def invalidate_room_graph(room_code: str):
    """Clear cached graph so it gets rebuilt next time."""
    conn = get_connection()
    conn.execute("UPDATE rooms SET graph_cache=NULL, graph_built_at=NULL WHERE code=?", (room_code,))
    conn.commit()
    conn.close()


def save_room_graph(room_code: str, graph_json: str):
    conn = get_connection()
    conn.execute(
        "UPDATE rooms SET graph_cache=?, graph_built_at=datetime('now') WHERE code=?",
        (graph_json, room_code)
    )
    conn.commit()
    conn.close()


def get_room_graph(room_code: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT graph_cache FROM rooms WHERE code=?", (room_code,)).fetchone()
    conn.close()
    if row and row["graph_cache"]:
        try:
            return json.loads(row["graph_cache"])
        except Exception:
            return None
    return None


# ── Member Operations ──────────────────────────────────────────────────────────

def join_room(room_code: str, username: str) -> bool:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO members (room_code, username, is_active) VALUES (?,?,1)",
            (room_code.upper(), username)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False


def get_members(room_code: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM members WHERE room_code=? AND is_active=1 ORDER BY joined_at ASC",
        (room_code.upper(),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Upload Operations ──────────────────────────────────────────────────────────

def add_upload(room_code: str, username: str, filename: str, content: str) -> dict:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO uploads (room_code, username, filename, content) VALUES (?,?,?,?)",
        (room_code.upper(), username, filename, content)
    )
    conn.commit()
    row = dict(conn.execute("SELECT * FROM uploads WHERE id=?", (cursor.lastrowid,)).fetchone())
    conn.close()
    invalidate_room_graph(room_code)
    return row


def get_uploads(room_code: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM uploads WHERE room_code=? ORDER BY uploaded_at ASC",
        (room_code.upper(),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_merged_content(room_code: str) -> str:
    """Merge all uploaded content from all members into one string."""
    uploads = get_uploads(room_code)
    if not uploads:
        return ""
    sections = []
    for u in uploads:
        sections.append(f"=== {u['filename']} (by {u['username']}) ===\n{u['content']}")
    return "\n\n".join(sections)


# ── Message Operations ─────────────────────────────────────────────────────────

def add_message(room_code: str, username: str, role: str, content: str, agent: str = "general") -> dict:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO messages (room_code, username, role, content, agent) VALUES (?,?,?,?,?)",
        (room_code.upper(), username, role, content, agent)
    )
    conn.commit()
    row = dict(conn.execute("SELECT * FROM messages WHERE id=?", (cursor.lastrowid,)).fetchone())
    conn.close()
    return row


def get_messages(room_code: str, limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages WHERE room_code=? ORDER BY created_at DESC LIMIT ?",
        (room_code.upper(), limit)
    ).fetchall()
    conn.close()
    return list(reversed([dict(r) for r in rows]))


# Initialize on import
init_collab_db()
