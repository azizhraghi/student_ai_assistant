"""
Study Tracker — logs every meaningful student interaction for analytics.
Tracks quiz attempts, agent usage, study sessions, topic engagement.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "analytics.db")
# Resolves to project_root/data/analytics.db


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_analytics_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT NOT NULL,
            agent_used   TEXT NOT NULL,
            topic        TEXT DEFAULT '',
            duration_sec INTEGER DEFAULT 0,
            created_at   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT NOT NULL,
            topic        TEXT DEFAULT 'General',
            score        INTEGER NOT NULL,
            total        INTEGER NOT NULL,
            pct          REAL NOT NULL,
            created_at   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS topic_engagement (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            date         TEXT NOT NULL,
            topic        TEXT NOT NULL,
            agent        TEXT NOT NULL,
            created_at   TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


# ── Log Functions ──────────────────────────────────────────────────────────────

def log_session(agent_used: str, topic: str = "", duration_sec: int = 0):
    conn = get_connection()
    conn.execute(
        "INSERT INTO study_sessions (date, agent_used, topic, duration_sec) VALUES (date('now'),?,?,?)",
        (agent_used, topic, duration_sec)
    )
    conn.commit()
    conn.close()


def log_quiz(score: int, total: int, topic: str = "General"):
    pct = round(score / total * 100, 1) if total else 0
    conn = get_connection()
    conn.execute(
        "INSERT INTO quiz_attempts (date, topic, score, total, pct) VALUES (date('now'),?,?,?,?)",
        (topic, score, total, pct)
    )
    conn.commit()
    conn.close()


def log_topic(topic: str, agent: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO topic_engagement (date, topic, agent) VALUES (date('now'),?,?)",
        (topic, agent)
    )
    conn.commit()
    conn.close()


# ── Analytics Queries ──────────────────────────────────────────────────────────

def get_daily_activity(days: int = 30) -> list[dict]:
    """Sessions per day for the last N days."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT date, COUNT(*) as count
        FROM study_sessions
        WHERE date >= date('now', ? || ' days')
        GROUP BY date
        ORDER BY date ASC
    """, (f"-{days}",)).fetchall()
    conn.close()

    # Fill missing days with 0
    result = {}
    for i in range(days):
        d = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        result[d] = 0
    for r in rows:
        result[r["date"]] = r["count"]
    return [{"date": k, "count": v} for k, v in result.items()]


def get_agent_usage(days: int = 30) -> dict:
    """Count of sessions per agent."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT agent_used, COUNT(*) as count
        FROM study_sessions
        WHERE date >= date('now', ? || ' days')
        GROUP BY agent_used
        ORDER BY count DESC
    """, (f"-{days}",)).fetchall()
    conn.close()
    return {r["agent_used"]: r["count"] for r in rows}


def get_quiz_history(limit: int = 20) -> list[dict]:
    """Recent quiz attempts with scores."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM quiz_attempts ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def get_quiz_stats() -> dict:
    """Aggregate quiz statistics."""
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*) as total_attempts,
            ROUND(AVG(pct), 1) as avg_score,
            MAX(pct) as best_score,
            MIN(pct) as worst_score,
            SUM(score) as total_correct,
            SUM(total) as total_questions
        FROM quiz_attempts
    """).fetchone()
    conn.close()
    return dict(row) if row else {}


def get_topic_frequency(days: int = 30, top_n: int = 8) -> list[dict]:
    """Most studied topics."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT topic, COUNT(*) as count
        FROM topic_engagement
        WHERE date >= date('now', ? || ' days') AND topic != ''
        GROUP BY topic
        ORDER BY count DESC
        LIMIT ?
    """, (f"-{days}", top_n)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_study_streak() -> dict:
    """Calculate current and longest study streaks."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT date FROM study_sessions ORDER BY date DESC"
    ).fetchall()
    conn.close()

    if not rows:
        return {"current": 0, "longest": 0, "total_days": 0}

    dates = [datetime.strptime(r["date"], "%Y-%m-%d").date() for r in rows]
    today = datetime.now().date()

    # Current streak
    current = 0
    check = today
    for d in dates:
        if d == check or d == check - timedelta(days=1):
            if d == check - timedelta(days=1):
                check = d
            current += 1
            check = d - timedelta(days=1)
        elif d < check - timedelta(days=1):
            break

    # Longest streak
    longest = 1
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 1

    return {
        "current": current,
        "longest": longest,
        "total_days": len(dates),
    }


def get_full_summary(days: int = 30) -> dict:
    """Full analytics summary for AI report generation."""
    from tools.db import get_all_deadlines
    deadlines = get_all_deadlines()
    done = sum(1 for d in deadlines if d["status"] == "done")
    pending = sum(1 for d in deadlines if d["status"] == "pending")

    return {
        "daily_activity": get_daily_activity(days),
        "agent_usage": get_agent_usage(days),
        "quiz_history": get_quiz_history(10),
        "quiz_stats": get_quiz_stats(),
        "topic_frequency": get_topic_frequency(days),
        "streak": get_study_streak(),
        "deadlines": {"done": done, "pending": pending, "total": len(deadlines)},
    }


def seed_demo_data():
    """Seed realistic demo data so the dashboard looks great on first launch."""
    conn = get_connection()
    existing = conn.execute("SELECT COUNT(*) as c FROM study_sessions").fetchone()["c"]
    conn.close()
    if existing > 0:
        return  # Already seeded

    import random
    agents = ["course_agent", "revision_agent", "deadline_agent", "research_agent", "general"]
    topics = ["Machine Learning", "Neural Networks", "Data Structures", "Algorithms",
              "Linear Algebra", "Probability", "Python", "Deep Learning"]

    # Sessions over last 28 days
    for i in range(28):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        n_sessions = random.randint(0, 5) if i > 3 else random.randint(2, 6)
        conn = get_connection()
        for _ in range(n_sessions):
            agent = random.choice(agents)
            topic = random.choice(topics)
            conn.execute(
                "INSERT INTO study_sessions (date, agent_used, topic, created_at) VALUES (?,?,?,?)",
                (date, agent, topic, date + " 10:00:00")
            )
            conn.execute(
                "INSERT INTO topic_engagement (date, topic, agent, created_at) VALUES (?,?,?,?)",
                (date, topic, agent, date + " 10:00:00")
            )
        conn.commit()
        conn.close()

    # Quiz attempts — improving trend
    quiz_topics = ["Machine Learning", "Data Structures", "Neural Networks", "Algorithms"]
    base_scores = [45, 52, 58, 63, 67, 72, 75, 78, 82, 85, 88, 90]
    for i, pct in enumerate(base_scores):
        date = (datetime.now() - timedelta(days=len(base_scores) - i)).strftime("%Y-%m-%d")
        topic = quiz_topics[i % len(quiz_topics)]
        total = 10
        score = round(total * pct / 100)
        conn = get_connection()
        conn.execute(
            "INSERT INTO quiz_attempts (date, topic, score, total, pct, created_at) VALUES (?,?,?,?,?,?)",
            (date, topic, score, total, float(pct), date + " 14:00:00")
        )
        conn.commit()
        conn.close()


init_analytics_db()
