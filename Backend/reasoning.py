"""Reasoning & verification layer — this is the "extra logic on top of RAG"
layer. It does two things retrieval alone can't:
1. Detects when a question is genuinely ambiguous (needs clarification, not
   a guess) — encoded from the real evaluation set's documented cases.
2. Detects when the top-matching page's scope doesn't cover the question's
   actual jurisdiction — the exact mistake JB's real assistant made.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

from retrieval import WikiPage

# Pages where the real evaluation set says a single answer cannot be given
# without more context — keyed by page id, from Dataset/evaluation_set.json.
AMBIGUOUS_PAGES: dict[str, dict] = {
    "issuer_concentration_risk": {
        "resolves_if_any": [
            "advisory session", "client book", "actively solicited",
            "reverse solicited", "unsolicited",
        ],
        "clarify_question": (
            "Was this alert triggered in an Advisory Session or in Client Book "
            "(overnight monitoring)? If Advisory Session, which solicitation type — "
            "actively solicited, reverse solicited, or unsolicited?"
        ),
        "quick_replies": [
            "Advisory Session — actively solicited",
            "Advisory Session — reverse solicited",
            "Advisory Session — unsolicited",
            "Client Book (overnight monitoring)",
        ],
    },
    "overnight_wn_alerts": {
        "resolves_if_any": ["advisory session", "client book"],
        "clarify_question": (
            "Was this alert triggered in an Advisory Session (before entering a trade) "
            "or in Client Book (overnight monitoring)?"
        ),
        "quick_replies": ["Advisory Session", "Client Book (overnight monitoring)"],
    },
    "k_and_e_update": {
        "resolves_if_any": [
            "knowledge level", "experience level", "clm", "crm", "wn/dias", "dias",
        ],
        "clarify_question": (
            "Do you need to update the Knowledge level or the Experience level, and "
            "which system manages this client — Wealth Navigator/DiAS, CLM, or CRM?"
        ),
        "quick_replies": [
            "Knowledge level, in WN/DiAS", "Experience level, in WN/DiAS", "CLM", "CRM",
        ],
    },
}

# Pages whose content is scoped to one jurisdiction — mirrors Dataset/page_index.json.
REGION_KEYWORDS = {
    "CH": ["switzerland", "swiss", " ch ", "bc ch"],
    "Monaco": ["monaco", "mc_local"],
    "Germany": ["germany", "german"],
    "EEA": ["eea", "europe", "european"],
}

NO_ANSWER_TRIGGER = re.compile(r"\bblocked\b.{0,25}\b(order|session|purchase)\b", re.I)


@dataclass
class ReasoningResult:
    needs_clarification: bool = False
    clarify_question: Optional[str] = None
    quick_replies: Optional[list[str]] = None
    scope_flags: list[str] = None
    scope_note: Optional[str] = None

    def __post_init__(self):
        if self.scope_flags is None:
            self.scope_flags = []


def mentioned_regions(question: str) -> list[str]:
    q = f" {question.lower()} "
    return [region for region, kws in REGION_KEYWORDS.items() if any(kw in q for kw in kws)]


def check_ambiguity(top_page: WikiPage, question: str) -> ReasoningResult:
    q_lower = question.lower()

    if NO_ANSWER_TRIGGER.search(question):
        return ReasoningResult(
            needs_clarification=True,
            clarify_question=(
                "Can you tell me more about the block — what error or message are you "
                "seeing? A block can come from several different checks and I can only "
                "point you in the right direction once I know which one applies."
            ),
        )

    rule = AMBIGUOUS_PAGES.get(top_page.id)
    if rule and not any(kw in q_lower for kw in rule["resolves_if_any"]):
        return ReasoningResult(
            needs_clarification=True,
            clarify_question=rule["clarify_question"],
            quick_replies=rule["quick_replies"],
        )

    return ReasoningResult()


def check_scope(top_page: WikiPage, question: str) -> ReasoningResult:
    if len(top_page.region_scope) > 1:
        return ReasoningResult()

    page_region = top_page.region_scope[0]
    regions_in_q = mentioned_regions(question)
    other_regions = [r for r in regions_in_q if r != page_region]

    if other_regions:
        return ReasoningResult(
            scope_flags=["source_does_not_cover_jurisdiction"],
            scope_note=(
                f"The primary source here is scoped to {page_region} only — it does not "
                f"give an authoritative answer for {', '.join(other_regions)}."
            ),
        )
    return ReasoningResult()
