"""DRF serializers for public profiles, customization updates, and follow lists."""

from typing import Any

from rest_framework import serializers

from apps.accounts.models import MAX_PRESET_BANNER_ID, MAX_PRESET_ICON_ID

from .services import ProfileDetail, UserSummary


class UserSummarySerializer(serializers.Serializer[UserSummary]):
    """Compact user summary for follower, following, and suggestion lists."""

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    icon_id = serializers.IntegerField(read_only=True)


class ProfileDetailSerializer(serializers.Serializer[ProfileDetail]):
    """Full public profile payload including follow counts and viewer status."""

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    bio = serializers.CharField(read_only=True)
    icon_id = serializers.IntegerField(read_only=True)
    banner_id = serializers.IntegerField(read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_following = serializers.BooleanField(read_only=True)
    is_self = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class UpdateProfileSerializer(serializers.Serializer[dict[str, Any]]):
    """Validate profile customization inputs."""

    display_name = serializers.CharField(max_length=80)
    bio = serializers.CharField(max_length=200, allow_blank=True)
    icon_id = serializers.IntegerField(min_value=0, max_value=MAX_PRESET_ICON_ID)
    banner_id = serializers.IntegerField(min_value=0, max_value=MAX_PRESET_BANNER_ID)
