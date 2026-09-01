"""Audit & logging layer — every request, every decision, every eventual
SME resolution gets written here. This is the required audit trail and the
seed of the feedback-loop bonus point.
"""
from __future__ import annotations
import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.environ.get("AUDIT_DB_PATH", os.path.join(os.path.dirname(__file__), "audit_log.db"))


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY,
            question TEXT,
            context TEXT,
            status TEXT,
            answer TEXT,
            answer_confidence REAL,
            routing_confidence REAL,
            sources TEXT,
            scope_flags TEXT,
            escalation TEXT,
            created_at TEXT,
            resolved_by TEXT,
            final_answer TEXT,
            was_ai_correct INTEGER,
            resolved_at TEXT
        )"""
    )
    return conn


def log_request(request_id: str, question: str, context: dict, response: dict) -> None:
    conn = _connect()
    conn.execute(
        """INSERT INTO requests
           (request_id, question, context, status, answer, answer_confidence,
            routing_confidence, sources, scope_flags, escalation, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            request_id,
            question,
            json.dumps(context),
            response.get("status"),
            response.get("answer"),
            response.get("confidence", {}).get("answer_confidence"),
            response.get("confidence", {}).get("routing_confidence"),
            json.dumps(response.get("sources", [])),
            json.dumps(response.get("scope_flags", [])),
            json.dumps(response.get("escalation")),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def log_resolution(request_id: str, resolved_by: str, final_answer: str, was_ai_correct: bool) -> bool:
    conn = _connect()
    cur = conn.execute(
        """UPDATE requests SET resolved_by = ?, final_answer = ?, was_ai_correct = ?, resolved_at = ?
           WHERE request_id = ?""",
        (resolved_by, final_answer, int(was_ai_correct), datetime.now(timezone.utc).isoformat(), request_id),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


def all_records() -> list[dict]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM requests ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
