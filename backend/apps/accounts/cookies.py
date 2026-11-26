"""HttpOnly cookie management for JWT access and refresh tokens."""

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import RankitUser


@dataclass(frozen=True)
class JwtCookieSettings:
    """Configuration values controlling HttpOnly JWT cookie attributes."""

    access_name: str
    refresh_name: str
    secure: bool
    access_max_age_seconds: int
    refresh_max_age_seconds: int


def _lifetime_seconds(key: str) -> int:
    value = settings.SIMPLE_JWT[key]
    if not isinstance(value, timedelta):
        raise TypeError(f"SIMPLE_JWT[{key!r}] must be a timedelta, got {type(value).__name__}.")
    return int(value.total_seconds())


def default_cookie_settings() -> JwtCookieSettings:
    """Build JwtCookieSettings from Django project settings."""
    return JwtCookieSettings(
        access_name=settings.JWT_ACCESS_COOKIE_NAME,
        refresh_name=settings.JWT_REFRESH_COOKIE_NAME,
        secure=bool(settings.JWT_COOKIE_SECURE),
        access_max_age_seconds=_lifetime_seconds("ACCESS_TOKEN_LIFETIME"),
        refresh_max_age_seconds=_lifetime_seconds("REFRESH_TOKEN_LIFETIME"),
    )


class AuthCookieService:
    """Attach and clear HttpOnly JWT cookies on DRF Response objects.

    Example:
        AuthCookieService().attach_for_user(response, user)
    """

    def __init__(self, cookie_settings: JwtCookieSettings | None = None) -> None:
        self._settings = cookie_settings or default_cookie_settings()

    def _set_cookie(self, response: Response, key: str, value: str, max_age: int) -> None:
        response.set_cookie(
            key=key,
            value=value,
            httponly=True,
            secure=self._settings.secure,
            samesite="Lax",
            max_age=max_age,
            path="/",
        )

    def attach_for_user(self, response: Response, user: RankitUser) -> None:
        """Issue access + refresh tokens for user and write them as HttpOnly cookies."""
        refresh = RefreshToken.for_user(user)
        self.attach_tokens(response, str(refresh.access_token), str(refresh))

    def attach_tokens(
        self,
        response: Response,
        access_token: str,
        refresh_token: str | None = None,
    ) -> None:
        """Write access (and optional refresh) JWT cookies with HttpOnly + SameSite=Lax."""
        self._set_cookie(
            response,
            self._settings.access_name,
            access_token,
            self._settings.access_max_age_seconds,
        )
        if refresh_token is not None:
            self._set_cookie(
                response,
                self._settings.refresh_name,
                refresh_token,
                self._settings.refresh_max_age_seconds,
            )

    def clear_tokens(self, response: Response) -> None:
        """Delete both JWT authentication cookies from the client."""
        response.delete_cookie(self._settings.access_name, path="/", samesite="Lax")
        response.delete_cookie(self._settings.refresh_name, path="/", samesite="Lax")
