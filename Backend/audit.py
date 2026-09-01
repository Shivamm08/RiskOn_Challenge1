"""Audit & logging layer — Postgres-backed (was SQLite; Vercel's ephemeral
filesystem can't hold a local file, this was the whole reason for Supabase).
"""
from __future__ import annotations
import json

import db


def log_request(request_id: str, rm_id: str | None, question: str, context: dict, response: dict) -> None:
    db.execute(
        """INSERT INTO audit_log
           (request_id, rm_id, question, context, status, answer, answer_confidence,
            routing_confidence, sources, scope_flags, reasoning_trail)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            request_id, rm_id, question, json.dumps(context), response.get("status"),
            response.get("answer"),
            response.get("confidence", {}).get("answer_confidence"),
            response.get("confidence", {}).get("routing_confidence"),
            json.dumps(response.get("sources", [])),
            response.get("scope_flags", []),
            response.get("reasoning", []),
        ),
    )


def log_resolution(request_id: str, resolved_by: str, final_answer: str, was_ai_correct: bool) -> bool:
    db.execute(
        """UPDATE audit_log SET resolved_by=%s, final_answer=%s, was_ai_correct=%s, resolved_at=now()
           WHERE request_id=%s""",
        (resolved_by, final_answer, was_ai_correct, request_id),
    )
    return True


def all_records(limit: int = 200) -> list[dict]:
    return db.query("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT %s", (limit,))


def eval_summary() -> dict:
    """Lightweight evaluation-dashboard data — aggregate stats over the audit
    log, for the 'evaluation dashboard' bonus point."""
    rows = db.query(
        """SELECT status, count(*) as n, avg(answer_confidence) as avg_conf
           FROM audit_log GROUP BY status"""
    )
    total = db.query("SELECT count(*) as n FROM audit_log")[0]["n"]
    feedback = db.query(
        """SELECT count(*) filter (where was_ai_correct = true) as correct,
                  count(*) filter (where was_ai_correct = false) as incorrect
           FROM audit_log WHERE was_ai_correct IS NOT NULL"""
    )[0]
    return {
        "total_requests": total,
        "by_status": rows,
        "feedback_correct": feedback["correct"],
        "feedback_incorrect": feedback["incorrect"],
    }
