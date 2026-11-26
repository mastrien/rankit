"""DRF serializers for media categories, search hits, and cached media details."""

from rest_framework import serializers

from .models import MediaItem
from .providers import MediaSearchResult


class MediaCategorySerializer(serializers.Serializer[dict[str, str]]):
    """Describe a supported Rankit media category."""

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    provider = serializers.CharField(read_only=True)


class MediaSearchResultSerializer(serializers.Serializer[MediaSearchResult]):
    """Compact normalized result returned by media search endpoint."""

    external_id = serializers.CharField(read_only=True)
    category = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    poster_url = serializers.CharField(read_only=True)
    release_year = serializers.CharField(read_only=True)
    score = serializers.FloatField(read_only=True)


class MediaDetailSerializer(serializers.ModelSerializer[MediaItem]):
    """Full cached MediaItem representation for media detail pages."""

    universal_id = serializers.CharField(read_only=True)

    class Meta:
        model = MediaItem
        fields = (
            "id",
            "universal_id",
            "category",
            "external_id",
            "title",
            "description",
            "score",
            "poster_url",
            "banner_url",
            "release_year",
            "origin_country",
            "genres",
            "views_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
