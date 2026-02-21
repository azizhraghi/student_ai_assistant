"""
SQLite Database Manager — handles persistent storage for deadlines and tasks.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "student.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deadlines (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            subject     TEXT,
            due_date    TEXT    NOT NULL,
            priority    TEXT    DEFAULT 'medium',
            status      TEXT    DEFAULT 'pending',
            notes       TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


# ── CRUD Operations ────────────────────────────────────────────────────────────

def add_deadline(title: str, due_date: str, subject: str = "",
                 priority: str = "medium", notes: str = "") -> dict:
    """Add a new deadline. Returns the created record."""
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO deadlines (title, subject, due_date, priority, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (title, subject, due_date, priority, notes)
    )
    conn.commit()
    record = conn.execute(
        "SELECT * FROM deadlines WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    conn.close()
    return dict(record)


def get_all_deadlines(status: str = None) -> list[dict]:
    """Retrieve all deadlines, optionally filtered by status."""
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM deadlines WHERE status = ? ORDER BY due_date ASC", (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM deadlines ORDER BY due_date ASC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_deadline_status(deadline_id: int, status: str) -> bool:
    """Update the status of a deadline (pending/done/overdue)."""
    conn = get_connection()
    conn.execute(
        "UPDATE deadlines SET status = ? WHERE id = ?", (status, deadline_id)
    )
    conn.commit()
    changes = conn.total_changes
    conn.close()
    return changes > 0


def delete_deadline(deadline_id: int) -> bool:
    """Delete a deadline by ID."""
    conn = get_connection()
    conn.execute("DELETE FROM deadlines WHERE id = ?", (deadline_id,))
    conn.commit()
    changes = conn.total_changes
    conn.close()
    return changes > 0


def get_upcoming_deadlines(days: int = 7) -> list[dict]:
    """Get deadlines due within the next N days."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM deadlines
        WHERE status = 'pending'
          AND due_date BETWEEN date('now') AND date('now', ? || ' days')
        ORDER BY due_date ASC
    """, (str(days),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialize DB on import
init_db()
