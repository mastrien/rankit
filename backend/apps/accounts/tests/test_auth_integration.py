"""Integration tests for JWT HttpOnly cookie auth endpoints against PostgreSQL."""

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from apps.accounts.models import RankitUser


@pytest.mark.integration
@pytest.mark.django_db
def test_register_login_refresh_me_and_logout_flow() -> None:
    client = APIClient()

    register_response = client.post(
        "/api/v1/auth/register/",
        {
            "display_name": "João Pedro",
            "username": "joao_auth",
            "email": "joao_auth@example.com",
            "password": "StrongPassword!2026",
            "password_confirm": "StrongPassword!2026",
        },
        format="json",
    )
    assert register_response.status_code == 201
    assert register_response.json()["username"] == "joao_auth"
    assert settings.JWT_ACCESS_COOKIE_NAME in register_response.cookies
    assert settings.JWT_REFRESH_COOKIE_NAME in register_response.cookies

    me_response = client.get("/api/v1/auth/me/")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "joao_auth@example.com"

    refresh_response = client.post("/api/v1/auth/refresh/")
    assert refresh_response.status_code == 200
    assert settings.JWT_ACCESS_COOKIE_NAME in refresh_response.cookies

    logout_response = client.post("/api/v1/auth/logout/")
    assert logout_response.status_code == 204

    unauthenticated_me = client.get("/api/v1/auth/me/")
    assert unauthenticated_me.status_code == 401

    login_response = client.post(
        "/api/v1/auth/login/",
        {"username": "joao_auth", "password": "StrongPassword!2026"},
        format="json",
    )
    assert login_response.status_code == 200
    assert login_response.json()["display_name"] == "João Pedro"

    bearer_client = APIClient()
    access_token = login_response.cookies[settings.JWT_ACCESS_COOKIE_NAME].value
    bearer_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    bearer_me = bearer_client.get("/api/v1/auth/me/")
    assert bearer_me.status_code == 200
    assert bearer_me.json()["username"] == "joao_auth"


@pytest.mark.integration
@pytest.mark.django_db
def test_register_rejects_duplicate_username_and_email() -> None:
    RankitUser.objects.create_user(
        username="dupuser",
        email="dup@example.com",
        password="StrongPassword!2026",
        display_name="Dup User",
    )
    client = APIClient()

    response = client.post(
        "/api/v1/auth/register/",
        {
            "display_name": "Another",
            "username": "dupuser",
            "email": "dup@example.com",
            "password": "StrongPassword!2026",
            "password_confirm": "StrongPassword!2026",
        },
        format="json",
    )
    assert response.status_code == 400
    errors = response.json()
    assert "username" in errors
    assert "email" in errors


@pytest.mark.integration
@pytest.mark.django_db
def test_login_and_refresh_reject_invalid_credentials_and_tokens() -> None:
    RankitUser.objects.create_user(
        username="validuser",
        email="valid@example.com",
        password="StrongPassword!2026",
        display_name="Valid User",
    )
    client = APIClient()

    bad_login = client.post(
        "/api/v1/auth/login/",
        {"username": "validuser", "password": "WrongPassword"},
        format="json",
    )
    assert bad_login.status_code == 401

    missing_refresh = client.post("/api/v1/auth/refresh/")
    assert missing_refresh.status_code == 401

    client.cookies[settings.JWT_REFRESH_COOKIE_NAME] = "not-a-valid-jwt"
    invalid_refresh = client.post("/api/v1/auth/refresh/")
    assert invalid_refresh.status_code == 401
