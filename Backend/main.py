"""RiskON 2026 backend — the complete, database-backed version.

Decision flow: normalize input (acronym expansion) -> hybrid retrieve
(wiki + chat KB) -> ambiguity check -> scope check -> confidence gate ->
answer (with self-verification) OR escalate (real geo/rank/timezone
routing, creates a real message thread) OR clarify. Every request is
logged to Postgres. No LLM anywhere in this path — purely extractive,
by design (see chat history: reliability > polish for a live demo).
"""
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import (
    AskRequest, AskResponse, Confidence, SourceRef, Escalation, Expert,
    FallbackContact, FeedbackRequest, FeedbackResponse,
)
from retrieval import get_retriever
from reasoning import normalize_question, check_ambiguity, check_scope, verify_grounded, _load_ambiguous_ids
from escalation import get_router, RANK_LABEL
import audit
import monitoring
import db

app = FastAPI(title="RiskON Suitability Copilot API — v2 (Supabase-backed)")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

ANSWER_CONFIDENCE_THRESHOLD = 0.10
_ambiguous_ids_cache = None


def _ambiguous_ids():
    global _ambiguous_ids_cache
    if _ambiguous_ids_cache is None:
        _ambiguous_ids_cache = _load_ambiguous_ids()
    return _ambiguous_ids_cache


def _get_or_create_rm(name: str | None) -> str:
    """Returns an rm id, creating a minimal row if this name hasn't been seen."""
    if not name:
        name = "Guest RM"
    rows = db.query("SELECT id FROM rms WHERE name = %s", (name,))
    if rows:
        return str(rows[0]["id"])
    row = db.execute_returning(
        "INSERT INTO rms (name, office) VALUES (%s, %s) RETURNING id", (name, "Unknown"),
    )
    return str(row["id"])


def _create_escalation_thread(rm_id: str, question: str, context: dict, routing, candidates: list[dict]) -> str:
    row = db.execute_returning(
        """INSERT INTO messages (rm_id, expert_id, question, context, routing_reasoning, routing_candidates, status)
           VALUES (%s, %s, %s, %s, %s, %s, 'pending') RETURNING id""",
        (rm_id, routing.expert_id, question, __import__("json").dumps(context),
         routing.reason, __import__("json").dumps(candidates)),
    )
    message_id = str(row["id"])
    db.execute(
        "INSERT INTO message_events (message_id, sender, body) VALUES (%s, 'rm', %s)",
        (message_id, question),
    )
    return message_id


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/auth/available-users")
def available_users():
    """Real, database-backed login identities — replaces any hardcoded
    frontend user list. RMs are all login-able (they're the primary users);
    experts are login-able only where has_login = true (the curated subset
    that lets the RM -> expert -> answer -> KB-publish demo flow work
    end-to-end, per the routing preference above)."""
    rms = db.query("SELECT id, name, office FROM rms ORDER BY name")
    experts = db.query(
        "SELECT id, name, office, rank FROM experts WHERE has_login = true ORDER BY name"
    )
    return {
        "rms": [{"id": str(r["id"]), "name": r["name"], "role": f"RM, {r['office']}", "kind": "rm"} for r in rms],
        "experts": [{"id": str(e["id"]), "name": e["name"], "role": f"{RANK_LABEL.get(e['rank'], e['rank'])}, {e['office']}", "kind": "expert"} for e in experts],
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    request_id = str(uuid.uuid4())
    retriever = get_retriever()
    router = get_router()
    rm_id = _get_or_create_rm(req.rm_name)

    reasoning: list[str] = []
    raw_question = req.question.strip()
    if not raw_question:
        response = AskResponse(request_id=request_id, status="clarification_needed",
                                clarification_question="What would you like to ask?",
                                reasoning=["Empty question received."])
        audit.log_request(request_id, rm_id, raw_question, req.context.model_dump(), response.model_dump())
        return response

    # --- Input normalization (acronym expansion) ---
    expanded_question, expansions = normalize_question(raw_question)
    if expansions:
        reasoning.append(f"Expanded acronyms before retrieval: {', '.join(expansions)}.")

    matches = retriever.retrieve(expanded_question, top_k=3)
    reasoning.append(
        f"Searched the Suitability Wiki and chat-based knowledge base for: \"{raw_question}\"."
        if matches else "No document scored above zero relevance across either knowledge source."
    )

    context_dict = req.context.model_dump()
    booking_centre = req.context.booking_centre

    # --- No match at all: escalate ---
    if not matches:
        routing = router.route(topic_tags=[], booking_centre=booking_centre, no_source_at_all=True)
        message_id = _create_escalation_thread(rm_id, raw_question, context_dict, routing, routing.candidates_considered)
        reasoning.append(routing.reason)
        response = AskResponse(
            request_id=request_id, status="escalated",
            confidence=Confidence(answer_confidence=0.05, routing_confidence=routing.routing_confidence),
            sources=[], scope_flags=["wiki_gap:no_matching_guidance"],
            escalation=Escalation(
                required=True, tier=routing.tier,
                expert=Expert(name=routing.expert_name, role=routing.expert_role, team=routing.expert_office),
                reason=routing.reason,
                fallback_contact=FallbackContact(name=routing.fallback_name, role=routing.fallback_role),
            ),
            reasoning=reasoning,
        )
        audit.log_request(request_id, rm_id, raw_question, context_dict, response.model_dump())
        return response

    top_doc, top_score = matches[0]
    reasoning.append(f"Top match: \"{top_doc.title}\" ({top_doc.source_type}, relevance {top_score:.2f}).")

    # --- Ambiguity check ---
    ambiguity = check_ambiguity([d for d, s in matches[:2]], raw_question, _ambiguous_ids())
    if ambiguity.needs_clarification:
        reasoning.append("Multiple correct answers exist depending on unstated context — asking rather than guessing.")
        response = AskResponse(
            request_id=request_id, status="clarification_needed",
            confidence=Confidence(answer_confidence=0.3, routing_confidence=0.0),
            sources=[SourceRef(page_title=top_doc.title, excerpt=retriever.excerpt(top_doc, raw_question),
                                url=top_doc.source_url, fileType="link", source_type=top_doc.source_type,
                                trust_score=top_doc.trust_score)],
            clarification_question=ambiguity.clarify_question, quick_replies=ambiguity.quick_replies,
            reasoning=reasoning,
        )
        audit.log_request(request_id, rm_id, raw_question, context_dict, response.model_dump())
        return response

    # --- Scope check ---
    scope = check_scope(top_doc, raw_question)
    reasoning.append(scope.scope_note or "No scope/jurisdiction mismatch detected.")

    # --- Confidence gate ---
    if top_score >= ANSWER_CONFIDENCE_THRESHOLD:
        answer = retriever.excerpt(top_doc, raw_question)
        if scope.scope_note:
            answer = f"{answer} {scope.scope_note}"

        # --- Self-verification: does the answer actually trace to the source? ---
        source_text_for_check = top_doc.extra.get("answer", top_doc.text) if top_doc.source_type == "chat_kb" else top_doc.text
        grounding = verify_grounded(answer, source_text_for_check)
        if not grounding.grounded:
            reasoning.append(f"Self-verification failed: {grounding.grounding_note}")
            routing = router.route(topic_tags=top_doc.topic_tags, booking_centre=booking_centre, no_source_at_all=False)
            message_id = _create_escalation_thread(rm_id, raw_question, context_dict, routing, routing.candidates_considered)
            response = AskResponse(
                request_id=request_id, status="escalated",
                confidence=Confidence(answer_confidence=round(top_score, 2), routing_confidence=routing.routing_confidence),
                sources=[SourceRef(page_title=top_doc.title, excerpt=answer, url=top_doc.source_url,
                                    fileType="link", source_type=top_doc.source_type, trust_score=top_doc.trust_score)],
                scope_flags=scope.scope_flags + ["failed_self_verification"],
                escalation=Escalation(
                    required=True, tier=routing.tier,
                    expert=Expert(name=routing.expert_name, role=routing.expert_role, team=routing.expert_office),
                    reason=routing.reason,
                    fallback_contact=FallbackContact(name=routing.fallback_name, role=routing.fallback_role),
                ),
                reasoning=reasoning,
            )
            audit.log_request(request_id, rm_id, raw_question, context_dict, response.model_dump())
            return response

        sources = [
            SourceRef(page_title=d.title, excerpt=retriever.excerpt(d, raw_question), url=d.source_url,
                       fileType="link", source_type=d.source_type, trust_score=d.trust_score)
            for d, s in matches[:2] if s > 0
        ]
        confidence_score = min(0.97, 0.55 + top_score)
        reasoning.append(f"Relevance {top_score:.2f} ≥ threshold ({ANSWER_CONFIDENCE_THRESHOLD}); self-verification passed. Answering.")
        response = AskResponse(
            request_id=request_id, status="answered", answer=answer,
            confidence=Confidence(answer_confidence=round(confidence_score, 2), routing_confidence=0.0),
            sources=sources, scope_flags=scope.scope_flags, reasoning=reasoning,
        )
        audit.log_request(request_id, rm_id, raw_question, context_dict, response.model_dump())
        return response

    # --- Not confident: escalate, real thread created ---
    routing = router.route(topic_tags=top_doc.topic_tags, booking_centre=booking_centre, no_source_at_all=False)
    message_id = _create_escalation_thread(rm_id, raw_question, context_dict, routing, routing.candidates_considered)
    reasoning.append(f"Relevance {top_score:.2f} < threshold ({ANSWER_CONFIDENCE_THRESHOLD}); escalating rather than guessing.")
    reasoning.append(routing.reason)
    response = AskResponse(
        request_id=request_id, status="escalated",
        confidence=Confidence(answer_confidence=round(top_score, 2), routing_confidence=routing.routing_confidence),
        sources=[SourceRef(page_title=top_doc.title, excerpt=retriever.excerpt(top_doc, raw_question),
                            url=top_doc.source_url, fileType="link", source_type=top_doc.source_type,
                            trust_score=top_doc.trust_score)],
        scope_flags=scope.scope_flags,
        escalation=Escalation(
            required=True, tier=routing.tier,
            expert=Expert(name=routing.expert_name, role=routing.expert_role, team=routing.expert_office),
            reason=routing.reason,
            fallback_contact=FallbackContact(name=routing.fallback_name, role=routing.fallback_role),
        ),
        reasoning=reasoning,
    )
    audit.log_request(request_id, rm_id, raw_question, context_dict, response.model_dump())
    return response


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest) -> FeedbackResponse:
    audit.log_resolution(req.request_id, req.resolved_by, req.final_answer, req.was_ai_correct)
    return FeedbackResponse(status="logged")


@app.get("/audit")
def get_audit(limit: int = 200):
    return audit.all_records(limit)


@app.get("/eval/summary")
def eval_summary():
    """Evaluation-dashboard data — aggregate accuracy/escalation stats."""
    return audit.eval_summary()


@app.post("/monitor/run")
def run_monitor(limit: int = 100):
    """Triggers a monitoring pass — the brief's second deliverable. Re-checks
    recent answers for groundedness and source staleness, writes findings to
    monitoring_flags. Run manually via this endpoint, or wire to a cron."""
    return monitoring.run_monitoring_pass(limit=limit)


@app.get("/monitor/flags")
def get_flags():
    return monitoring.get_open_flags()


@app.post("/kb/reload")
def reload_kb():
    """Call after a new kb_entries row is published so it becomes searchable
    without restarting the process."""
    get_retriever(force_reload=True)
    return {"status": "reloaded"}


# ---------------------------------------------------------------------------
# Messages — RM <-> expert escalation threads
# ---------------------------------------------------------------------------

@app.get("/messages")
def list_messages(rm_id: str = None, expert_id: str = None):
    """Only shows what's relevant to the requesting user — pass rm_id for an
    RM's own sent escalations, or expert_id for an expert's own inbox.
    Neither is real auth, just correct scoping — matches the 'RM should
    only see their own chats' requirement."""
    if expert_id:
        rows = db.query(
            """SELECT m.*, r.name as rm_name, e.name as expert_name FROM messages m
               JOIN rms r ON r.id = m.rm_id JOIN experts e ON e.id = m.expert_id
               WHERE m.expert_id = %s ORDER BY m.created_at DESC""",
            (expert_id,),
        )
    elif rm_id:
        rows = db.query(
            """SELECT m.*, r.name as rm_name, e.name as expert_name FROM messages m
               JOIN rms r ON r.id = m.rm_id JOIN experts e ON e.id = m.expert_id
               WHERE m.rm_id = %s ORDER BY m.created_at DESC""",
            (rm_id,),
        )
    else:
        rows = db.query(
            """SELECT m.*, r.name as rm_name, e.name as expert_name FROM messages m
               JOIN rms r ON r.id = m.rm_id JOIN experts e ON e.id = m.expert_id
               ORDER BY m.created_at DESC"""
        )
    return rows


@app.get("/messages/{message_id}")
def get_message(message_id: str):
    rows = db.query(
        """SELECT m.*, r.name as rm_name, e.name as expert_name, e.email as expert_email
           FROM messages m JOIN rms r ON r.id = m.rm_id JOIN experts e ON e.id = m.expert_id
           WHERE m.id = %s""",
        (message_id,),
    )
    if not rows:
        return {"error": "not found"}
    thread = db.query(
        "SELECT * FROM message_events WHERE message_id = %s ORDER BY created_at ASC",
        (message_id,),
    )
    return {**rows[0], "thread": thread}


class ReplyRequest(BaseModel):
    body: str


@app.post("/messages/{message_id}/reply")
def reply_to_message(message_id: str, req: ReplyRequest):
    """Expert answers an escalated question. Sets status to 'answered' and
    fires a notification back to the RM who asked."""
    db.execute(
        "INSERT INTO message_events (message_id, sender, body) VALUES (%s, 'expert', %s)",
        (message_id, req.body),
    )
    db.execute("UPDATE messages SET status = 'answered' WHERE id = %s", (message_id,))
    rows = db.query("SELECT rm_id, question FROM messages WHERE id = %s", (message_id,))
    if rows:
        db.execute(
            """INSERT INTO notifications (recipient_kind, recipient_id, kind, title, body, related_message_id)
               VALUES ('rm', %s, 'message', 'Your question was answered', %s, %s)""",
            (rows[0]["rm_id"], rows[0]["question"][:100], message_id),
        )
    return {"status": "replied"}


@app.post("/messages/{message_id}/publish-to-kb")
def publish_to_kb(message_id: str):
    """The 'add this answer to the knowledge base?' -> Yes flow. Creates a
    real kb_entries row, marks the message as added_to_kb, notifies everyone,
    and hot-reloads the retriever so it's searchable immediately."""
    rows = db.query("SELECT * FROM messages WHERE id = %s", (message_id,))
    if not rows:
        return {"error": "not found"}
    msg = rows[0]
    events = db.query(
        "SELECT body FROM message_events WHERE message_id = %s AND sender = 'expert' ORDER BY created_at DESC LIMIT 1",
        (message_id,),
    )
    if not events:
        return {"error": "no expert reply yet — nothing to publish"}
    answer = events[0]["body"]

    kb_row = db.execute_returning(
        """INSERT INTO kb_entries (question, answer, contributed_by, source_message_id, status)
           VALUES (%s, %s, %s, %s, 'published') RETURNING id""",
        (msg["question"], answer, msg["expert_id"], message_id),
    )
    db.execute("UPDATE messages SET status = 'added_to_kb' WHERE id = %s", (message_id,))
    db.execute(
        """INSERT INTO notifications (recipient_kind, recipient_id, kind, title, body, related_kb_entry_id)
           VALUES ('all', NULL, 'kb_update', 'New info added to the knowledge base', %s, %s)""",
        (msg["question"][:100], kb_row["id"]),
    )
    get_retriever(force_reload=True)
    return {"status": "published", "kb_entry_id": str(kb_row["id"])}


@app.post("/messages/{message_id}/decline-kb")
def decline_kb(message_id: str):
    db.execute("UPDATE messages SET status = 'declined_kb' WHERE id = %s", (message_id,))
    return {"status": "declined"}


# ---------------------------------------------------------------------------
# Chat-based knowledge base — browsing + Reddit-thread-style review
# ---------------------------------------------------------------------------

@app.get("/kb/entries")
def list_kb_entries():
    return db.query(
        """SELECT k.*, e.name as contributor_name FROM kb_entries k
           JOIN experts e ON e.id = k.contributed_by
           WHERE k.status != 'removed' ORDER BY k.created_at DESC"""
    )


@app.get("/kb/entries/{entry_id}")
def get_kb_entry(entry_id: str):
    rows = db.query(
        """SELECT k.*, e.name as contributor_name FROM kb_entries k
           JOIN experts e ON e.id = k.contributed_by WHERE k.id = %s""",
        (entry_id,),
    )
    if not rows:
        return {"error": "not found"}
    reviews = db.query(
        """SELECT r.*, e.name as reviewer_name FROM kb_entry_reviews r
           JOIN experts e ON e.id = r.reviewer_id WHERE r.kb_entry_id = %s
           ORDER BY r.created_at ASC""",
        (entry_id,),
    )
    return {**rows[0], "reviews": reviews}


class ReviewRequest(BaseModel):
    reviewer_id: str
    verdict: str  # "endorse" or "flag"
    note: str = ""


@app.post("/kb/entries/{entry_id}/review")
def review_kb_entry(entry_id: str, req: ReviewRequest):
    """The Reddit-thread-style right/wrong-with-a-reason flow. One review
    per expert per entry (re-reviewing updates their prior verdict+note).
    The database trigger (schema.sql) automatically updates trust_score and
    the contributor's favorability_score on endorse; a flag routes to
    'flagged' status for supervisor review."""
    db.execute(
        """INSERT INTO kb_entry_reviews (kb_entry_id, reviewer_id, verdict, note)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (kb_entry_id, reviewer_id) DO UPDATE SET
             verdict = excluded.verdict, note = excluded.note, created_at = now()""",
        (entry_id, req.reviewer_id, req.verdict, req.note),
    )
    return {"status": "reviewed"}


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@app.get("/notifications")
def list_notifications(kind: str = None, recipient_id: str = None):
    """kind = 'rm' or 'expert'. Returns that user's own notifications plus
    any 'all'-recipient ones (like KB updates)."""
    if kind and recipient_id:
        return db.query(
            """SELECT * FROM notifications WHERE recipient_kind = 'all'
               OR (recipient_kind = %s AND recipient_id = %s)
               ORDER BY created_at DESC LIMIT 50""",
            (kind, recipient_id),
        )
    return db.query("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 50")


class MarkReadRequest(BaseModel):
    notification_id: str


@app.post("/notifications/mark-read")
def mark_read(req: MarkReadRequest):
    db.execute("UPDATE notifications SET read = true WHERE id = %s", (req.notification_id,))
    return {"status": "ok"}
