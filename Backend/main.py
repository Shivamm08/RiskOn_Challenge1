"""RiskON 2026 backend — implements the decision flow from the strategy doc:
Wiki retrieval -> ambiguity/scope check -> confident answer, clarification,
or escalation to the right SME. Matches docs API contract / frontend
types.ts exactly (see models.py).
"""
import sys
import os
import uuid
from html import escape
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from models import (
    AskRequest, AskResponse, Confidence, SourceRef, Escalation, Expert,
    FallbackContact, FeedbackRequest, FeedbackResponse,
)
from retrieval import get_retriever
from reasoning import check_ambiguity, check_scope
from escalation import get_router
from llm_client import answer_with_context, is_insufficient_evidence
import audit

app = FastAPI(title="RiskON Suitability Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tune based on eval_harness.py results against Dataset/evaluation_set.json —
# see README.md for how to re-run and re-tune this.
ANSWER_CONFIDENCE_THRESHOLD = 0.04


@app.get("/health")
def health():
    retriever = get_retriever()
    return {"status": "ok", "wiki_pages": len(retriever.pages), "wiki_dir": str(retriever.wiki_dir)}


@app.get("/wiki/{page_id}", response_class=HTMLResponse)
def local_wiki_page(page_id: str):
    """Serve a competition Wiki export page locally for offline citations."""
    if not page_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid Wiki page ID")
    retriever = get_retriever()
    path = Path(retriever.wiki_dir) / f"{page_id}.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Wiki page not found")
    body = path.read_text(encoding="utf-8", errors="replace")
    title = next((p.title for p in retriever.pages if p.id == page_id), f"Wiki page {page_id}")
    return HTMLResponse(
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{escape(title)}</title>"
        "<style>body{font:15px/1.55 Arial,sans-serif;max-width:1000px;margin:32px auto;padding:0 24px;color:#172b4d}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd2d8;padding:8px;vertical-align:top}"
        "img,ac\\:image{max-width:100%}h1,h2,h3{color:#1b365d}</style></head><body>"
        f"<p><strong>Local competition Wiki export - page {page_id}</strong></p>{body}</body></html>"
    )


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    request_id = str(uuid.uuid4())
    retriever = get_retriever()
    router = get_router()

    reasoning: list[str] = []
    question = req.question.strip()

    if not question:
        response = AskResponse(
            request_id=request_id,
            status="clarification_needed",
            clarification_question="What would you like to ask?",
            reasoning=["Empty question received."],
        )
        audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
        return response

    matches = retriever.retrieve(question, top_k=3)
    reasoning.append(
        f"Searched the Suitability Wiki for: \"{question}\"."
        if matches else f"Searched the Suitability Wiki for: \"{question}\" — no page scored above zero relevance."
    )

    # --- No matching page at all: straight to escalation ---
    if not matches:
        routing = router.route(topic_tags=[], low_confidence=True, no_source_at_all=True, region=req.context.booking_centre)
        reasoning.append("No wiki page was retrieved above the relevance threshold for this question.")
        reasoning.append(f"Escalating to {routing.expert_role} ({routing.tier}).")
        response = AskResponse(
            request_id=request_id,
            status="escalated",
            confidence=Confidence(answer_confidence=0.05, routing_confidence=routing.routing_confidence),
            sources=[],
            scope_flags=["wiki_gap:no_matching_guidance"],
            escalation=Escalation(
                required=True,
                tier=routing.tier,
                expert=Expert(name=routing.expert_name, role=routing.expert_role, team=routing.expert_team),
                experts=[
                    Expert(name=entry["name"], role=entry["role"], team=entry["team"])
                    for entry in routing.experts
                ],
                reason=routing.reason,
                fallback_contact=FallbackContact(name=routing.fallback_name, role=routing.fallback_role),
            ),
            reasoning=reasoning,
        )
        audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
        return response

    top_page, top_score = matches[0]
    reasoning.append(f"Top match: \"{top_page.title}\" (relevance {top_score:.2f}).")

    # --- Ambiguity check: does this need clarification before we can answer? ---
    ambiguity = check_ambiguity(top_page, question)
    if ambiguity.needs_clarification:
        reasoning.append(
            "This page has multiple correct answers depending on context that wasn't "
            "provided — asking for clarification rather than guessing."
        )
        response = AskResponse(
            request_id=request_id,
            status="clarification_needed",
            confidence=Confidence(answer_confidence=0.3, routing_confidence=0.0),
            sources=[SourceRef(page_title=top_page.title, excerpt=retriever.excerpt(top_page, question),
                                url=top_page.url, fileType="link")],
            clarification_question=ambiguity.clarify_question,
            quick_replies=ambiguity.quick_replies,
            reasoning=reasoning,
        )
        audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
        return response

    # --- Scope check: does the top page actually cover the jurisdiction asked about? ---
    scope = check_scope(top_page, question)
    reasoning.append(scope.scope_note if scope.scope_note else "No scope/jurisdiction mismatch detected.")

    # --- Confidence gate: answer only if genuinely confident ---
    if top_score >= ANSWER_CONFIDENCE_THRESHOLD:
        sources = [
            SourceRef(
                page_title=p.title,
                excerpt=retriever.excerpt(p, question),
                url=p.url,
                fileType="link",
            )
            for p, s in matches[:2] if s > 0
        ]
        history = [
            {"role": turn.role, "content": turn.content}
            for turn in req.conversation
        ]
        retrieved_pages = [p for p, _ in matches[:5]]
        answer = answer_with_context(question, retrieved_pages, conversation_history=history)
        if is_insufficient_evidence(answer):
            routing = router.route(
                topic_tags=top_page.topic_tags,
                low_confidence=True,
                no_source_at_all=False,
                region=req.context.booking_centre,
            )
            reasoning.append("The retrieved sources were not strong enough to support a grounded answer, so the request was escalated.")
            reasoning.append(f"Routed to {routing.expert_role} ({routing.tier}).")
            response = AskResponse(
                request_id=request_id,
                status="escalated",
                confidence=Confidence(answer_confidence=round(top_score, 2), routing_confidence=routing.routing_confidence),
                sources=sources,
                scope_flags=scope.scope_flags,
                escalation=Escalation(
                    required=True,
                    tier=routing.tier,
                    expert=Expert(name=routing.expert_name, role=routing.expert_role, team=routing.expert_team),
                    experts=[
                        Expert(name=entry["name"], role=entry["role"], team=entry["team"])
                        for entry in routing.experts
                    ],
                    reason=routing.reason,
                    fallback_contact=FallbackContact(name=routing.fallback_name, role=routing.fallback_role),
                ),
                reasoning=reasoning,
            )
            audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
            return response

        if scope.scope_note:
            answer = f"{answer} {scope.scope_note}"

        confidence_score = min(0.97, 0.55 + top_score)
        reasoning.append(f"Relevance {top_score:.2f} is above the answer threshold ({ANSWER_CONFIDENCE_THRESHOLD}) — answering with grounded source support.")
        response = AskResponse(
            request_id=request_id,
            status="answered",
            answer=answer,
            confidence=Confidence(answer_confidence=round(confidence_score, 2), routing_confidence=0.0),
            sources=sources,
            scope_flags=scope.scope_flags,
            reasoning=reasoning,
        )
        audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
        return response

    # --- Not confident enough: escalate, but show what was checked ---
    routing = router.route(
        topic_tags=top_page.topic_tags,
        low_confidence=True,
        no_source_at_all=False,
        region=req.context.booking_centre,
    )
    reasoning.append(f"Relevance {top_score:.2f} is below the answer threshold ({ANSWER_CONFIDENCE_THRESHOLD}) — escalating rather than guessing.")
    reasoning.append(f"Routed to {routing.expert_role} ({routing.tier}).")
    response = AskResponse(
        request_id=request_id,
        status="escalated",
        confidence=Confidence(answer_confidence=round(top_score, 2), routing_confidence=routing.routing_confidence),
        sources=[SourceRef(page_title=top_page.title, excerpt=retriever.excerpt(top_page, question),
                            url=top_page.url, fileType="link")],
        scope_flags=scope.scope_flags,
        escalation=Escalation(
            required=True,
            tier=routing.tier,
            expert=Expert(name=routing.expert_name, role=routing.expert_role, team=routing.expert_team),
            experts=[
                Expert(name=entry["name"], role=entry["role"], team=entry["team"])
                for entry in routing.experts
            ],
            reason=routing.reason,
            fallback_contact=FallbackContact(name=routing.fallback_name, role=routing.fallback_role),
        ),
        reasoning=reasoning,
    )
    audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
    return response


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest) -> FeedbackResponse:
    audit.log_resolution(req.request_id, req.resolved_by, req.final_answer, req.was_ai_correct)
    return FeedbackResponse(status="logged")


@app.get("/audit")
def get_audit():
    """Convenience endpoint for the frontend's Audit Trail page, or manual inspection."""
    return audit.all_records()
