"""Persistent escalation conversations and expert-approved learned knowledge."""
from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone

from audit import DB_PATH


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS escalation_cases (
            id TEXT PRIMARY KEY, request_id TEXT UNIQUE, question TEXT NOT NULL,
            requester_id TEXT, requester_name TEXT NOT NULL, assigned_name TEXT NOT NULL,
            assigned_tier TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
            resolved_at TEXT
        );
        CREATE TABLE IF NOT EXISTS case_messages (
            id TEXT PRIMARY KEY, case_id TEXT NOT NULL, sender_id TEXT,
            sender_name TEXT NOT NULL, sender_kind TEXT NOT NULL, content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS knowledge_candidates (
            id TEXT PRIMARY KEY, case_id TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
            question TEXT NOT NULL, answer TEXT NOT NULL, keywords TEXT NOT NULL,
            status TEXT NOT NULL, reviewer_name TEXT, created_at TEXT NOT NULL,
            decided_at TEXT
        );
        CREATE TABLE IF NOT EXISTS approved_knowledge (
            id TEXT PRIMARY KEY, candidate_id TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
            question TEXT NOT NULL, answer TEXT NOT NULL, keywords TEXT NOT NULL,
            approved_by TEXT NOT NULL, created_at TEXT NOT NULL
        );
        """
    )
    return conn


def create_case(
    request_id: str, question: str, requester_id: str | None,
    requester_name: str | None, assigned_name: str, assigned_tier: str,
) -> None:
    conn = _connect()
    conn.execute(
        """INSERT OR IGNORE INTO escalation_cases
           (id, request_id, question, requester_id, requester_name, assigned_name,
            assigned_tier, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?)""",
        (str(uuid.uuid4()), request_id, question, requester_id,
         requester_name or "Relationship Manager", assigned_name, assigned_tier, _now()),
    )
    conn.commit()
    conn.close()


def _candidate(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    result = dict(row)
    result["keywords"] = json.loads(result["keywords"])
    return result


def list_cases(user_name: str, view: str) -> list[dict]:
    conn = _connect()
    column = "assigned_name" if view == "assigned" else "requester_name"
    rows = conn.execute(
        f"SELECT * FROM escalation_cases WHERE {column} = ? ORDER BY created_at DESC",
        (user_name,),
    ).fetchall()
    result = []
    for row in rows:
        case = dict(row)
        case["messages"] = [dict(item) for item in conn.execute(
            "SELECT * FROM case_messages WHERE case_id = ? ORDER BY created_at", (row["id"],)
        ).fetchall()]
        case["knowledge_candidate"] = _candidate(conn.execute(
            "SELECT * FROM knowledge_candidates WHERE case_id = ?", (row["id"],)
        ).fetchone())
        result.append(case)
    conn.close()
    return result


def get_case(case_id: str) -> dict | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM escalation_cases WHERE id = ?", (case_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    cases = list_cases(row["assigned_name"], "assigned")
    return next((case for case in cases if case["id"] == case_id), None)


def add_message(case_id: str, sender_id: str, sender_name: str,
                sender_kind: str, content: str) -> dict | None:
    conn = _connect()
    case = conn.execute("SELECT * FROM escalation_cases WHERE id = ?", (case_id,)).fetchone()
    if case is None:
        conn.close()
        return None
    message = {
        "id": str(uuid.uuid4()), "case_id": case_id, "sender_id": sender_id,
        "sender_name": sender_name, "sender_kind": sender_kind,
        "content": content.strip(), "created_at": _now(),
    }
    conn.execute(
        """INSERT INTO case_messages
           (id, case_id, sender_id, sender_name, sender_kind, content, created_at)
           VALUES (:id, :case_id, :sender_id, :sender_name, :sender_kind, :content, :created_at)""",
        message,
    )
    if sender_kind == "expert":
        conn.execute(
            "UPDATE escalation_cases SET status = 'answered', resolved_at = ? WHERE id = ?",
            (_now(), case_id),
        )
    conn.commit()
    conn.close()
    return message


def save_candidate(case_id: str, title: str, question: str, answer: str,
                   keywords: list[str]) -> dict:
    conn = _connect()
    candidate_id = str(uuid.uuid4())
    conn.execute(
        """INSERT OR REPLACE INTO knowledge_candidates
           (id, case_id, title, question, answer, keywords, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
        (candidate_id, case_id, title, question, answer, json.dumps(keywords), _now()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM knowledge_candidates WHERE case_id = ?", (case_id,)).fetchone()
    conn.close()
    return _candidate(row) or {}


def decide_candidate(candidate_id: str, reviewer_name: str, decision: str) -> dict | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM knowledge_candidates WHERE id = ?", (candidate_id,)).fetchone()
    if row is None or row["status"] != "pending":
        conn.close()
        return None
    conn.execute(
        "UPDATE knowledge_candidates SET status = ?, reviewer_name = ?, decided_at = ? WHERE id = ?",
        (decision, reviewer_name, _now(), candidate_id),
    )
    if decision == "accepted":
        conn.execute(
            """INSERT OR IGNORE INTO approved_knowledge
               (id, candidate_id, title, question, answer, keywords, approved_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), candidate_id, row["title"], row["question"], row["answer"],
             row["keywords"], reviewer_name, _now()),
        )
    conn.commit()
    updated = conn.execute("SELECT * FROM knowledge_candidates WHERE id = ?", (candidate_id,)).fetchone()
    conn.close()
    return _candidate(updated)


def _tokens(value: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", value.lower()) if len(word) > 2}


def retrieve_approved(query: str, threshold: float = 0.45) -> tuple[dict, float] | None:
    query_tokens = _tokens(query)
    if not query_tokens:
        return None
    conn = _connect()
    rows = conn.execute("SELECT * FROM approved_knowledge").fetchall()
    conn.close()
    best: tuple[dict, float] | None = None
    for row in rows:
        item = dict(row)
        knowledge_tokens = _tokens(" ".join([
            item["title"], item["question"], " ".join(json.loads(item["keywords"])),
        ]))
        score = len(query_tokens & knowledge_tokens) / max(1, len(query_tokens))
        if score >= threshold and (best is None or score > best[1]):
            best = (item, score)
    return best
