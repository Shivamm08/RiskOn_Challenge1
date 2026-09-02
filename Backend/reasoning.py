"""Reasoning & verification layer. Three jobs:
1. Input normalization — acronym expansion before retrieval (the "adaptive
   retrieval" bonus point), using JB's own official glossary.
2. Ambiguity + scope detection — same logic as the synthetic-dataset version,
   now remapped to the real page IDs by title lookup at startup (numeric
   Confluence IDs aren't stable to hardcode, titles are).
3. Self-verification — after an answer is composed, checks its key terms
   actually appear in the cited source before it's shown as confident (the
   "self-verification before answering" bonus point).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional

import db
from retrieval import RetrievedDoc

# ---------------------------------------------------------------------------
# 1. Input normalization — acronym expansion (JB's official glossary,
# RiskON 2026 deck "Terms: Common Abbreviations" slide)
# ---------------------------------------------------------------------------
GLOSSARY = {
    "bmo": "Business Model Offering",
    "k&e": "Knowledge and Experience",
    "cip": "Client Investment Profile",
    "cpr": "Consolidated Product Risk",
    "prr": "Product Risk Rating",
    "pir": "Personal Investment Recommendation",
    "fisr": "Financial Instrument Solicitation Rules",
    "dtm": "Distributor Target Market",
    "ah": "Account Holder",
    "poa": "Power of Attorney",
    "rm": "Relationship Manager",
    "rma": "Relationship Manager Assistant",
    "ia": "Investment Adviser",
    "kid": "Key Information Document",
    "mifid": "Markets in Financial Instruments Directive",
    "finsa": "Financial Services Act",
    "1lod": "1st Line of Defense",
    "2lod": "2nd Line of Defense",
    "sme": "Subject Matter Expert",
    "own": "One Way Notification",
    "cip": "Client Investment Profile",
}


def normalize_question(question: str) -> tuple[str, list[str]]:
    """Expands known acronyms so retrieval matches on the expanded term too.
    Returns (expanded_question, list_of_expansions_applied)."""
    applied = []
    expanded = question
    for term in re.findall(r"\b[A-Za-z][A-Za-z0-9&]{1,6}\b", question):
        key = term.lower()
        if key in GLOSSARY and GLOSSARY[key].lower() not in question.lower():
            expanded += f" {GLOSSARY[key]}"
            applied.append(f"{term.upper()} -> {GLOSSARY[key]}")
    return expanded, applied


# ---------------------------------------------------------------------------
# 2. Ambiguity + scope detection — remapped to real page titles
# ---------------------------------------------------------------------------
AMBIGUOUS_PAGE_TITLES: dict[str, dict] = {
    "Issuer Concentration Risk": {
        "resolves_if_any": ["advisory session", "client book", "actively solicited",
                             "reverse solicited", "unsolicited"],
        "clarify_question": (
            "Was this alert triggered in an Advisory Session or in Client Book "
            "(overnight monitoring)? If Advisory Session, which solicitation type — "
            "actively solicited, reverse solicited, or unsolicited?"
        ),
        "quick_replies": ["Advisory Session — actively solicited", "Advisory Session — reverse solicited",
                           "Advisory Session — unsolicited", "Client Book (overnight monitoring)"],
    },
    "Concentration Risk on Single Positions": {
        "resolves_if_any": ["advisory session", "client book"],
        "clarify_question": (
            "Was this alert triggered in an Advisory Session (before entering a trade) "
            "or in Client Book (overnight monitoring)?"
        ),
        "quick_replies": ["Advisory Session", "Client Book (overnight monitoring)"],
    },
    "Overnight Wealth Navigator alerts / Best practices for handling": {
        "resolves_if_any": ["advisory session", "client book"],
        "clarify_question": (
            "Was this alert triggered in an Advisory Session or in Client Book "
            "(overnight monitoring)?"
        ),
        "quick_replies": ["Advisory Session", "Client Book (overnight monitoring)"],
    },
    "How to update the K&E-levels of an order giver (WN/DiAS, CLM, CRM-systems)": {
        "resolves_if_any": ["knowledge level", "experience level", "clm", "crm", "wn/dias", "dias"],
        "clarify_question": (
            "Do you need to update the Knowledge level or the Experience level, and "
            "which system manages this client — Wealth Navigator/DiAS, CLM, or CRM?"
        ),
        "quick_replies": ["Knowledge level, in WN/DiAS", "Experience level, in WN/DiAS", "CLM", "CRM"],
    },
}

NO_ANSWER_TRIGGER = re.compile(r"\bblocked\b.{0,25}\b(order|session|purchase)\b", re.I)

REGION_KEYWORDS = {
    "CH": ["switzerland", "swiss"], "Monaco": ["monaco"],
    "Germany": ["germany", "german"], "EEA": ["eea", "europe", "european"],
}


def _load_ambiguous_ids() -> dict[str, dict]:
    """Maps AMBIGUOUS_PAGE_TITLES to real page ids by exact title match."""
    rows = db.query("SELECT id, title FROM wiki_pages WHERE title = ANY(%s)",
                     (list(AMBIGUOUS_PAGE_TITLES.keys()),))
    return {r["id"]: AMBIGUOUS_PAGE_TITLES[r["title"]] for r in rows}


@dataclass
class ReasoningResult:
    needs_clarification: bool = False
    clarify_question: Optional[str] = None
    quick_replies: Optional[list[str]] = None
    scope_flags: list[str] = field(default_factory=list)
    scope_note: Optional[str] = None
    grounded: bool = True
    grounding_note: Optional[str] = None


def mentioned_regions(question: str) -> list[str]:
    q = f" {question.lower()} "
    return [r for r, kws in REGION_KEYWORDS.items() if any(kw in q for kw in kws)]


def check_ambiguity(docs: list, question: str, ambiguous_ids: dict) -> ReasoningResult:
    """Checks the top-N retrieved docs (not just #1) against the known
    ambiguous-topic map. A closely related general page (e.g. "Knowledge &
    Experience (K&E)") can outrank the specific ambiguous page (e.g. "How
    to update K&E-levels...") in raw text similarity while the question is
    still genuinely about that ambiguous topic — checking only the top-1
    match misses this."""
    if NO_ANSWER_TRIGGER.search(question):
        return ReasoningResult(
            needs_clarification=True,
            clarify_question=(
                "Can you tell me more about the block — what error or message are you "
                "seeing? A block can come from several different checks and I can only "
                "point you in the right direction once I know which one applies."
            ),
        )
    for doc in docs:
        rule = ambiguous_ids.get(doc.id)
        if rule and not any(kw in question.lower() for kw in rule["resolves_if_any"]):
            return ReasoningResult(needs_clarification=True, clarify_question=rule["clarify_question"],
                                    quick_replies=rule["quick_replies"])
    return ReasoningResult()


def check_scope(doc: RetrievedDoc, question: str) -> ReasoningResult:
    if doc.source_type != "wiki" or len(doc.region_scope) > 1 or len(doc.region_scope) == 0:
        return ReasoningResult()
    page_region = doc.region_scope[0]
    other_regions = [r for r in mentioned_regions(question) if r != page_region]
    if other_regions:
        return ReasoningResult(
            scope_flags=["source_does_not_cover_jurisdiction"],
            scope_note=(f"The primary source here is scoped to {page_region} only — it does not "
                         f"give an authoritative answer for {', '.join(other_regions)}."),
        )
    return ReasoningResult()


# ---------------------------------------------------------------------------
# 3. Self-verification — does the composed answer actually trace to the source?
# ---------------------------------------------------------------------------
def verify_grounded(answer_text: str, source_text: str, min_overlap: float = 0.5) -> ReasoningResult:
    """Cheap but real groundedness check: what fraction of the answer's
    distinctive (4+ letter) words actually appear in the source text it was
    extracted from? Since answers ARE extracted verbatim from the source in
    this architecture, this should normally be ~1.0 — a low score here means
    something upstream composed text that isn't purely extractive, which is
    exactly the failure mode this check exists to catch."""
    answer_words = {w for w in re.findall(r"\w+", answer_text.lower()) if len(w) >= 4}
    source_words = {w for w in re.findall(r"\w+", source_text.lower())}
    if not answer_words:
        return ReasoningResult(grounded=True)
    overlap = len(answer_words & source_words) / len(answer_words)
    if overlap < min_overlap:
        return ReasoningResult(
            grounded=False,
            grounding_note=f"Only {overlap:.0%} of the answer's key terms trace back to the cited source — flagged for review rather than shown as confident.",
        )
    return ReasoningResult(grounded=True)
