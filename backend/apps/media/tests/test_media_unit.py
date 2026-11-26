"""Unit tests for media models, HTTP transport, provider adapters, services, and views."""

from io import BytesIO
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError, URLError

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.media.http_client import HttpTransportError, UrllibHttpTransport
from apps.media.models import MediaCategory, MediaItem
from apps.media.providers import (
    GoogleBooksMediaProvider,
    IgdbMediaProvider,
    LocalCatalogProvider,
    MediaProviderRegistry,
    MediaSearchResult,
    TmdbMediaProvider,
)
from apps.media.services import (
    InvalidMediaCategoryError,
    MediaCatalogService,
    MediaNotFoundError,
    parse_media_category,
)
from apps.media.views import MediaCategoriesView, MediaDetailView, MediaSearchView


class FakeHttpResponse:
    """Context-manager response stub returning UTF-8 JSON bytes."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class ScriptedTransport:
    """In-memory scripted HttpTransport recording calls and returning queued outcomes."""

    def __init__(self, outcomes: list[Any]) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[tuple[str, str, dict[str, str] | None, bytes | None]] = []

    def request_json(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ) -> Any:
        self.calls.append((method, url, headers, body))
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FailingCatalogService:
    """Fake MediaCatalogService raising HttpTransportError to verify 502 view mapping."""

    def list_categories(self) -> list[dict[str, str]]:
        return [{"id": "movie", "name": "Filmes", "provider": "TMDB"}]

    def search(self, category_raw: str, query: str, limit: int = 15) -> list[MediaSearchResult]:
        raise HttpTransportError("upstream timeout")

    def get_or_fetch_media(self, category_raw: str, external_id: str) -> MediaItem:
        raise HttpTransportError("upstream timeout")


@pytest.mark.unit
def test_media_item_universal_id_and_str() -> None:
    item = MediaItem(category=MediaCategory.MOVIE, external_id="tt0468569", title="Batman")
    assert item.universal_id == "movie_tt0468569"
    assert str(item) == "[movie] Batman (tt0468569)"


@pytest.mark.unit
def test_urllib_transport_get_success_retries_and_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "apps.media.http_client.urllib.request.urlopen",
        lambda req, timeout: FakeHttpResponse(b'{"ok": true}'),
    )
    sleep_calls: list[float] = []
    monkeypatch.setattr("apps.media.http_client.time.sleep", sleep_calls.append)

    default_transport = UrllibHttpTransport(timeout_seconds=2.5, max_retries=1)
    assert default_transport.request_json("GET", "https://example.test/ok") == {"ok": True}

    attempts = {"count": 0}

    def flaky_open(req: Any, timeout: float) -> FakeHttpResponse:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise HTTPError(req.full_url, 503, "unavailable", hdrs=None, fp=BytesIO(b""))  # type: ignore[arg-type]
        return FakeHttpResponse(b'{"recovered": 1}')

    retried = UrllibHttpTransport(max_retries=2, backoff_seconds=0.1, opener=flaky_open)
    assert retried.request_json("GET", "https://example.test/retry") == {"recovered": 1}
    assert sleep_calls == [0.1]

    def always_500(req: Any, timeout: float) -> FakeHttpResponse:
        raise HTTPError(req.full_url, 500, "err", hdrs=None, fp=BytesIO(b""))  # type: ignore[arg-type]

    no_post_retry = UrllibHttpTransport(
        max_retries=2, opener=always_500, sleeper=sleep_calls.append
    )
    with pytest.raises(HttpTransportError) as post_exc:
        no_post_retry.request_json("POST", "https://example.test/post")
    assert post_exc.value.status_code == 500

    with pytest.raises(HttpTransportError):
        UrllibHttpTransport(
            max_retries=1, backoff_seconds=0.0, opener=always_500, sleeper=lambda _: None
        ).request_json("GET", "https://example.test/exhaust")

    def client_404(req: Any, timeout: float) -> FakeHttpResponse:
        raise HTTPError(req.full_url, 404, "missing", hdrs=None, fp=BytesIO(b""))  # type: ignore[arg-type]

    with pytest.raises(HttpTransportError) as not_found_exc:
        UrllibHttpTransport(max_retries=2, opener=client_404).request_json(
            "GET", "https://example.test/404"
        )
    assert not_found_exc.value.status_code == 404


@pytest.mark.unit
def test_urllib_transport_network_and_json_errors() -> None:
    network_calls = {"n": 0}

    def flaky_network(req: Any, timeout: float) -> FakeHttpResponse:
        network_calls["n"] += 1
        if network_calls["n"] == 1:
            raise URLError("reset")
        raise TimeoutError("timed out")

    transport = UrllibHttpTransport(
        max_retries=1,
        backoff_seconds=0.05,
        opener=flaky_network,
        sleeper=lambda _: None,
    )
    with pytest.raises(HttpTransportError) as net_exc:
        transport.request_json("GET", "https://example.test/net")
    assert net_exc.value.status_code is None

    bad_json = UrllibHttpTransport(opener=lambda req, timeout: FakeHttpResponse(b"not-json"))
    with pytest.raises(HttpTransportError):
        bad_json.request_json("GET", "https://example.test/json")


@pytest.mark.unit
def test_local_catalog_provider_and_tmdb_provider() -> None:
    local = LocalCatalogProvider()
    assert [hit.external_id for hit in local.search(MediaCategory.MOVIE, "batman", 5)] == [
        "tt0468569"
    ]
    assert local.get_by_id(MediaCategory.BOOK, "dune-1") is not None
    assert local.get_by_id(MediaCategory.BOOK, "missing") is None

    transport = ScriptedTransport(
        [
            {
                "results": [
                    {"id": 10, "name": "Live Action", "genre_ids": [18]},
                    {
                        "id": 13916,
                        "name": "Death Note",
                        "genre_ids": [16, 9648],
                        "poster_path": "/dn.jpg",
                        "first_air_date": "2006-10-04",
                        "vote_average": 8.64,
                    },
                ]
            },
            {
                "id": 550,
                "title": "Fight Club",
                "overview": "First rule.",
                "vote_average": 8.43,
                "poster_path": "/fc.jpg",
                "backdrop_path": "/fc-bg.jpg",
                "release_date": "1999-10-15",
                "origin_country": ["US"],
                "genres": [{"name": "Drama"}],
            },
            HttpTransportError("not found", status_code=404),
            HttpTransportError("bad gateway", status_code=500),
        ]
    )
    tmdb = TmdbMediaProvider(transport=transport, api_key="tmdb-secret")
    anime_hits = tmdb.search(MediaCategory.ANIME, "death", limit=5)
    assert len(anime_hits) == 1
    assert anime_hits[0].external_id == "13916"
    assert anime_hits[0].score == 8.6

    detail = tmdb.get_by_id(MediaCategory.MOVIE, "550")
    assert detail is not None
    assert detail.genres == ("Drama",)
    assert detail.banner_url.endswith("/fc-bg.jpg")

    assert tmdb.get_by_id(MediaCategory.MOVIE, "999") is None
    with pytest.raises(HttpTransportError):
        tmdb.get_by_id(MediaCategory.MOVIE, "500")


@pytest.mark.unit
def test_igdb_google_books_and_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    igdb_transport = ScriptedTransport(
        [
            [
                {
                    "id": 1942,
                    "name": "The Witcher 3",
                    "cover": {"image_id": "cov1"},
                    "first_release_date": 1431993600,
                    "rating": 92.6,
                }
            ],
            [],
            [
                {
                    "id": 1942,
                    "name": "The Witcher 3",
                    "summary": "RPG.",
                    "cover": None,
                    "artworks": [{"image_id": "art1"}],
                    "genres": [{"name": "RPG"}],
                    "rating": 92.6,
                    "first_release_date": None,
                }
            ],
        ]
    )
    igdb = IgdbMediaProvider(transport=igdb_transport, client_id="cid", access_token="tok")
    games = igdb.search(MediaCategory.GAME, 'Witcher"', limit=5)
    assert games[0].release_year == "2015"
    assert games[0].poster_url.endswith("/cov1.jpg")
    assert igdb.get_by_id(MediaCategory.GAME, "404") is None
    game_detail = igdb.get_by_id(MediaCategory.GAME, "1942")
    assert game_detail is not None
    assert game_detail.poster_url == ""
    assert game_detail.banner_url.endswith("/art1.jpg")
    assert game_detail.release_year == ""

    books_transport = ScriptedTransport(
        [
            {
                "items": [
                    {
                        "id": "b1",
                        "volumeInfo": {
                            "title": "Duna",
                            "publishedDate": "1965",
                            "averageRating": 4.5,
                            "imageLinks": {"smallThumbnail": "https://img/duna.jpg"},
                        },
                    }
                ]
            },
            {
                "id": "b1",
                "volumeInfo": {
                    "title": "Duna",
                    "description": "Arrakis",
                    "publishedDate": "1965",
                    "averageRating": 4.5,
                    "language": "pt",
                    "categories": ["Sci-Fi"],
                    "imageLinks": {"thumbnail": "https://img/duna-big.jpg"},
                },
            },
            HttpTransportError("missing", status_code=404),
            HttpTransportError("boom", status_code=500),
        ]
    )
    books = GoogleBooksMediaProvider(transport=books_transport, api_key="gkey")
    book_hits = books.search(MediaCategory.BOOK, "Duna", limit=10)
    assert book_hits[0].score == 9.0
    assert books.get_by_id(MediaCategory.BOOK, "b1") is not None
    assert books.get_by_id(MediaCategory.BOOK, "404") is None
    with pytest.raises(HttpTransportError):
        books.get_by_id(MediaCategory.BOOK, "500")

    monkeypatch.setenv("RANKIT_USE_LOCAL_CATALOG", "false")
    monkeypatch.setenv("TMDB_API_KEY", "t")
    monkeypatch.setenv("IGDB_CLIENT_ID", "i")
    monkeypatch.setenv("IGDB_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("GOOGLE_BOOKS_API_KEY", "g")
    live_reg = MediaProviderRegistry.build_default()
    assert live_reg.provider_label(MediaCategory.MOVIE) == "TMDB"
    assert live_reg.provider_label(MediaCategory.GAME) == "IGDB"
    assert live_reg.provider_label(MediaCategory.BOOK) == "Google Books"

    monkeypatch.setenv("RANKIT_USE_LOCAL_CATALOG", "true")
    local_reg = MediaProviderRegistry.build_default()
    assert local_reg.provider_label(MediaCategory.MOVIE) == "Catálogo Local"


@pytest.mark.unit
def test_media_services_and_view_error_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    assert parse_media_category(" MOVIE ") == MediaCategory.MOVIE
    with pytest.raises(InvalidMediaCategoryError):
        parse_media_category("podcast")

    service = MediaCatalogService(registry=MediaProviderRegistry())
    categories = service.list_categories()
    assert len(categories) == 5
    assert len(service.search("anime", "death", limit=5)) == 1

    cached_item = MediaItem(
        id=1, category=MediaCategory.MOVIE, external_id="tt0468569", title="Batman"
    )
    monkeypatch.setattr(
        "apps.media.services.MediaItem.objects.filter",
        lambda **kwargs: SimpleNamespace(first=lambda: cached_item),
    )
    assert service.get_or_fetch_media("movie", "tt0468569") is cached_item

    monkeypatch.setattr(
        "apps.media.services.MediaItem.objects.filter",
        lambda **kwargs: SimpleNamespace(first=lambda: None),
    )
    with pytest.raises(MediaNotFoundError):
        service.get_or_fetch_media("movie", "unknown")

    monkeypatch.setattr(
        "apps.media.services.MediaCatalogService._upsert_media",
        lambda self, detail: MediaItem(
            id=2, category=detail.category.value, external_id=detail.external_id, title=detail.title
        ),
    )
    fetched = service.get_or_fetch_media("movie", "tt0468569")
    assert fetched.title == "Batman: O Cavaleiro das Trevas"

    factory = APIRequestFactory()
    failing = FailingCatalogService()
    cat_res = MediaCategoriesView.as_view(catalog_service=failing)(
        factory.get("/api/v1/media/categories/")
    )
    assert cat_res.status_code == 200

    search_view = MediaSearchView.as_view(catalog_service=failing)
    assert search_view(factory.get("/api/v1/media/search/?category=movie")).status_code == 400
    assert (
        search_view(factory.get("/api/v1/media/search/?category=movie&q=bat&limit=bad")).status_code
        == 400
    )
    assert (
        search_view(factory.get("/api/v1/media/search/?category=movie&q=bat&limit=99")).status_code
        == 400
    )
    assert search_view(factory.get("/api/v1/media/search/?category=movie&q=bat")).status_code == 502

    detail_view = MediaDetailView.as_view(catalog_service=failing)
    assert (
        detail_view(
            factory.get("/api/v1/media/movie/1/"), category="movie", external_id="1"
        ).status_code
        == 502
    )
    assert isinstance(Request(factory.get("/")), Request)
