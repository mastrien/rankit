"""Origin and custom-header CSRF guards for HttpOnly cookie requests."""

from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
EXPECTED_REQUESTED_WITH = "XMLHttpRequest"


def enforce_cookie_csrf_protection(request: Request) -> None:
    """Reject cross-origin or non-XHR unsafe requests when authenticating via cookies.

    Example:
        enforce_cookie_csrf_protection(request)
    """
    if request.method not in UNSAFE_METHODS:
        return

    origin = request.headers.get("Origin")
    if origin and origin not in settings.CORS_ALLOWED_ORIGINS:
        raise PermissionDenied(
            f"Origin não permitido para requisição autenticada por cookie: {origin!r}."
        )

    requested_with = request.headers.get("X-Requested-With")
    if requested_with != EXPECTED_REQUESTED_WITH:
        raise PermissionDenied(
            f"Cabeçalho X-Requested-With inválido: {requested_with!r} "
            f"(esperado {EXPECTED_REQUESTED_WITH!r})."
        )
