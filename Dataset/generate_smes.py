"""Generates a synthetic SME/org dataset for the expert-routing layer.
Schema matches docs/RiskON_2026_Challenge1_TeamStrategy.docx Section 3.2.
Run: python generate_smes.py
"""
import json
import random

random.seed(42)  # reproducible output — change/remove once tuning for real

TIERS = ["suitability_champion", "business_front_support", "brm_suitability_lead", "suitability_expert"]
ROLE_BY_TIER = {
    "suitability_champion": "Suitability Champion",
    "business_front_support": "Business Front Support",
    "brm_suitability_lead": "BRM Suitability Lead",
    "suitability_expert": "Suitability Expert",
}
TEAM_BY_TIER = {
    "suitability_champion": "Front Office",
    "business_front_support": "Business Front Support",
    "brm_suitability_lead": "BRM Suitability Leads",
    "suitability_expert": "Legal / Compliance / GPS",
}
# Weighted so the org pyramid looks realistic: more people at the lower tiers.
TIER_WEIGHTS = [0.4, 0.3, 0.2, 0.1]

TOPICS = [
    "overview", "cip", "k_and_e", "client_classification", "cross_border",
    "finsa_scope", "mifid_scope", "cpr_alerts", "concentration_risk", "saa",
    "monitoring", "solicitation_type", "own", "structured_products",
    "execution_only", "kid_requirements", "suitability_appropriateness",
]
REGIONS = ["CH", "Monaco", "Germany", "EEA"]

FIRST_NAMES = ["Anna", "Marco", "Lena", "David", "Sophie", "Lukas", "Elena", "Noah",
               "Mia", "Jonas", "Clara", "Felix", "Nina", "Tobias", "Laura", "Simon",
               "Julia", "Max", "Sara", "Leon"]
LAST_NAMES = ["Keller", "Frei", "Meier", "Studer", "Weber", "Huber", "Baumann",
              "Steiner", "Fischer", "Graf", "Widmer", "Brunner", "Roth", "Wyss",
              "Zimmermann", "Egli", "Suter", "Marti", "Kunz", "Moser"]


def pick_tier():
    return random.choices(TIERS, weights=TIER_WEIGHTS, k=1)[0]


def generate_sme(i: int) -> dict:
    tier = pick_tier()
    n_topics = {"suitability_champion": 2, "business_front_support": 3,
                "brm_suitability_lead": 3, "suitability_expert": 2}[tier]
    return {
        "id": f"sme_{i:03d}",
        "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
        "role": ROLE_BY_TIER[tier],
        "tier": tier,
        "team": TEAM_BY_TIER[tier],
        "region_coverage": random.sample(REGIONS, k=random.randint(1, 2)),
        "topic_tags": random.sample(TOPICS, k=n_topics),
        "seniority_years": random.randint(1, 18),
        "avg_response_time_hours": round(random.uniform(0.5, 12), 1),
        "historical_resolutions": random.randint(0, 80),
        "bio": "",  # fill in manually for the 2-3 people used in the live demo
    }


def ensure_topic_coverage(smes: list[dict]) -> list[dict]:
    """Every topic must have at least one owner — patch any gaps."""
    covered = {t for s in smes for t in s["topic_tags"]}
    missing = [t for t in TOPICS if t not in covered]
    for t in missing:
        target = random.choice([s for s in smes if s["tier"] in ("brm_suitability_lead", "suitability_expert")])
        target["topic_tags"].append(t)
    return smes


def main():
    smes = [generate_sme(i) for i in range(1, 21)]
    smes = ensure_topic_coverage(smes)
    with open("synthetic_smes.json", "w") as f:
        json.dump(smes, f, indent=2)
    print(f"Wrote {len(smes)} SME profiles to synthetic_smes.json")


if __name__ == "__main__":
    main()
