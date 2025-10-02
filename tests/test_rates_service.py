"""Unit tests for rates service multipliers and tier calculations."""

from app.services.rates import (
    _base_rate_for_project_type,
    _complexity_multiplier,
    _experience_multiplier,
    _skills_multiplier,
    _client_region_multiplier,
    _urgency_multiplier,
)


def test_base_rate_defaults():
    assert _base_rate_for_project_type("web_development") > 0
    assert _base_rate_for_project_type("unknown") == 200.0


def test_complexity_multiplier_ordering():
    assert _complexity_multiplier(
        "simple") < _complexity_multiplier("moderate")
    assert _complexity_multiplier(
        "complex") < _complexity_multiplier("enterprise")


def test_experience_multiplier_monotonic():
    assert _experience_multiplier(0) < _experience_multiplier(2)
    assert _experience_multiplier(3) <= _experience_multiplier(5)
    assert _experience_multiplier(7) < _experience_multiplier(10)


def test_skills_multiplier_steps():
    assert _skills_multiplier(1) < _skills_multiplier(4)
    assert _skills_multiplier(6) <= _skills_multiplier(8)
    assert _skills_multiplier(9) <= _skills_multiplier(12)


def test_client_region_multiplier_scale():
    assert _client_region_multiplier(
        "egypt") < _client_region_multiplier("usa")
    assert _client_region_multiplier(
        "mena") <= _client_region_multiplier("global")


def test_urgency_multiplier():
    assert _urgency_multiplier("normal") == 1.0
    assert _urgency_multiplier("rush") > 1.0
