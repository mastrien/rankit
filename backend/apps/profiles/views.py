"""HTTP views for Rankit profiles, customization, and social follow graph."""

import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import RankitUser

from .services import (
    PRESET_BANNER_IDS,
    PRESET_ICON_IDS,
    FollowConflictError,
    FollowRelationNotFoundError,
    FollowService,
    FollowSuggestionService,
    ProfileNotFoundError,
    ProfileService,
    _find_user_or_raise,
)

logger = logging.getLogger(__name__)


def _viewer_or_none(request: Request) -> RankitUser | None:
    return request.user if isinstance(request.user, RankitUser) else None


def _not_found_response(exc: ProfileNotFoundError) -> Response:
    return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)


def _parse_bounded_int(
    request: Request, name: str, default: int, min_value: int, max_value: int
) -> int:
    raw = request.query_params.get(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ValidationError(
            {name: f"Parâmetro {name!r} inválido ({raw!r}; esperado inteiro)."}
        ) from exc
    if parsed < min_value or parsed > max_value:
        raise ValidationError(
            {
                name: (
                    f"Parâmetro {name!r} fora do intervalo "
                    f"({parsed}; esperado entre {min_value} e {max_value})."
                )
            }
        )
    return parsed


class ProfilePresetsView(APIView):
    """Expose available preset icon and banner IDs."""

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        """Return lists of supported icon_id and banner_id presets."""
        return Response(
            {"icons": list(PRESET_ICON_IDS), "banners": list(PRESET_BANNER_IDS)},
            status=status.HTTP_200_OK,
        )


class UpdateOwnProfileView(APIView):
    """Update the authenticated user's display name, bio, icon, and banner."""

    permission_classes = (IsAuthenticated,)

    def patch(self, request: Request) -> Response:
        """Validate payload and persist customization on request.user."""
        actor = _viewer_or_none(request)
        if actor is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        from .serializers import ProfileDetailSerializer, UpdateProfileSerializer

        serializer = UpdateProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        detail = ProfileService().update_profile(
            actor=actor,
            display_name=data.get("display_name"),
            bio=data.get("bio"),
            icon_id=data.get("icon_id"),
            banner_id=data.get("banner_id"),
        )
        logger.info("Profile updated: %s", actor.username)
        return Response(ProfileDetailSerializer(detail).data, status=status.HTTP_200_OK)


class ProfileDetailView(APIView):
    """Fetch public profile metadata for any Rankit user."""

    permission_classes = (AllowAny,)

    def get(self, request: Request, username: str) -> Response:
        """Return ProfileDetail for username or 404 when absent."""
        from .serializers import ProfileDetailSerializer

        try:
            detail = ProfileService().get_profile(username, _viewer_or_none(request))
        except ProfileNotFoundError as exc:
            return _not_found_response(exc)
        return Response(ProfileDetailSerializer(detail).data, status=status.HTTP_200_OK)


class FollowUserView(APIView):
    """Follow or unfollow a target Rankit user."""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, username: str) -> Response:
        """Create follow relationship from authenticated user to username."""
        actor = _viewer_or_none(request)
        if actor is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            FollowService().follow_user(actor, username)
        except ProfileNotFoundError as exc:
            return _not_found_response(exc)
        except FollowConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Seguindo usuário."}, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, username: str) -> Response:
        """Delete follow relationship from authenticated user to username."""
        actor = _viewer_or_none(request)
        if actor is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            FollowService().unfollow_user(actor, username)
        except (ProfileNotFoundError, FollowRelationNotFoundError) as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowersListView(APIView):
    """List users who follow the specified profile."""

    permission_classes = (AllowAny,)

    def get(self, request: Request, username: str) -> Response:
        """Return compact summaries of followers for username."""
        from .serializers import UserSummarySerializer

        limit = _parse_bounded_int(request, "limit", default=50, min_value=1, max_value=100)
        offset = _parse_bounded_int(request, "offset", default=0, min_value=0, max_value=10_000)
        try:
            followers = FollowService().list_followers(username, limit=limit, offset=offset)
        except ProfileNotFoundError as exc:
            return _not_found_response(exc)
        return Response(
            [UserSummarySerializer(item).data for item in followers],
            status=status.HTTP_200_OK,
        )


class FollowingListView(APIView):
    """List users followed by the specified profile."""

    permission_classes = (AllowAny,)

    def get(self, request: Request, username: str) -> Response:
        """Return compact summaries of accounts followed by username."""
        from .serializers import UserSummarySerializer

        limit = _parse_bounded_int(request, "limit", default=50, min_value=1, max_value=100)
        offset = _parse_bounded_int(request, "offset", default=0, min_value=0, max_value=10_000)
        try:
            following = FollowService().list_following(username, limit=limit, offset=offset)
        except ProfileNotFoundError as exc:
            return _not_found_response(exc)
        return Response(
            [UserSummarySerializer(item).data for item in following],
            status=status.HTTP_200_OK,
        )


class FollowSuggestionsView(APIView):
    """Return 2-hop follow suggestions relative to the viewed profile."""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, username: str) -> Response:
        """Return prioritized follow suggestions for the authenticated viewer."""
        from .serializers import UserSummarySerializer

        actor = _viewer_or_none(request)
        if actor is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        limit = _parse_bounded_int(request, "limit", default=20, min_value=1, max_value=50)
        try:
            target = _find_user_or_raise(username)
        except ProfileNotFoundError as exc:
            return _not_found_response(exc)

        suggestions = FollowSuggestionService().suggest(
            actor_username=actor.username,
            target_username=target.username,
            limit=limit,
        )
        return Response(
            [UserSummarySerializer(item).data for item in suggestions],
            status=status.HTTP_200_OK,
        )
