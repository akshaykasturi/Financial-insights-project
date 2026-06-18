# tools/db_tools.py

import sqlite3
import os
from datetime import datetime

DB_PATH = "data/agent_runs.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name  TEXT,
            status      TEXT,
            message     TEXT,
            rows        INTEGER,
            model       TEXT,
            est_tokens  INTEGER,
            timestamp   TEXT
        )
    """)
    conn.commit()
    conn.close()


def estimate_tokens(text: str) -> int:
    """Rough estimate: ~4 characters per token (standard approximation)"""
    return len(text) // 4


def log_run(agent_name: str, status: str, message: str, rows: int = 0, model: str = "unknown"):
    """Log an agent run to SQLite, including estimated token usage"""
    init_db()
    est_tokens = estimate_tokens(message)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agent_runs (agent_name, status, message, rows, model, est_tokens, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (agent_name, status, message, rows, model, est_tokens, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    print(f"[LOG] {agent_name} | {status} | model={model} | ~{est_tokens} tokens | {message[:60]}")


def get_recent_runs(limit: int = 10) -> list:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT agent_name, status, message, rows, model, est_tokens, timestamp
        FROM agent_runs
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "agent_name": r[0], "status": r[1], "message": r[2],
            "rows": r[3], "model": r[4], "est_tokens": r[5], "timestamp": r[6]
        }
        for r in rows
    ]


def get_token_usage_today(model: str = None) -> dict:
    """Sum estimated tokens used today, optionally filtered by model"""
    init_db()
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if model:
        cursor.execute("""
            SELECT SUM(est_tokens), COUNT(*) FROM agent_runs
            WHERE timestamp LIKE ? AND model = ?
        """, (f"{today}%", model))
    else:
        cursor.execute("""
            SELECT model, SUM(est_tokens), COUNT(*) FROM agent_runs
            WHERE timestamp LIKE ?
            GROUP BY model
        """, (f"{today}%",))

    result = cursor.fetchall()
    conn.close()

    if model:
        total_tokens, count = result[0] if result[0][0] else (0, 0)
        return {"model": model, "total_tokens_today": total_tokens or 0, "calls_today": count or 0}
    else:
        return {row[0]: {"total_tokens_today": row[1], "calls_today": row[2]} for row in result}