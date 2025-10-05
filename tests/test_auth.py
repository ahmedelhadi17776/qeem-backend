"""Tests for authentication system."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.schemas.auth import UserRegisterRequest, UserLoginRequest
from app.services.user_service import UserService
from app.core.security import create_access_token


client = TestClient(app)


class TestUserRegistration:
    """Test user registration functionality."""

    def test_register_user_success(self, db_session: Session):
        """Test successful user registration."""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": unique_email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        if response.status_code != 201:
            print(
                f"Error response: {response.status_code} - {response.json()}")

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_user_duplicate_email(self, db_session: Session):
        """Test registration with duplicate email."""
        import uuid
        unique_email = f"duplicate_test_{uuid.uuid4().hex[:8]}@example.com"

        # First registration should succeed
        user_data = {
            "email": unique_email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201

        # Second registration with same email should fail
        user_data2 = {
            "email": unique_email,
            "password": "password456",
            "first_name": "Test2",
            "last_name": "User2"
        }

        response2 = client.post("/api/v1/auth/register", json=user_data2)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]

    def test_register_user_invalid_email(self, db_session: Session):
        """Test registration with invalid email."""
        user_data = {
            "email": "invalid-email",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    def test_register_user_short_password(self, db_session: Session):
        """Test registration with short password."""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": unique_email,
            "password": "short",
            "first_name": "Test",
            "last_name": "User"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error

    def test_register_user_missing_fields(self, db_session: Session):
        """Test registration with missing required fields."""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user_data = {
            "email": unique_email,
            "password": "password123"
            # Missing first_name and last_name
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login functionality."""

    def test_login_success(self, db_session: Session):
        """Test successful user login."""
        import uuid
        unique_email = f"login_test_{uuid.uuid4().hex[:8]}@example.com"

        # First register a user
        user_data = {
            "email": unique_email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        register_response = client.post(
            "/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Then login with the same credentials
        login_data = {
            "email": unique_email,
            "password": "password123"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] > 0

    def test_login_invalid_email(self, db_session: Session):
        """Test login with non-existent email."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_invalid_password(self, db_session: Session):
        """Test login with incorrect password."""
        import uuid
        unique_email = f"invalid_pass_test_{uuid.uuid4().hex[:8]}@example.com"

        # First register a user
        user_data = {
            "email": unique_email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        register_response = client.post(
            "/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Then try to login with wrong password
        login_data = {
            "email": unique_email,
            "password": "wrongpassword"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_inactive_user(self, db_session: Session):
        """Test login with inactive user."""
        import uuid
        unique_email = f"inactive_{uuid.uuid4().hex[:8]}@example.com"
        # Create inactive user
        user_service = UserService(db_session)
        user_data = UserRegisterRequest(
            email=unique_email,
            password="password123",
            first_name="Inactive",
            last_name="User"
        )
        user = user_service.create_user(user_data)

        # Deactivate user
        user.is_active = False
        db_session.commit()

        login_data = {
            "email": unique_email,
            "password": "password123"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]


class TestProtectedEndpoints:
    """Test protected endpoint functionality."""

    def test_get_current_user_success(self, db_session: Session):
        """Test getting current user with valid token."""
        import uuid
        unique_email = f"protected_test_{uuid.uuid4().hex[:8]}@example.com"

        # First register a user
        user_data = {
            "email": unique_email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        register_response = client.post(
            "/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Then login to get token
        login_data = {
            "email": unique_email,
            "password": "password123"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == unique_email

    def test_get_current_user_no_token(self, db_session: Session):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # No authorization header

    def test_get_current_user_invalid_token(self, db_session: Session):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_get_current_user_expired_token(self, db_session: Session):
        """Test accessing protected endpoint with expired token."""
        from datetime import timedelta
        # Create expired token
        expired_token = create_access_token(
            subject="1",
            extra_claims={"email": "test@example.com"},
            expires_delta=timedelta(seconds=-1)  # Expired 1 second ago
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_rate_calculation_with_auth(self, db_session: Session):
        """Test rate calculation with authentication."""
        import uuid
        unique_email = f"rate_test_{uuid.uuid4().hex[:8]}@example.com"

        # First register a user
        user_data = {
            "email": unique_email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        register_response = client.post(
            "/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Then login to get token
        login_data = {
            "email": unique_email,
            "password": "password123"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Calculate rate with authentication
        rate_data = {
            "project_type": "web_development",
            "project_complexity": "moderate",
            "estimated_hours": 40,
            "experience_years": 2,
            "skills_count": 3,
            "location": "Cairo, Egypt",
            "client_region": "egypt",
            "urgency": "normal"
        }

        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/rates/calculate",
                               json=rate_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "minimum_rate" in data
        assert "competitive_rate" in data
        assert "premium_rate" in data
        assert data["currency"] == "EGP"

    def test_rate_calculation_without_auth(self, db_session: Session):
        """Test rate calculation without authentication should fail."""
        rate_data = {
            "project_type": "web_development",
            "project_complexity": "moderate",
            "estimated_hours": 40,
            "experience_years": 2,
            "skills_count": 3,
            "location": "Cairo, Egypt",
            "client_region": "egypt",
            "urgency": "normal"
        }

        response = client.post("/api/v1/rates/calculate", json=rate_data)

        assert response.status_code == 403  # No authorization header


class TestUserProfile:
    """Test user profile functionality."""

    def test_get_profile_success(self, db_session: Session):
        """Test getting user profile with valid token."""
        import uuid
        unique_email = f"profile_test_{uuid.uuid4().hex[:8]}@example.com"

        # First register a user
        user_data = {
            "email": unique_email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        register_response = client.post(
            "/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Then login to get token
        login_data = {
            "email": unique_email,
            "password": "password123"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Get profile
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users/profile", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == unique_email
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"

    def test_update_profile_success(self, db_session: Session):
        """Test updating user profile."""
        import uuid
        unique_email = f"update_test_{uuid.uuid4().hex[:8]}@example.com"

        # First register a user
        user_data = {
            "email": unique_email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        register_response = client.post(
            "/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Then login to get token
        login_data = {
            "email": unique_email,
            "password": "password123"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Update profile
        profile_data = {
            "bio": "Experienced web developer",
            "profession": "Full Stack Developer",
            "experience_years": 5,
            "city": "Cairo",
            "hourly_rate_preference": 400
        }

        headers = {"Authorization": f"Bearer {token}"}
        response = client.put("/api/v1/users/profile",
                              json=profile_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == profile_data["bio"]
        assert data["profession"] == profile_data["profession"]
        assert data["experience_years"] == profile_data["experience_years"]
        assert data["city"] == profile_data["city"]
        assert data["hourly_rate_preference"] == profile_data["hourly_rate_preference"]

    def test_get_profile_without_auth(self, db_session: Session):
        """Test getting profile without authentication."""
        response = client.get("/api/v1/users/profile")

        assert response.status_code == 403  # No authorization header

    def test_update_profile_without_auth(self, db_session: Session):
        """Test updating profile without authentication."""
        profile_data = {
            "bio": "Test bio"
        }

        response = client.put("/api/v1/users/profile", json=profile_data)

        assert response.status_code == 403  # No authorization header


class TestRateHistory:
    """Test rate calculation history functionality."""

    def test_get_rate_history_success(self, db_session: Session):
        """Test getting rate calculation history."""
        import uuid
        unique_email = f"history_test_{uuid.uuid4().hex[:8]}@example.com"

        # First register a user
        user_data = {
            "email": unique_email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }

        register_response = client.post(
            "/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Then login to get token
        login_data = {
            "email": unique_email,
            "password": "password123"
        }

        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Get rate history
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/rates/history", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_rate_history_without_auth(self, db_session: Session):
        """Test getting rate history without authentication."""
        response = client.get("/api/v1/rates/history")

        assert response.status_code == 403  # No authorization header
