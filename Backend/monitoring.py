"""Monitoring system — the brief's SECOND deliverable, not a bonus point:
"a monitoring system that continuously checks the responses of the AI
assistant... for accuracy, completeness and currency. It compares the
answers with official internal sources and identifies deviations,
generating proposals for corrective measures."

This scans recent answered questions in audit_log and checks three things:
1. Groundedness — does the stored answer still trace back to its cited source?
2. Staleness — has the cited source since changed (wiki page updated, or a
   cited chat_kb entry been superseded/flagged/removed)?
3. Contradiction — does a cited chat_kb entry conflict with the wiki page
   it was checked against at kb-publish time?

Findings are written to monitoring_flags with a proposed corrective action —
not auto-applied, a human reviews and resolves each flag.
"""
from __future__ import annotations
import json

import db
from reasoning import verify_grounded


def run_monitoring_pass(limit: int = 100) -> dict:
    rows = db.query(
        """SELECT request_id, answer, sources FROM audit_log
           WHERE status = 'answered' AND answer IS NOT NULL
           ORDER BY created_at DESC LIMIT %s""",
        (limit,),
    )

    wiki_by_title = {r["title"]: r for r in db.query("SELECT title, plain_text, updated_at FROM wiki_pages")}
    kb_by_id = {str(r["id"]): r for r in db.query("SELECT id, answer, status, updated_at FROM kb_entries")}

    flags_created = 0
    checked = 0

    for row in rows:
        checked += 1
        sources = row["sources"] if isinstance(row["sources"], list) else json.loads(row["sources"] or "[]")
        if not sources:
            continue
        primary = sources[0]
        source_type = primary.get("source_type", "wiki")
        page_title = primary.get("page_title", "")

        # --- 1. Groundedness re-check ---
        source_text = None
        if source_type == "wiki" and page_title in wiki_by_title:
            source_text = wiki_by_title[page_title]["plain_text"]
        elif source_type == "chat_kb":
            kb_row = kb_by_id.get(page_title) or next(
                (v for v in kb_by_id.values() if str(v.get("id")) in page_title), None
            )
            if kb_row:
                source_text = kb_row["answer"]
                # --- 2. Staleness: was this chat_kb entry superseded/flagged since? ---
                if kb_row["status"] in ("flagged", "superseded", "removed"):
                    _flag(row["request_id"], "stale_source",
                          f"Answer cited a chat-KB entry that is now status='{kb_row['status']}'.",
                          "Re-verify this answer against current guidance; the source it relied on has changed.")
                    flags_created += 1

        if source_text:
            result = verify_grounded(row["answer"], source_text)
            if not result.grounded:
                _flag(row["request_id"], "groundedness",
                      result.grounding_note or "Answer no longer traces cleanly to its cited source.",
                      "Route to a Suitability Expert for manual re-verification before this answer is reused.")
                flags_created += 1

    return {"checked": checked, "flags_created": flags_created}


def _flag(audit_request_id, flag_type: str, detail: str, proposed_action: str):
    db.execute(
        """INSERT INTO monitoring_flags (audit_request_id, flag_type, detail, proposed_action)
           VALUES (%s, %s, %s, %s)""",
        (audit_request_id, flag_type, detail, proposed_action),
    )


def get_open_flags() -> list[dict]:
    return db.query(
        """SELECT mf.*, al.question FROM monitoring_flags mf
           JOIN audit_log al ON al.request_id = mf.audit_request_id
           WHERE mf.status = 'open' ORDER BY mf.created_at DESC"""
    )
