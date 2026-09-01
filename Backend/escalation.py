"""Escalation & routing layer — picks the right escalation tier and SME
using the synthetic SME dataset. Tier order and roles come from the real
1&2LoD support model (Dataset/README.md, and the official RiskON slide):
Wiki -> Suitability Champion -> Business Front Support -> BRM Suitability
Lead -> Suitability Expert.
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field

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
REGION_FALLBACK_ORDER = {
    "Monaco": ["Monaco", "EEA", "CH", "Germany"],
    "Germany": ["Germany", "EEA", "CH", "Monaco"],
    "CH": ["CH", "EEA", "Germany", "Monaco"],
    "EEA": ["EEA", "Germany", "CH", "Monaco"],
    "Other": ["Other", "EEA", "CH", "Germany", "Monaco"],
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
    experts: list[dict] = field(default_factory=list)


class Router:
    def __init__(self):
        with open(SMES_PATH) as f:
            self.smes = json.load(f)

    def _topic_candidates(self, topic_tags: list[str], min_tier_index: int = 0):
        scored = []
        for sme in self.smes:
            tier_idx = TIER_ORDER.index(sme["tier"]) if sme["tier"] in TIER_ORDER else 0
            if tier_idx < min_tier_index:
                continue
            overlap = len(set(sme["topic_tags"]) & set(topic_tags))
            if overlap > 0:
                scored.append((overlap, tier_idx, sme))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return scored

    def _region_priority(self, region: str | None) -> list[str]:
        if not region:
            return ["CH", "Germany", "Monaco", "EEA", "Other"]
        return REGION_FALLBACK_ORDER.get(region, [region, "EEA", "CH", "Germany", "Monaco", "Other"])

    def _pick_best_sme(self, candidates: list[tuple[int, int, dict]], region: str | None):
        if not candidates:
            return None

        ordered = []
        for overlap, tier_idx, sme in candidates:
            preferred = 0
            if region and region in sme.get("region_coverage", []):
                preferred = 0
            elif region:
                pref_order = self._region_priority(region)
                sme_regions = sme.get("region_coverage", [])
                region_rank = next((i for i, r in enumerate(pref_order) if r in sme_regions), len(pref_order))
                preferred = 1 + region_rank
            ordered.append((preferred, overlap, tier_idx, sme))

        ordered.sort(key=lambda x: (x[0], -x[1], x[2], -x[3].get("historical_resolutions", 0), x[3].get("avg_response_time_hours", 999)))
        return ordered[0][3]

    def _ranked_smes(self, topic_tags: list[str], region: str | None) -> list[dict]:
        topic_candidates = self._topic_candidates(topic_tags, min_tier_index=0)
        local_candidates = []
        if region:
            local_candidates = [item for item in topic_candidates if region in item[2].get("region_coverage", [])]
        candidate_pool = local_candidates or topic_candidates

        ordered = []
        for overlap, tier_idx, sme in candidate_pool:
            preferred = 0
            if region and region in sme.get("region_coverage", []):
                preferred = 0
            elif region:
                pref_order = self._region_priority(region)
                sme_regions = sme.get("region_coverage", [])
                region_rank = next((i for i, r in enumerate(pref_order) if r in sme_regions), len(pref_order))
                preferred = 1 + region_rank
            ordered.append((preferred, overlap, tier_idx, sme))

        ordered.sort(key=lambda x: (x[0], -x[1], x[2], -x[3].get("historical_resolutions", 0), x[3].get("avg_response_time_hours", 999)))
        return [sme for _, _, _, sme in ordered]

    def route(self, topic_tags: list[str], low_confidence: bool, no_source_at_all: bool, region: str | None = None) -> RoutingResult:
        # Hierarchical routing: first prefer SMEs in the same region/zone, then expand.
        topic_candidates = self._topic_candidates(topic_tags, min_tier_index=0)
        local_candidates = []
        if region:
            local_candidates = [item for item in topic_candidates if region in item[2].get("region_coverage", [])]

        ranked_smes = self._ranked_smes(topic_tags, region)
        chosen = ranked_smes[0] if ranked_smes else None

        options: list[dict] = []
        seen_names: set[str] = set()
        for sme in ranked_smes:
            if sme["name"] in seen_names:
                continue
            seen_names.add(sme["name"])
            options.append(sme)
            if len(options) >= 3:
                break
        if len(options) < 3:
            for sme in self.smes:
                if sme["name"] in seen_names:
                    continue
                seen_names.add(sme["name"])
                options.append(sme)
                if len(options) >= 3:
                    break

        if not chosen:
            fallback_pool = [s for s in self.smes if s["tier"] == "suitability_champion"]
            chosen = fallback_pool[0] if fallback_pool else self.smes[0]
            overlap = 0
        else:
            overlap = len(set(chosen["topic_tags"]) & set(topic_tags)) if topic_tags else 0

        tier = chosen["tier"]
        topics_str = ", ".join(topic_tags) if topic_tags else "this topic"
        region_note = f" in {region}" if region else ""
        if local_candidates:
            reason_prefix = f"Local expert match{region_note}"
        elif region:
            reason_prefix = f"No same-zone expert matched, so expanded to broader coverage{region_note}"
        else:
            reason_prefix = "Matched the most relevant SME"

        if no_source_at_all:
            reason = (
                f"No wiki guidance was retrieved for this question, so it can't be answered "
                f"from the connected knowledge sources. {reason_prefix}: routed to {TIER_TEAM_LABEL[tier]} "
                f"based on subject-matter overlap on {topics_str}."
            )
        else:
            reason = (
                f"The retrieved guidance wasn't clear-cut enough to answer confidently. {reason_prefix}: "
                f"routed to {chosen['role']} based on topic overlap on {topics_str} "
                f"({overlap} matching tag(s)) and the support model."
            )

        higher = [s for s in self.smes if TIER_ORDER.index(s["tier"]) > TIER_ORDER.index(tier)]
        fallback = higher[0] if higher else next((s for s in self.smes if s["id"] != chosen["id"]), chosen)

        routing_confidence = min(0.95, 0.5 + 0.15 * overlap)
        if region and not local_candidates:
            routing_confidence = max(0.2, routing_confidence - 0.1)

        return RoutingResult(
            tier=tier,
            expert_name=chosen["name"],
            expert_role=chosen["role"],
            expert_team=chosen.get("team", TIER_TEAM_LABEL[tier]),
            reason=reason,
            fallback_name=fallback["name"],
            fallback_role=fallback["role"],
            routing_confidence=routing_confidence,
            experts=[
                {
                    "name": sme["name"],
                    "role": sme["role"],
                    "team": sme.get("team", TIER_TEAM_LABEL.get(sme["tier"], sme["tier"])),
                }
                for sme in options
            ],
        )


_router: Router | None = None


def get_router() -> Router:
    global _router
    if _router is None:
        _router = Router()
    return _router
