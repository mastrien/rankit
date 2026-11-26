"""Application services for Rankit media catalog search and lazy PostgreSQL caching."""

from django.db import transaction

from .models import MediaCategory, MediaItem
from .providers import MediaDetailData, MediaProviderRegistry, MediaSearchResult


class InvalidMediaCategoryError(Exception):
    """Raised when a caller supplies an unsupported media category slug."""


class MediaNotFoundError(Exception):
    """Raised when an external or local catalog item cannot be located."""


def parse_media_category(raw: str) -> MediaCategory:
    """Validate and normalize a category slug into MediaCategory or raise domain error."""
    normalized = raw.strip().lower()
    valid_map = {member.value: member for member in MediaCategory}
    category = valid_map.get(normalized)
    if category is None:
        expected = ", ".join(valid_map.keys())
        raise InvalidMediaCategoryError(
            f"Categoria de mídia inválida {raw!r} (esperado uma de: {expected})."
        )
    return category


class MediaCatalogService:
    """Coordinate provider lookups and lazy MediaItem persistence in PostgreSQL.

    Example:
        results = MediaCatalogService().search("movie", "batman", limit=10)
    """

    def __init__(self, registry: MediaProviderRegistry | None = None) -> None:
        self._registry = registry or MediaProviderRegistry.build_default()

    def list_categories(self) -> list[dict[str, str]]:
        """Return supported media categories with display labels and active provider names."""
        return [
            {
                "id": member.value,
                "name": str(member.label),
                "provider": self._registry.provider_label(member),
            }
            for member in MediaCategory
        ]

    def search(self, category_raw: str, query: str, limit: int = 15) -> list[MediaSearchResult]:
        """Search active provider for category_raw using trimmed query."""
        category = parse_media_category(category_raw)
        provider = self._registry.for_category(category)
        return provider.search(category=category, query=query.strip(), limit=limit)

    def _upsert_media(self, detail: MediaDetailData) -> MediaItem:
        with transaction.atomic():
            item, _ = MediaItem.objects.update_or_create(
                category=detail.category.value,
                external_id=detail.external_id,
                defaults={
                    "title": detail.title,
                    "description": detail.description,
                    "score": detail.score,
                    "poster_url": detail.poster_url,
                    "banner_url": detail.banner_url,
                    "release_year": detail.release_year,
                    "origin_country": detail.origin_country,
                    "genres": list(detail.genres),
                },
            )
            return item

    def get_or_fetch_media(self, category_raw: str, external_id: str) -> MediaItem:
        """Serve cached MediaItem from PostgreSQL or hydrate it once from provider."""
        category = parse_media_category(category_raw)
        cleaned_id = external_id.strip()
        cached = MediaItem.objects.filter(category=category.value, external_id=cleaned_id).first()
        if cached is not None:
            return cached

        detail = self._registry.for_category(category).get_by_id(category, cleaned_id)
        if detail is None:
            raise MediaNotFoundError(
                f"Obra ({category.value}, {external_id!r}) não encontrada no catálogo."
            )
        return self._upsert_media(detail)
