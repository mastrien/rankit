"""Unit tests for cookie JWT utilities, CSRF guard, and authentication serializers."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.authentication import CookieJWTAuthentication
from apps.accounts.cookies import AuthCookieService, JwtCookieSettings, _lifetime_seconds
from apps.accounts.models import RankitUser
from apps.accounts.security import enforce_cookie_csrf_protection
from apps.accounts.serializers import LoginSerializer, RegisterSerializer
from apps.accounts.views import CurrentUserView, LogoutView


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
        secure=True,
        access_max_age_seconds=1800,
        refresh_max_age_seconds=604800,
    )


@pytest.mark.unit
def test_auth_cookie_service_attaches_and_clears_httponly_cookies() -> None:
    service = AuthCookieService(cookie_settings=_test_cookie_settings())
    response = Response({"ok": True})

    service.attach_tokens(response, access_token="acc.jwt", refresh_token="ref.jwt")
    for name, expected_age in (("rankit_access", 1800), ("rankit_refresh", 604800)):
        cookie = response.cookies[name]
        assert cookie["httponly"] is True
        assert cookie["samesite"] == "Lax"
        assert cookie["secure"] is True
        assert cookie["max-age"] == expected_age
    assert response.cookies["rankit_access"].value == "acc.jwt"
    assert response.cookies["rankit_refresh"].value == "ref.jwt"

    service.attach_tokens(response, access_token="acc2.jwt")
    assert response.cookies["rankit_access"].value == "acc2.jwt"

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
def test_enforce_cookie_csrf_protection_rules() -> None:
    factory = APIRequestFactory()

    get_req = SimpleNamespace(method="GET", headers={})
    enforce_cookie_csrf_protection(get_req)  # type: ignore[arg-type]

    with override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000"]):
        ok_req = SimpleNamespace(
            method="POST",
            headers={"Origin": "http://localhost:3000", "X-Requested-With": "XMLHttpRequest"},
        )
        enforce_cookie_csrf_protection(ok_req)  # type: ignore[arg-type]

        bad_origin = SimpleNamespace(
            method="POST",
            headers={"Origin": "https://evil.example", "X-Requested-With": "XMLHttpRequest"},
        )
        with pytest.raises(PermissionDenied, match="Origin"):
            enforce_cookie_csrf_protection(bad_origin)  # type: ignore[arg-type]

        missing_xhr = SimpleNamespace(method="POST", headers={"Origin": "http://localhost:3000"})
        with pytest.raises(PermissionDenied, match="X-Requested-With"):
            enforce_cookie_csrf_protection(missing_xhr)  # type: ignore[arg-type]

    _ = factory


@pytest.mark.unit
def test_cookie_jwt_authentication_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    factory = APIRequestFactory()
    auth = CookieJWTAuthentication()

    anon_req = SimpleNamespace(META=factory.get("/").META, COOKIES={}, method="GET", headers={})
    assert auth.authenticate(anon_req) is None  # type: ignore[arg-type]

    bad_hdr = SimpleNamespace(
        META=factory.get("/", HTTP_AUTHORIZATION="Basic abc").META,
        COOKIES={},
        method="GET",
        headers={},
    )
    assert auth.authenticate(bad_hdr) is None  # type: ignore[arg-type]

    stale_cookie = SimpleNamespace(
        META=factory.get("/").META,
        COOKIES={"rankit_access": "not-a-jwt"},
        method="GET",
        headers={},
    )
    assert auth.authenticate(stale_cookie) is None  # type: ignore[arg-type]

    fake_user = RankitUser(id=1, username="joao", display_name="João", email="j@example.com")
    fake_token = AccessToken()
    monkeypatch.setattr(auth._jwt, "get_validated_token", lambda raw: fake_token)
    monkeypatch.setattr(auth._jwt, "get_user", lambda tok: fake_user)

    valid_cookie = SimpleNamespace(
        META=factory.get("/").META,
        COOKIES={"rankit_access": "valid.jwt"},
        method="GET",
        headers={},
    )
    assert auth.authenticate(valid_cookie) == (fake_user, fake_token)  # type: ignore[arg-type]

    monkeypatch.setattr(auth._jwt, "authenticate", lambda req: (fake_user, fake_token))
    valid_hdr = SimpleNamespace(
        META=factory.get("/", HTTP_AUTHORIZATION="Bearer ok").META,
        COOKIES={},
        method="GET",
        headers={},
    )
    assert auth.authenticate(valid_hdr) == (fake_user, fake_token)  # type: ignore[arg-type]


@pytest.mark.unit
def test_register_serializer_validation_rules() -> None:
    checker = FakeAvailableUserChecker()
    mismatch = RegisterSerializer(
        data={
            "display_name": "João",
            "username": "joao_unit",
            "email": "joao_unit@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "DifferentPassword123!",
        },
        uniqueness_checker=checker,
    )
    assert mismatch.is_valid() is False
    assert "password_confirm" in mismatch.errors

    similar = RegisterSerializer(
        data={
            "display_name": "rankit_probe",
            "username": "rankit_probe",
            "email": "rankit_probe@example.com",
            "password": "rankit_probe",
            "password_confirm": "rankit_probe",
        },
        uniqueness_checker=checker,
    )
    assert similar.is_valid() is False

    reserved = RegisterSerializer(
        data={
            "display_name": "Presets",
            "username": "presets",
            "email": "presets@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        },
        uniqueness_checker=checker,
    )
    assert reserved.is_valid() is False
    assert "username" in reserved.errors

    bad_username = RegisterSerializer(
        data={
            "display_name": "   ",
            "username": "x!",
            "email": "bad@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        },
        uniqueness_checker=checker,
    )
    assert bad_username.is_valid() is False
    assert "display_name" in bad_username.errors
    assert "username" in bad_username.errors


@pytest.mark.unit
def test_login_serializer_lowercases_username_and_rejects_blank() -> None:
    blank = LoginSerializer(data={"username": "   ", "password": "secret"})
    assert blank.is_valid() is False
    assert "username" in blank.errors

    valid = LoginSerializer(data={"username": "Joao", "password": "secret"})
    assert valid.is_valid() is True
    assert valid.validated_data["username"] == "joao"


@pytest.mark.unit
def test_current_user_view_returns_401_for_anonymous_user() -> None:
    response = CurrentUserView().get(SimpleNamespace(user=AnonymousUser()))  # type: ignore[arg-type]
    assert response.status_code == 401


@pytest.mark.unit
def test_logout_view_clears_cookies_even_without_refresh_cookie() -> None:
    request = SimpleNamespace(
        method="POST",
        headers={"Origin": "http://localhost:3000", "X-Requested-With": "XMLHttpRequest"},
        COOKIES={},
    )
    response = LogoutView().post(request)  # type: ignore[arg-type]
    assert response.status_code == 204
    assert response.cookies["rankit_access"].value == ""
    assert response.cookies["rankit_refresh"].value == ""


@pytest.mark.unit
def test_rankit_user_str_returns_at_username() -> None:
    user = RankitUser(username="nathan", display_name="Nathan", email="n@example.com")
    assert str(user) == "@nathan"
