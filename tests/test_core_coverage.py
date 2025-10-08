"""Tests for core modules to increase coverage."""

import pytest
from app.core.config import get_settings
from app.core.security import hash_password, verify_password, create_refresh_token, hash_refresh_token, verify_refresh_token, create_token_family


class TestCoreCoverage:
    """Test core modules for coverage."""

    def test_get_settings(self):
        """Test get_settings function."""
        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, 'environment')
        assert hasattr(settings, 'database_url')

    def test_password_hashing(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_refresh_token_creation(self):
        """Test refresh token creation."""
        token = create_refresh_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_hashing(self):
        """Test refresh token hashing."""
        token = "test_token"
        hashed = hash_refresh_token(token)
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex length

    def test_refresh_token_verification(self):
        """Test refresh token verification."""
        token = "test_token"
        hashed = hash_refresh_token(token)
        assert verify_refresh_token(token, hashed)
        assert not verify_refresh_token("wrong_token", hashed)

    def test_token_family_creation(self):
        """Test token family creation."""
        family = create_token_family()
        assert isinstance(family, str)
        assert len(family) > 0
