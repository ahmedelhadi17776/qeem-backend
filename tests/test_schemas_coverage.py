"""Tests for schemas to increase coverage."""

import pytest
from app.schemas.auth import UserRegisterRequest, UserLoginRequest
from app.schemas.market import MarketStatisticsResponse, MarketStatisticsQuery, MarketStatisticsItem, MarketTrendsQuery, MarketTrendsResponse
from app.schemas.rates import RateRequest, RateResponse, RateHistoryResponse


class TestSchemasCoverage:
    """Test schemas for coverage."""

    def test_user_register_request(self):
        """Test UserRegisterRequest schema."""
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }
        user = UserRegisterRequest(**user_data)
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"

    def test_user_login_request(self):
        """Test UserLoginRequest schema."""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        login = UserLoginRequest(**login_data)
        assert login.email == "test@example.com"
        assert login.password == "password123"

    def test_market_statistics_response(self):
        """Test MarketStatisticsResponse schema."""
        stats_data = {
            "items": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
            "cached": False
        }
        stats = MarketStatisticsResponse(**stats_data)
        assert stats.total == 0
        assert stats.limit == 20

    def test_market_statistics_query(self):
        """Test MarketStatisticsQuery schema."""
        query_data = {
            "project_type": "web_development",
            "location": "Cairo"
        }
        query = MarketStatisticsQuery(**query_data)
        assert query.project_type == "web_development"
        assert query.location == "Cairo"

    def test_market_statistics_item(self):
        """Test MarketStatisticsItem schema."""
        from datetime import date
        item_data = {
            "date": date(2024, 1, 1),
            "period_type": "weekly",
            "project_type": "web_development",
            "location": "Cairo",
            "average_rate": 45000.0,
            "median_rate": 40000.0,
            "min_rate": 30000.0,
            "max_rate": 60000.0
        }
        item = MarketStatisticsItem(**item_data)
        assert item.project_type == "web_development"
        assert item.average_rate == 45000.0

    def test_market_trends_query(self):
        """Test MarketTrendsQuery schema."""
        query_data = {
            "project_type": "web_development",
            "location": "Cairo",
            "window": 12
        }
        query = MarketTrendsQuery(**query_data)
        assert query.project_type == "web_development"
        assert query.window == 12

    def test_market_trends_response(self):
        """Test MarketTrendsResponse schema."""
        response_data = {
            "points": [],
            "cached": False
        }
        response = MarketTrendsResponse(**response_data)
        assert response.points == []
        assert response.cached == False

    def test_rate_request(self):
        """Test RateRequest schema."""
        rate_data = {
            "project_type": "web_development",
            "project_complexity": "moderate",
            "estimated_hours": 100,
            "experience_years": 5,
            "skills_count": 10,
            "location": "Cairo"
        }
        rate = RateRequest(**rate_data)
        assert rate.project_type == "web_development"
        assert rate.experience_years == 5

    def test_rate_response(self):
        """Test RateResponse schema."""
        response_data = {
            "minimum_rate": 50.0,
            "competitive_rate": 75.0,
            "premium_rate": 100.0,
            "currency": "EGP",
            "method": "rule_based"
        }
        response = RateResponse(**response_data)
        assert response.minimum_rate == 50.0
        assert response.competitive_rate == 75.0

    def test_rate_history_response(self):
        """Test RateHistoryResponse schema."""
        response_data = {
            "items": []
        }
        response = RateHistoryResponse(**response_data)
        assert response.items == []
