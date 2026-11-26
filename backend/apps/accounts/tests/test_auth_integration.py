"""Integration tests for JWT HttpOnly cookie auth endpoints against PostgreSQL."""

import pytest
from django.conf import settings
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import RankitUser
from apps.accounts.serializers import RegisterSerializer
from apps.accounts.views import _active_user_for_refresh


@pytest.mark.integration
@pytest.mark.django_db
def test_register_login_refresh_rotation_and_logout_revocation() -> None:
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
    old_refresh = register_response.cookies[settings.JWT_REFRESH_COOKIE_NAME].value

    me_response = client.get("/api/v1/auth/me/")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "joao_auth@example.com"

    refresh_response = client.post("/api/v1/auth/refresh/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert refresh_response.status_code == 200
    new_refresh = refresh_response.cookies[settings.JWT_REFRESH_COOKIE_NAME].value
    assert new_refresh and new_refresh != old_refresh

    reused_old_client = APIClient()
    reused_old_client.cookies[settings.JWT_REFRESH_COOKIE_NAME] = old_refresh
    reused_old_resp = reused_old_client.post(
        "/api/v1/auth/refresh/", HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    assert reused_old_resp.status_code == 401

    logout_response = client.post("/api/v1/auth/logout/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert logout_response.status_code == 204
    assert client.get("/api/v1/auth/me/").status_code == 401

    reused_after_logout = APIClient()
    reused_after_logout.cookies[settings.JWT_REFRESH_COOKIE_NAME] = new_refresh
    reused_logout_resp = reused_after_logout.post(
        "/api/v1/auth/refresh/", HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )
    assert reused_logout_resp.status_code == 401

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
    assert bearer_client.get("/api/v1/auth/me/").status_code == 200


@pytest.mark.integration
@pytest.mark.django_db
def test_cookie_csrf_protection_and_stale_cookie_handling() -> None:
    user = RankitUser.objects.create_user(
        username="csrf_user",
        email="csrf@example.com",
        password="StrongPassword!2026",
        display_name="CSRF User",
    )
    client = APIClient()
    login = client.post(
        "/api/v1/auth/login/",
        {"username": "csrf_user", "password": "StrongPassword!2026"},
        format="json",
    )
    assert login.status_code == 200

    assert client.post("/api/v1/auth/refresh/").status_code == 403
    assert client.post("/api/v1/auth/logout/").status_code == 403
    evil_origin = client.post(
        "/api/v1/auth/refresh/",
        HTTP_ORIGIN="https://evil.example.com",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    assert evil_origin.status_code == 403

    stale_client = APIClient()
    stale_client.cookies[settings.JWT_ACCESS_COOKIE_NAME] = "expired.or.invalid"
    assert stale_client.get("/api/v1/health/").status_code == 200
    assert stale_client.get("/api/v1/auth/me/").status_code == 401

    user.is_active = False
    user.save(update_fields=["is_active"])
    inactive_resp = client.post("/api/v1/auth/refresh/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    assert inactive_resp.status_code == 401


@pytest.mark.integration
@pytest.mark.django_db
def test_register_rejects_duplicate_and_concurrent_integrity_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    def _raise_integrity(**kwargs: object) -> RankitUser:
        raise IntegrityError("race duplicate")

    monkeypatch.setattr(RankitUser.objects, "create_user", _raise_integrity)
    serializer = RegisterSerializer()
    with pytest.raises(serializers.ValidationError):
        serializer.create(
            {
                "username": "race",
                "email": "race@example.com",
                "password": "StrongPassword!2026",
                "display_name": "Race",
            }
        )


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

    assert (
        client.post("/api/v1/auth/refresh/", HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code
        == 401
    )

    client.cookies[settings.JWT_REFRESH_COOKIE_NAME] = "not-a-valid-jwt"
    assert (
        client.post("/api/v1/auth/refresh/", HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code
        == 401
    )
    assert (
        client.post("/api/v1/auth/logout/", HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code
        == 204
    )

    token_without_user = RefreshToken()
    assert _active_user_for_refresh(token_without_user) is None
