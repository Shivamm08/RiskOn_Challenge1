from escalation import Router


def test_route_prefers_local_region_expert_before_broader_match():
    router = Router()

    result = router.route(
        topic_tags=["cross_border", "client_classification"],
        low_confidence=True,
        no_source_at_all=False,
        region="Monaco",
    )

    assert result.expert_name == "Anna Fischer"
    assert result.tier == "business_front_support"
    assert "Local expert match in Monaco" in result.reason


def test_route_expands_when_local_region_has_no_match():
    router = Router()

    result = router.route(
        topic_tags=["solicitation_type", "suitability_appropriateness"],
        low_confidence=True,
        no_source_at_all=False,
        region="Monaco",
    )

    assert result.tier in {"brm_suitability_lead", "business_front_support"}
    assert "No same-zone expert matched" in result.reason


def test_route_works_without_region_for_flat_fallback():
    router = Router()

    result = router.route(
        topic_tags=["client_classification"],
        low_confidence=True,
        no_source_at_all=False,
        region=None,
    )

    assert result.expert_name
    assert result.tier in {"suitability_champion", "business_front_support", "brm_suitability_lead"}


def test_route_returns_multiple_people_for_user_choice():
    router = Router()

    result = router.route(
        topic_tags=["cross_border", "client_classification"],
        low_confidence=True,
        no_source_at_all=False,
        region="Monaco",
    )

    assert len(result.experts) >= 3
    assert {expert["name"] for expert in result.experts} >= {result.expert_name}
