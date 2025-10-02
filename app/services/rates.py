"""Rule-based rate calculation service.

This module contains a simple, transparent rule engine to compute
minimum, competitive, and premium hourly rates in EGP based on:
 - Project complexity
 - Years of experience
 - Number of relevant skills
 - Client region (Egypt, MENA, Europe, USA, Global)
 - Urgency (normal vs rush)
"""

from typing import Dict

from ..schemas.rates import RateRequest


def _base_rate_for_project_type(project_type: str) -> float:
    """Return a baseline hourly rate in EGP by project type.

    Values are placeholders to enable the MVP and should be replaced later
    with market-backed figures or ML predictions.
    """
    baselines: Dict[str, float] = {
        "web_development": 250.0,
        "mobile_development": 280.0,
        "design": 220.0,
        "writing": 180.0,
        "marketing": 200.0,
        "consulting": 300.0,
        "data_analysis": 260.0,
        "other": 200.0,
    }
    return baselines.get(project_type, 200.0)


def _complexity_multiplier(complexity: str) -> float:
    return {
        "simple": 0.9,
        "moderate": 1.0,
        "complex": 1.2,
        "enterprise": 1.4,
    }.get(complexity, 1.0)


def _experience_multiplier(years: int) -> float:
    if years < 1:
        return 0.8
    if years < 3:
        return 0.9
    if years < 5:
        return 1.0
    if years < 8:
        return 1.15
    return 1.3


def _skills_multiplier(skills_count: int) -> float:
    if skills_count <= 2:
        return 0.95
    if skills_count <= 5:
        return 1.0
    if skills_count <= 8:
        return 1.08
    return 1.15


def _client_region_multiplier(region: str) -> float:
    return {
        "egypt": 1.0,
        "mena": 1.1,
        "europe": 1.8,
        "usa": 2.0,
        "global": 1.6,
    }.get(region, 1.0)


def _urgency_multiplier(urgency: str) -> float:
    return 1.15 if urgency == "rush" else 1.0


def calculate_compensation_tiers(payload: RateRequest) -> Dict[str, float]:
    """Compute hourly rate tiers in EGP.

    Strategy:
      base = project_type baseline
      x complexity x experience x skills x client_region x urgency
      tiers: min=0.8x, competitive=1.0x, premium=1.3x (rounded to whole EGP)
    """
    base = _base_rate_for_project_type(payload.project_type)
    value = (
        base
        * _complexity_multiplier(payload.project_complexity)
        * _experience_multiplier(int(payload.experience_years))
        * _skills_multiplier(int(payload.skills_count))
        * _client_region_multiplier(payload.client_region)
        * _urgency_multiplier(payload.urgency)
    )

    # ensure a sensible lower bound
    minimum_rate = round(max(80.0, value * 0.8))
    competitive_rate = round(value)
    premium_rate = round(value * 1.3)

    return {
        "minimum_rate": float(minimum_rate),
        "competitive_rate": float(competitive_rate),
        "premium_rate": float(premium_rate),
        "currency": "EGP",
        "method": "rule_based",
    }
