"""Escalation & routing layer — picks the right escalation tier and SME
using the synthetic SME dataset. Tier order and roles come from the real
1&2LoD support model (Dataset/README.md, and the official RiskON slide):
Wiki -> Suitability Champion -> Business Front Support -> BRM Suitability
Lead -> Suitability Expert.
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass

DATASET_DIR = os.environ.get("DATASET_DIR", os.path.join(os.path.dirname(__file__), "..", "Dataset"))
SMES_PATH = os.path.join(DATASET_DIR, "synthetic_smes.json")

TIER_ORDER = [
    "suitability_champion", "business_front_support", "brm_suitability_lead", "suitability_expert",
]
TIER_TEAM_LABEL = {
    "suitability_champion": "Front Office",
    "business_front_support": "Business Front Support",
    "brm_suitability_lead": "BRM Suitability Leads",
    "suitability_expert": "Legal / Compliance / GPS",
}


@dataclass
class RoutingResult:
    tier: str
    expert_name: str
    expert_role: str
    expert_team: str
    reason: str
    fallback_name: str
    fallback_role: str
    routing_confidence: float


class Router:
    def __init__(self):
        with open(SMES_PATH) as f:
            self.smes = json.load(f)

    def _candidates_for_topic(self, topic_tags: list[str], min_tier_index: int = 0):
        scored = []
        for sme in self.smes:
            tier_idx = TIER_ORDER.index(sme["tier"]) if sme["tier"] in TIER_ORDER else 0
            if tier_idx < min_tier_index:
                continue
            overlap = len(set(sme["topic_tags"]) & set(topic_tags))
            if overlap > 0:
                scored.append((overlap, tier_idx, sme))
        # Prefer more topic overlap, then lower tier (start as low as reasonably possible).
        scored.sort(key=lambda x: (-x[0], x[1]))
        return scored

    def route(self, topic_tags: list[str], low_confidence: bool, no_source_at_all: bool) -> RoutingResult:
        # Genuinely unmatched questions (no wiki page at all) skip straight past the
        # self-serve tier to a human who can at least point in the right direction.
        min_tier = 0
        candidates = self._candidates_for_topic(topic_tags, min_tier)

        if not candidates:
            # No topic-tag match at all — fall back to the generic first human tier.
            fallback_pool = [s for s in self.smes if s["tier"] == "suitability_champion"]
            chosen = fallback_pool[0] if fallback_pool else self.smes[0]
            overlap = 0
        else:
            overlap, _, chosen = candidates[0]

        tier = chosen["tier"]
        topics_str = ", ".join(topic_tags) if topic_tags else "this topic"
        if no_source_at_all:
            reason = (
                f"No wiki guidance was retrieved for this question, so it can't be answered "
                f"from the connected knowledge sources. Routed to {TIER_TEAM_LABEL[tier]} "
                f"based on subject-matter overlap on {topics_str}."
            )
        else:
            reason = (
                f"The retrieved guidance wasn't clear-cut enough to answer confidently. "
                f"Routed to {chosen['role']} based on topic overlap on {topics_str} "
                f"({overlap} matching tag(s)) and their tier in the support model."
            )

        # Fallback contact: next tier up, or a different person in the same tier.
        higher = [s for s in self.smes if TIER_ORDER.index(s["tier"]) > TIER_ORDER.index(tier)]
        fallback = higher[0] if higher else next((s for s in self.smes if s["id"] != chosen["id"]), chosen)

        routing_confidence = min(0.95, 0.5 + 0.15 * overlap)

        return RoutingResult(
            tier=tier,
            expert_name=chosen["name"],
            expert_role=chosen["role"],
            expert_team=chosen.get("team", TIER_TEAM_LABEL[tier]),
            reason=reason,
            fallback_name=fallback["name"],
            fallback_role=fallback["role"],
            routing_confidence=routing_confidence,
        )


_router: Router | None = None


def get_router() -> Router:
    global _router
    if _router is None:
        _router = Router()
    return _router
