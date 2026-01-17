"""
Feature tests for user registration API endpoint.

These tests hit real HTTP endpoints with real database, verifying
user-visible behavior from the API consumer's perspective.
"""
import pytest
from rest_framework import status


class TestRegistrationEndpoint_SuccessfulRegistration:
    """Tests successful registration via API."""

    @pytest.mark.django_db
    def test_returns_201_on_successful_registration(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "newuser@example.com",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_returns_user_id_in_response(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "newuser@example.com",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert "user_id" in response.data
        assert response.data["user_id"] is not None

    @pytest.mark.django_db
    def test_returns_email_in_response(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "newuser@example.com",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert response.data["email"] == "newuser@example.com"

    @pytest.mark.django_db
    def test_does_not_return_password_in_response(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "newuser@example.com",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert "password" not in response.data


class TestRegistrationEndpoint_ValidationErrors:
    """Tests validation error responses."""

    @pytest.mark.django_db
    def test_returns_400_for_invalid_email(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "not-valid-email",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data["errors"]

    @pytest.mark.django_db
    def test_returns_400_for_weak_password(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "newuser@example.com",
                "password": "weak",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data["errors"]

    @pytest.mark.django_db
    def test_returns_400_for_missing_email(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data["errors"]

    @pytest.mark.django_db
    def test_returns_400_for_missing_password(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "newuser@example.com",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data["errors"]

    @pytest.mark.django_db
    def test_returns_descriptive_error_messages(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "newuser@example.com",
                "password": "weak",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        # Error message should help user fix the issue
        error_msg = response.data["errors"]["password"][0].lower()
        assert "8 characters" in error_msg or "uppercase" in error_msg or "digit" in error_msg


class TestRegistrationEndpoint_DuplicateEmail:
    """Tests duplicate email handling."""

    @pytest.mark.django_db
    def test_returns_409_for_duplicate_email(self, api_client):
        # First registration
        api_client.post(
            "/api/v1/auth/register",
            {
                "email": "existing@example.com",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        # Second registration with same email
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "existing@example.com",
                "password": "StrongPass1!",
                "first_name": "Jane",
                "last_name": "Smith",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.django_db
    def test_returns_error_code_for_duplicate_email(self, api_client):
        api_client.post(
            "/api/v1/auth/register",
            {
                "email": "existing@example.com",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "existing@example.com",
                "password": "StrongPass1!",
                "first_name": "Jane",
                "last_name": "Smith",
            },
            format="json",
        )

        assert response.data["error"] == "email_already_exists"


class TestRegistrationEndpoint_EmailNormalization:
    """Tests email normalization behavior."""

    @pytest.mark.django_db
    def test_normalizes_email_case(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "NewUser@EXAMPLE.COM",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        assert response.data["email"] == "newuser@example.com"

    @pytest.mark.django_db
    def test_treats_different_case_emails_as_duplicate(self, api_client):
        api_client.post(
            "/api/v1/auth/register",
            {
                "email": "user@example.com",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "USER@EXAMPLE.COM",
                "password": "StrongPass1!",
                "first_name": "Jane",
                "last_name": "Smith",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_409_CONFLICT


class TestRegistrationEndpoint_SecurityHeaders:
    """Tests security-related response headers."""

    @pytest.mark.django_db
    def test_does_not_cache_registration_response(self, api_client):
        response = api_client.post(
            "/api/v1/auth/register",
            {
                "email": "newuser@example.com",
                "password": "StrongPass1!",
                "first_name": "John",
                "last_name": "Doe",
            },
            format="json",
        )

        # Should not cache sensitive data
        cache_control = response.get("Cache-Control")
        assert cache_control is None or "no-store" in cache_control or "no-cache" in cache_control
