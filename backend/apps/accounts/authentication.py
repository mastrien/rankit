"""JWT authentication reading access tokens from HttpOnly cookies or Bearer headers."""

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import Token


class CookieJWTAuthentication(BaseAuthentication):
    """Authenticate requests via Bearer header first, falling back to HttpOnly cookie.

    Example:
        REST_FRAMEWORK = {
            "DEFAULT_AUTHENTICATION_CLASSES": [
                "apps.accounts.authentication.CookieJWTAuthentication",
            ]
        }
    """

    def __init__(self) -> None:
        self._jwt = JWTAuthentication()

    def authenticate(self, request: Request) -> tuple[AbstractBaseUser, Token] | None:
        """Return (user, token) from Authorization header or HttpOnly access cookie."""
        if self._jwt.get_header(request) is not None:
            result = self._jwt.authenticate(request)
            if result is None:
                return None
            user, token = result
            return (user, token) if isinstance(user, AbstractBaseUser) else None

        cookie_token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
        if not cookie_token:
            return None

        validated_token = self._jwt.get_validated_token(cookie_token.encode("utf-8"))
        return self._jwt.get_user(validated_token), validated_token

    def authenticate_header(self, request: Request) -> str:
        """Return WWW-Authenticate challenge header delegated to JWTAuthentication."""
        return self._jwt.authenticate_header(request)
