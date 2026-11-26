"""HTTP views exposing media categories, catalog search, and detail endpoints."""

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .http_client import HttpTransportError
from .serializers import (
    MediaCategorySerializer,
    MediaDetailSerializer,
    MediaSearchResultSerializer,
)
from .services import InvalidMediaCategoryError, MediaCatalogService, MediaNotFoundError


def _parse_limit(request: Request, default: int = 15, max_value: int = 50) -> int:
    raw = request.query_params.get("limit")
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ValidationError({"limit": f"Parâmetro 'limit' inválido ({raw!r}; inteiro)."}) from exc
    if parsed < 1 or parsed > max_value:
        raise ValidationError(
            {"limit": f"Parâmetro 'limit' fora do intervalo ({parsed}; entre 1 e {max_value})."}
        )
    return parsed


class MediaCategoriesView(APIView):
    """List Rankit media categories and their active provider adapters."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    catalog_service: MediaCatalogService | None = None

    def _get_service(self) -> MediaCatalogService:
        return self.catalog_service or MediaCatalogService()

    def get(self, request: Request) -> Response:
        """Return supported media categories with provider metadata."""
        categories = self._get_service().list_categories()
        return Response(
            [MediaCategorySerializer(entry).data for entry in categories],
            status=status.HTTP_200_OK,
        )


class MediaSearchView(APIView):
    """Search media entries by category and query via active provider adapter."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    catalog_service: MediaCatalogService | None = None

    def _get_service(self) -> MediaCatalogService:
        return self.catalog_service or MediaCatalogService()

    def get(self, request: Request) -> Response:
        """Validate ?category=&q=&limit= and return normalized MediaSearchResult items."""
        category = request.query_params.get("category", "").strip()
        query = request.query_params.get("q", "").strip()
        if not category or not query:
            return Response(
                {"detail": "Informe os parâmetros 'category' e 'q' não vazios."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        limit = _parse_limit(request)
        try:
            results = self._get_service().search(category_raw=category, query=query, limit=limit)
        except InvalidMediaCategoryError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except HttpTransportError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(
            [MediaSearchResultSerializer(item).data for item in results],
            status=status.HTTP_200_OK,
        )


class MediaDetailView(APIView):
    """Retrieve and lazily cache full media metadata in PostgreSQL."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    catalog_service: MediaCatalogService | None = None

    def _get_service(self) -> MediaCatalogService:
        return self.catalog_service or MediaCatalogService()

    def get(self, request: Request, category: str, external_id: str) -> Response:
        """Return cached or freshly fetched MediaItem detail for (category, external_id)."""
        try:
            item = self._get_service().get_or_fetch_media(
                category_raw=category, external_id=external_id
            )
        except InvalidMediaCategoryError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except MediaNotFoundError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except HttpTransportError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(MediaDetailSerializer(item).data, status=status.HTTP_200_OK)
