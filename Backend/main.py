"""RiskON 2026 backend — implements the decision flow from the strategy doc:
Wiki retrieval -> ambiguity/scope check -> confident answer, clarification,
or escalation to the right SME. Matches docs API contract / frontend
types.ts exactly (see models.py).
"""
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models import (
    AskRequest, AskResponse, Confidence, SourceRef, Escalation, Expert,
    FallbackContact, FeedbackRequest, FeedbackResponse,
    CaseMessageRequest, KnowledgeDecisionRequest,
)
from retrieval import get_retriever
from query_rewriter import get_query_rewriter
from reasoning import check_ambiguity, check_scope
from escalation import get_router
import audit
import workflow
from knowledge import draft_knowledge

app = FastAPI(title="RiskON Suitability Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tune based on eval_harness.py results against Dataset/evaluation_set.json —
# see README.md for how to re-run and re-tune this.
ANSWER_CONFIDENCE_THRESHOLD = 0.12
STRONG_ANSWER_CONFIDENCE_THRESHOLD = 0.18
MIN_SOURCE_TERM_COVERAGE = 0.8

# Confluence-style URL prefix, matching the real JB wiki URL pattern
# (https://wiki.juliusbaer.com/pages/viewpage.action?pageId=...) referenced
# in the challenge materials. Swap for the real page IDs once the real
# Wiki dump is ingested.
WIKI_URL_BASE = "https://wiki.juliusbaer.com/pages/viewpage.action?pageId="


def _page_url(page_id: str) -> str:
    # Deterministic fake pageId per page so links are stable across requests.
    return f"{WIKI_URL_BASE}{abs(hash(page_id)) % 900000000 + 100000000}"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    request_id = str(uuid.uuid4())
    retriever = get_retriever()
    query_rewriter = get_query_rewriter()
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

    rewrite = query_rewriter.rewrite(question, req.history)
    retrieval_query = " ".join([rewrite.query, *rewrite.keywords]).strip()
    # Downstream checks need the context resolved by the rewriter too. Keep the
    # original wording alongside it so jurisdiction/scope details cannot be lost.
    contextual_question = f"{question} {retrieval_query}".strip()
    if rewrite.used_llm:
        reasoning.append(f'Prepared the retrieval query as: "{rewrite.query}".')
    elif rewrite.fallback_reason not in {"no_history", "disabled"}:
        reasoning.append("Query rewriting was unavailable; used the original question safely.")

    if not rewrite.needs_retrieval:
        reasoning.append("The request is outside the Suitability Copilot's wealth-management scope.")
        response = AskResponse(
            request_id=request_id,
            status="out_of_scope",
            answer=(
                "This request is outside my scope. I can help with wealth-management "
                "suitability, compliance, client classification, products, and related policies."
            ),
            confidence=Confidence(answer_confidence=0.0, routing_confidence=0.0),
            sources=[],
            scope_flags=["out_of_scope"],
            reasoning=reasoning,
        )
        audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
        return response

    learned_match = workflow.retrieve_approved(retrieval_query)
    if learned_match:
        learned, learned_score = learned_match
        reasoning.append(
            f'Matched expert-approved knowledge: "{learned["title"]}" '
            f'(relevance {learned_score:.2f}).'
        )
        response = AskResponse(
            request_id=request_id,
            status="answered",
            answer=learned["answer"],
            confidence=Confidence(answer_confidence=min(0.95, 0.65 + learned_score / 3)),
            sources=[SourceRef(
                page_title=f'Expert Knowledge — {learned["title"]}',
                excerpt=learned["answer"][:320], fileType="doc",
            )],
            scope_flags=["expert_approved_knowledge"],
            reasoning=reasoning,
        )
        audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
        return response

    matches = retriever.retrieve(retrieval_query, top_k=3)
    reasoning.append(
        f"Searched the Suitability Wiki for: \"{rewrite.query}\"."
        if matches else f"Searched the Suitability Wiki for: \"{rewrite.query}\" — no page scored above zero relevance."
    )

    # --- No matching page at all: straight to escalation ---
    if not matches:
        routing = router.route(topic_tags=[], low_confidence=True, no_source_at_all=True)
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
                reason=routing.reason,
                fallback_contact=FallbackContact(name=routing.fallback_name, role=routing.fallback_role),
            ),
            reasoning=reasoning,
        )
        audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
        workflow.create_case(
            request_id, question, req.requester_id, req.requester_name,
            routing.expert_name, routing.tier,
        )
        return response

    top_page, top_score = matches[0]
    reasoning.append(f"Top match: \"{top_page.title}\" (relevance {top_score:.2f}).")

    # --- Ambiguity check: does this need clarification before we can answer? ---
    ambiguity = check_ambiguity(top_page, contextual_question)
    if ambiguity.needs_clarification:
        reasoning.append(
            "This page has multiple correct answers depending on context that wasn't "
            "provided — asking for clarification rather than guessing."
        )
        response = AskResponse(
            request_id=request_id,
            status="clarification_needed",
            confidence=Confidence(answer_confidence=0.3, routing_confidence=0.0),
            sources=[SourceRef(page_title=top_page.title, excerpt=retriever.excerpt(top_page, retrieval_query),
                                url=_page_url(top_page.id), fileType="link")],
            clarification_question=ambiguity.clarify_question,
            quick_replies=ambiguity.quick_replies,
            reasoning=reasoning,
        )
        audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
        return response

    # --- Scope check: does the top page actually cover the jurisdiction asked about? ---
    scope = check_scope(top_page, contextual_question)
    reasoning.append(scope.scope_note if scope.scope_note else "No scope/jurisdiction mismatch detected.")

    # --- Confidence gate: answer only if genuinely confident ---
    term_coverage = retriever.term_coverage(top_page, retrieval_query)
    grounded_enough = (
        top_score >= STRONG_ANSWER_CONFIDENCE_THRESHOLD
        or (
            top_score >= ANSWER_CONFIDENCE_THRESHOLD
            and term_coverage >= MIN_SOURCE_TERM_COVERAGE
        )
    )
    reasoning.append(f"The source explicitly covers {term_coverage:.0%} of the question's meaningful terms.")
    if grounded_enough:
        sources = [
            SourceRef(
                page_title=p.title,
                excerpt=retriever.excerpt(p, retrieval_query),
                url=_page_url(p.id),
                fileType="link",
            )
            for p, s in matches[:2] if s > 0
        ]
        answer = retriever.excerpt(top_page, retrieval_query)
        if scope.scope_note:
            answer = f"{answer} {scope.scope_note}"

        confidence_score = min(0.97, 0.55 + top_score)
        reasoning.append("Relevance and source-term coverage passed the answer gate — answering.")
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
    routing = router.route(topic_tags=top_page.topic_tags, low_confidence=True, no_source_at_all=False)
    reasoning.append("Relevance or source-term coverage did not pass the answer gate — escalating rather than guessing.")
    reasoning.append(f"Routed to {routing.expert_role} ({routing.tier}).")
    response = AskResponse(
        request_id=request_id,
        status="escalated",
        confidence=Confidence(answer_confidence=round(top_score, 2), routing_confidence=routing.routing_confidence),
        sources=[SourceRef(page_title=top_page.title, excerpt=retriever.excerpt(top_page, retrieval_query),
                            url=_page_url(top_page.id), fileType="link")],
        scope_flags=scope.scope_flags,
        escalation=Escalation(
            required=True,
            tier=routing.tier,
            expert=Expert(name=routing.expert_name, role=routing.expert_role, team=routing.expert_team),
            reason=routing.reason,
            fallback_contact=FallbackContact(name=routing.fallback_name, role=routing.fallback_role),
        ),
        reasoning=reasoning,
    )
    audit.log_request(request_id, question, req.context.model_dump(), response.model_dump())
    workflow.create_case(
        request_id, question, req.requester_id, req.requester_name,
        routing.expert_name, routing.tier,
    )
    return response


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest) -> FeedbackResponse:
    audit.log_resolution(req.request_id, req.resolved_by, req.final_answer, req.was_ai_correct)
    return FeedbackResponse(status="logged")


@app.get("/audit")
def get_audit():
    """Convenience endpoint for the frontend's Audit Trail page, or manual inspection."""
    return audit.all_records()


@app.get("/cases")
def get_cases(user_name: str = Query(...), view: str = Query("assigned", pattern="^(assigned|requested)$")):
    return workflow.list_cases(user_name, view)


@app.get("/users")
def get_users():
    router = get_router()
    return [
        {
            "id": sme["id"], "name": sme["name"], "role": sme["role"],
            "kind": "expert", "tier": sme["tier"],
        }
        for sme in router.smes
    ]


@app.post("/cases/{case_id}/messages")
def post_case_message(case_id: str, req: CaseMessageRequest):
    case = workflow.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Escalation case not found")
    message = workflow.add_message(
        case_id, req.sender_id, req.sender_name, req.sender_kind, req.content,
    )
    candidate = None
    if req.sender_kind == "expert":
        audit.log_resolution(case["request_id"], req.sender_name, req.content, False)
        draft = draft_knowledge(case["question"], req.content)
        candidate = workflow.save_candidate(case_id=case_id, **draft)
    return {"message": message, "knowledge_candidate": candidate}


@app.post("/knowledge-candidates/{candidate_id}/decision")
def decide_knowledge(candidate_id: str, req: KnowledgeDecisionRequest):
    result = workflow.decide_candidate(candidate_id, req.reviewer_name, req.decision)
    if result is None:
        raise HTTPException(status_code=404, detail="Pending knowledge candidate not found")
    return result
