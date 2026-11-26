"""Unit tests for cookie JWT utilities and authentication serializers."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from apps.accounts.authentication import CookieJWTAuthentication
from apps.accounts.cookies import AuthCookieService, JwtCookieSettings, _lifetime_seconds
from apps.accounts.models import RankitUser
from apps.accounts.serializers import LoginSerializer, RegisterSerializer
from apps.accounts.views import CurrentUserView


class FakeAvailableUserChecker:
    """Fake uniqueness checker reporting all usernames and emails as available."""

    def username_exists(self, username: str) -> bool:
        return False

    def email_exists(self, email: str) -> bool:
        return False


def _test_cookie_settings() -> JwtCookieSettings:
    return JwtCookieSettings(
        access_name="rankit_access",
        refresh_name="rankit_refresh",
        secure=False,
        access_max_age_seconds=1800,
        refresh_max_age_seconds=604800,
    )


@pytest.mark.unit
def test_auth_cookie_service_attaches_and_clears_httponly_cookies() -> None:
    service = AuthCookieService(cookie_settings=_test_cookie_settings())
    response = Response({"ok": True})

    service.attach_tokens(response, access_token="acc.jwt", refresh_token="ref.jwt")
    assert response.cookies["rankit_access"].value == "acc.jwt"
    assert response.cookies["rankit_access"]["httponly"] is True
    assert response.cookies["rankit_access"]["samesite"] == "Lax"
    assert response.cookies["rankit_refresh"].value == "ref.jwt"

    service.clear_tokens(response)
    assert response.cookies["rankit_access"].value == ""
    assert response.cookies["rankit_refresh"].value == ""


@pytest.mark.unit
def test_lifetime_seconds_rejects_non_timedelta_setting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from django.conf import settings

    monkeypatch.setitem(settings.SIMPLE_JWT, "ACCESS_TOKEN_LIFETIME", 300)
    with pytest.raises(TypeError, match="must be a timedelta"):
        _lifetime_seconds("ACCESS_TOKEN_LIFETIME")


@pytest.mark.unit
def test_cookie_jwt_authentication_returns_none_without_header_or_cookie() -> None:
    factory = APIRequestFactory()
    django_request = factory.get("/api/v1/auth/me/")
    drf_request = SimpleNamespace(META=django_request.META, COOKIES={})

    auth = CookieJWTAuthentication()
    assert auth.authenticate(drf_request) is None  # type: ignore[arg-type]


@pytest.mark.unit
def test_cookie_jwt_authentication_returns_none_for_malformed_header() -> None:
    factory = APIRequestFactory()
    django_request = factory.get("/api/v1/auth/me/", HTTP_AUTHORIZATION="Basic abc")
    drf_request = SimpleNamespace(META=django_request.META, COOKIES={})

    auth = CookieJWTAuthentication()
    assert auth.authenticate(drf_request) is None  # type: ignore[arg-type]


@pytest.mark.unit
def test_register_serializer_rejects_mismatched_passwords() -> None:
    serializer = RegisterSerializer(
        data={
            "display_name": "João",
            "username": "joao_unit",
            "email": "joao_unit@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "DifferentPassword123!",
        },
        uniqueness_checker=FakeAvailableUserChecker(),
    )

    assert serializer.is_valid() is False
    assert "password_confirm" in serializer.errors


@pytest.mark.unit
def test_register_serializer_rejects_blank_display_name_and_bad_username() -> None:
    serializer = RegisterSerializer(
        data={
            "display_name": "   ",
            "username": "x!",
            "email": "bad@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        },
        uniqueness_checker=FakeAvailableUserChecker(),
    )

    assert serializer.is_valid() is False
    assert "display_name" in serializer.errors
    assert "username" in serializer.errors


@pytest.mark.unit
def test_login_serializer_rejects_blank_username() -> None:
    serializer = LoginSerializer(data={"username": "   ", "password": "secret"})

    assert serializer.is_valid() is False
    assert "username" in serializer.errors


@pytest.mark.unit
def test_current_user_view_returns_401_for_anonymous_user() -> None:
    response = CurrentUserView().get(SimpleNamespace(user=AnonymousUser()))  # type: ignore[arg-type]
    assert response.status_code == 401


@pytest.mark.unit
def test_rankit_user_str_returns_at_username() -> None:
    user = RankitUser(username="nathan", display_name="Nathan", email="n@example.com")
    assert str(user) == "@nathan"
