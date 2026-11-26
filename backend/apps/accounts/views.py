"""HTTP views for cookie-based JWT authentication."""

import contextlib
import logging

from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .cookies import AuthCookieService
from .models import RankitUser
from .security import enforce_cookie_csrf_protection
from .serializers import AuthenticatedUserSerializer, LoginSerializer, RegisterSerializer

logger = logging.getLogger(__name__)


def _active_user_for_refresh(refresh: RefreshToken) -> RankitUser | None:
    user_id = refresh.get("user_id")
    if user_id is None:
        return None
    return RankitUser.objects.filter(pk=user_id, is_active=True).first()


class RegisterView(APIView):
    """Create a RankitUser account and issue HttpOnly JWT cookies."""

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        """Validate signup data, persist user, and return 201 with auth cookies."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user: RankitUser = serializer.save()

        response = Response(AuthenticatedUserSerializer(user).data, status=status.HTTP_201_CREATED)
        AuthCookieService().attach_for_user(response, user)
        logger.info("User registered: %s", user.username)
        return response


class LoginView(APIView):
    """Authenticate an existing RankitUser and attach HttpOnly JWT cookies."""

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        """Validate credentials via Django authenticate and set JWT cookies."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(request=request, username=username, password=password)
        if not isinstance(user, RankitUser):
            logger.warning("Failed login attempt for username=%s", username)
            return Response(
                {"detail": "Usuário ou senha incorretos."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response(AuthenticatedUserSerializer(user).data, status=status.HTTP_200_OK)
        AuthCookieService().attach_for_user(response, user)
        return response


class RefreshSessionView(APIView):
    """Rotate refresh cookie and issue a fresh access token cookie."""

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        """Verify CSRF, validate refresh JWT + active user, blacklist old token, and rotate."""
        enforce_cookie_csrf_protection(request)
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if not raw_refresh:
            return Response(
                {"detail": "Refresh token ausente nos cookies."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(raw_refresh)  # type: ignore[arg-type]
            user = _active_user_for_refresh(refresh)
            if user is None:
                return Response(
                    {"detail": "Usuário inativo ou inexistente."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            refresh.blacklist()
        except TokenError:
            return Response(
                {"detail": "Refresh token inválido ou expirado."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response({"detail": "Sessão renovada."}, status=status.HTTP_200_OK)
        AuthCookieService().attach_for_user(response, user)
        return response


class LogoutView(APIView):
    """Revoke refresh token server-side and clear HttpOnly JWT cookies."""

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        """Verify CSRF, blacklist refresh cookie if valid, and delete auth cookies."""
        enforce_cookie_csrf_protection(request)
        raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if raw_refresh:
            with contextlib.suppress(TokenError):
                RefreshToken(raw_refresh).blacklist()  # type: ignore[arg-type]

        response = Response(status=status.HTTP_204_NO_CONTENT)
        AuthCookieService().clear_tokens(response)
        return response


class CurrentUserView(APIView):
    """Return the profile of the currently authenticated user."""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        """Serialize request.user when authenticated by CookieJWTAuthentication."""
        if not isinstance(request.user, RankitUser):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = AuthenticatedUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
