"""ORM models for Rankit media categories and cached catalog items."""

from django.db import models

from apps.core.models import TimestampedModel


class MediaCategory(models.TextChoices):
    """Supported Rankit catalog categories matching frontend slugs."""

    MOVIE = "movie", "Filmes"
    SERIE = "serie", "Séries"
    ANIME = "anime", "Animes"
    GAME = "game", "Jogos"
    BOOK = "book", "Livros"


class MediaItem(TimestampedModel):
    """Cached media entry fetched from an external provider or local catalog.

    Example:
        MediaItem.objects.create(
            category=MediaCategory.MOVIE,
            external_id="tt0468569",
            title="Batman",
        )
    """

    category = models.CharField(max_length=16, choices=MediaCategory.choices)
    external_id = models.CharField(max_length=128)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    score = models.FloatField(default=0.0)
    poster_url = models.CharField(max_length=500, blank=True, default="")
    banner_url = models.CharField(max_length=500, blank=True, default="")
    release_year = models.CharField(max_length=16, blank=True, default="")
    origin_country = models.CharField(max_length=64, blank=True, default="")
    genres = models.JSONField(default=list, blank=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=["category", "external_id"],
                name="unique_media_category_external_id",
            ),
        )
        ordering = ("-updated_at", "-id")

    @property
    def universal_id(self) -> str:
        """Return canonical composite identifier across categories."""
        return f"{self.category}_{self.external_id}"

    def __str__(self) -> str:
        return f"[{self.category}] {self.title} ({self.external_id})"
