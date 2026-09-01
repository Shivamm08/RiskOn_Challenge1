"""Escalation & routing layer — the real algorithm behind what the frontend
has been showing as mock reasoning. Scores every expert on four factors and
explains the winner in plain language:
  1. Geographic distance from the RM's region (closer preferred, not absolute)
  2. Rank (5-tier ladder: suitability_champion -> ... -> brm_suitability_lead)
  3. Current availability (are they in roughly 08:00-18:00 local right now?)
  4. Track record (favorability_score + accuracy_pct)
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

import db

RANK_ORDER = ["suitability_champion", "business_front_support", "expert",
              "senior_expert", "brm_suitability_lead"]
RANK_LABEL = {
    "suitability_champion": "Suitability Champion", "business_front_support": "Business Front Support",
    "expert": "Expert", "senior_expert": "Senior Expert", "brm_suitability_lead": "BRM Suitability Lead",
}

# Region tiers, ordered by typical distance from a CH-based RM. Used to expand
# the search outward: branch -> country -> nearby region -> everywhere else.
REGION_DISTANCE = {
    "Branch": 0, "CH": 1, "EU/UK": 2, "EU": 2, "MEA": 3, "APAC": 4, "Japan": 4, "US": 3,
}

# booking_centre from the API contract -> the RM's own approximate region tier.
BOOKING_CENTRE_TO_REGION = {"CH": "CH", "Monaco": "CH", "Germany": "EU",
                            "EEA": "EU", "Other": "CH"}


@dataclass
class RoutingResult:
    tier: str
    expert_id: str
    expert_name: str
    expert_role: str
    expert_office: str
    expert_local_time: str
    reason: str
    fallback_name: str
    fallback_role: str
    routing_confidence: float
    candidates_considered: list[dict]


def _local_time_str(utc_offset_minutes: int) -> str:
    now = datetime.now(timezone.utc) + timedelta(minutes=utc_offset_minutes)
    return now.strftime("%H:%M local")


def _is_available(utc_offset_minutes: int) -> bool:
    now = datetime.now(timezone.utc) + timedelta(minutes=utc_offset_minutes)
    return 8 <= now.hour < 18


def _score(expert: dict, rm_region: str, topic_tags: list[str]) -> tuple[float, dict]:
    rank_idx = RANK_ORDER.index(expert["rank"]) if expert["rank"] in RANK_ORDER else 0
    tier_distance = REGION_DISTANCE.get(expert["region_tier"], 5)
    rm_distance = REGION_DISTANCE.get(rm_region, 1)
    distance_from_rm = abs(tier_distance - rm_distance)
    available = _is_available(expert["utc_offset_minutes"])

    topic_overlap = 0  # experts table doesn't carry topic_tags in this schema version;
    # kept as a hook — set from a future experts.specialty-keyword match if desired.

    score = (
        -distance_from_rm * 12
        + rank_idx * 10
        + (15 if available else -10)
        + float(expert["favorability_score"]) / 10
        + float(expert["accuracy_pct"]) / 10
    )
    breakdown = {
        "name": expert["name"], "office": expert["office"], "rank": expert["rank"],
        "distance_from_rm": distance_from_rm, "available": available, "score": round(score, 1),
    }
    return score, breakdown


class Router:
    def route(self, topic_tags: list[str], booking_centre: str | None, no_source_at_all: bool) -> RoutingResult:
        experts = db.query("SELECT * FROM experts ORDER BY name")
        if not experts:
            raise RuntimeError("No experts found — run database/seed_database.py first.")

        rm_region = BOOKING_CENTRE_TO_REGION.get(booking_centre or "Other", "CH")
        scored = [(_score(e, rm_region, topic_tags), e) for e in experts]
        scored.sort(key=lambda x: x[0][0], reverse=True)

        (top_score, top_breakdown), top_expert = scored[0]

        reasons = []
        if top_breakdown["distance_from_rm"] == 0:
            reasons.append(f"in the same region tier as the request")
        else:
            reasons.append(f"the closest available match after expanding the search outward")
        reasons.append(f"rank: {RANK_LABEL[top_expert['rank']]}")
        reasons.append(
            "currently within working hours" if top_breakdown["available"]
            else "outside typical working hours, but still the best overall match"
        )
        reasons.append(
            f"{float(top_expert['favorability_score']):.0f}/100 favorability, "
            f"{float(top_expert['accuracy_pct']):.0f}% accuracy on past answers"
        )

        prefix = (
            "No wiki or knowledge-base guidance matched this question. "
            if no_source_at_all else
            "The retrieved guidance wasn't clear-cut enough to answer confidently. "
        )
        reason = prefix + f"Recommending {top_expert['name']} — " + "; ".join(reasons) + "."

        # Fallback: this expert's supervisor, or next-best scored candidate.
        fallback = None
        if top_expert.get("supervisor_id"):
            sup_rows = [e for e in experts if str(e["id"]) == str(top_expert["supervisor_id"])]
            fallback = sup_rows[0] if sup_rows else None
        if not fallback and len(scored) > 1:
            fallback = scored[1][1]
        if not fallback:
            fallback = top_expert

        routing_confidence = min(0.97, max(0.35, 0.5 + top_score / 100))

        return RoutingResult(
            tier=top_expert["rank"],
            expert_id=str(top_expert["id"]),
            expert_name=top_expert["name"],
            expert_role=RANK_LABEL[top_expert["rank"]],
            expert_office=top_expert["office"],
            expert_local_time=_local_time_str(top_expert["utc_offset_minutes"]),
            reason=reason,
            fallback_name=fallback["name"],
            fallback_role=RANK_LABEL[fallback["rank"]],
            routing_confidence=round(routing_confidence, 2),
            candidates_considered=[b for (_, b), _ in scored[:5]],
        )


_router: Router | None = None


def get_router() -> Router:
    global _router
    if _router is None:
        _router = Router()
    return _router
