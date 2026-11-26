"""External media providers (TMDB, IGDB, Google Books) and deterministic local fallback."""

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import quote

from .http_client import HttpTransport, HttpTransportError, UrllibHttpTransport
from .models import MediaCategory


@dataclass(frozen=True)
class MediaSearchResult:
    """Normalized media search hit returned across all category providers."""

    external_id: str
    category: MediaCategory
    title: str
    poster_url: str
    release_year: str
    score: float


@dataclass(frozen=True)
class MediaDetailData:
    """Normalized full media metadata used to hydrate and cache MediaItem rows."""

    external_id: str
    category: MediaCategory
    title: str
    description: str
    score: float
    poster_url: str
    banner_url: str
    release_year: str
    origin_country: str
    genres: tuple[str, ...]


class MediaProvider(Protocol):
    """Provider contract implemented by external API adapters and local catalog fallback."""

    def search(self, category: MediaCategory, query: str, limit: int) -> list[MediaSearchResult]:
        """Search media entries matching query within category."""

    def get_by_id(self, category: MediaCategory, external_id: str) -> MediaDetailData | None:
        """Fetch full media details by provider external_id or return None if absent."""


_LOCAL_ITEMS: tuple[MediaDetailData, ...] = (
    MediaDetailData(
        external_id="tt0468569",
        category=MediaCategory.MOVIE,
        title="Batman: O Cavaleiro das Trevas",
        description=(
            "Com ajuda de Jim Gordon e Harvey Dent, Batman enfrenta o caos do Coringa em Gotham."
        ),
        score=9.0,
        poster_url="/assets/banners/0.png",
        banner_url="/assets/banners/0.png",
        release_year="2008",
        origin_country="US",
        genres=("Ação", "Crime", "Drama"),
    ),
    MediaDetailData(
        external_id="tt1375666",
        category=MediaCategory.MOVIE,
        title="A Origem",
        description=(
            "Um ladrão especializado em extrair segredos do subconsciente recebe uma última missão."
        ),
        score=8.8,
        poster_url="/assets/banners/1.png",
        banner_url="/assets/banners/1.png",
        release_year="2010",
        origin_country="US",
        genres=("Ficção Científica", "Ação"),
    ),
    MediaDetailData(
        external_id="1396",
        category=MediaCategory.SERIE,
        title="Breaking Bad",
        description=(
            "Um professor de química diagnosticado com câncer passa a produzir metanfetamina."
        ),
        score=9.5,
        poster_url="/assets/banners/2.png",
        banner_url="/assets/banners/2.png",
        release_year="2008",
        origin_country="US",
        genres=("Drama", "Crime"),
    ),
    MediaDetailData(
        external_id="1399",
        category=MediaCategory.SERIE,
        title="Game of Thrones",
        description=(
            "Famílias nobres disputam o controle do Trono de Ferro nos Sete Reinos de Westeros."
        ),
        score=8.9,
        poster_url="/assets/banners/3.png",
        banner_url="/assets/banners/3.png",
        release_year="2011",
        origin_country="US",
        genres=("Fantasia", "Drama"),
    ),
    MediaDetailData(
        external_id="13916",
        category=MediaCategory.ANIME,
        title="Death Note",
        description=(
            "Um estudante encontra um caderno capaz de matar quem tiver o nome escrito nele."
        ),
        score=8.9,
        poster_url="/assets/banners/4.png",
        banner_url="/assets/banners/4.png",
        release_year="2006",
        origin_country="JP",
        genres=("Animação", "Mistério", "Suspense"),
    ),
    MediaDetailData(
        external_id="1429",
        category=MediaCategory.ANIME,
        title="Attack on Titan",
        description=(
            "A humanidade luta pela sobrevivência atrás de muralhas gigantescas contra titãs."
        ),
        score=9.0,
        poster_url="/assets/banners/5.png",
        banner_url="/assets/banners/5.png",
        release_year="2013",
        origin_country="JP",
        genres=("Animação", "Ação", "Fantasia"),
    ),
    MediaDetailData(
        external_id="1942",
        category=MediaCategory.GAME,
        title="The Witcher 3: Wild Hunt",
        description="Geralt de Rívia percorre um mundo devastado pela guerra em busca de Ciri.",
        score=9.3,
        poster_url="/assets/banners/6.png",
        banner_url="/assets/banners/6.png",
        release_year="2015",
        origin_country="PL",
        genres=("RPG", "Aventura"),
    ),
    MediaDetailData(
        external_id="119133",
        category=MediaCategory.GAME,
        title="Elden Ring",
        description="Um Maculado explora as Terras Intermédias para restaurar o Anel Prístino.",
        score=9.5,
        poster_url="/assets/banners/0.png",
        banner_url="/assets/banners/0.png",
        release_year="2022",
        origin_country="JP",
        genres=("RPG", "Ação"),
    ),
    MediaDetailData(
        external_id="hp-1",
        category=MediaCategory.BOOK,
        title="Harry Potter e a Pedra Filosofal",
        description="Um jovem descobre aos onze anos que é um bruxo e ingressa em Hogwarts.",
        score=8.9,
        poster_url="/assets/icons/0.png",
        banner_url="/assets/banners/1.png",
        release_year="1997",
        origin_country="GB",
        genres=("Fantasia", "Aventura"),
    ),
    MediaDetailData(
        external_id="dune-1",
        category=MediaCategory.BOOK,
        title="Duna",
        description=(
            "Paul Atreides enfrenta intrigas políticas e profecias no planeta desértico Arrakis."
        ),
        score=9.1,
        poster_url="/assets/icons/1.png",
        banner_url="/assets/banners/2.png",
        release_year="1965",
        origin_country="US",
        genres=("Ficção Científica",),
    ),
)


class LocalCatalogProvider:
    """Deterministic local fallback catalog used when external API credentials are absent."""

    def __init__(self, items: tuple[MediaDetailData, ...] = _LOCAL_ITEMS) -> None:
        self._items = items

    def search(self, category: MediaCategory, query: str, limit: int) -> list[MediaSearchResult]:
        """Return matching seeded items for category filtered case-insensitively by query."""
        needle = query.strip().lower()
        results: list[MediaSearchResult] = []
        for item in self._items:
            if item.category != category:
                continue
            haystack = " ".join((item.title, item.description, *item.genres)).lower()
            if needle in haystack:
                results.append(
                    MediaSearchResult(
                        external_id=item.external_id,
                        category=item.category,
                        title=item.title,
                        poster_url=item.poster_url,
                        release_year=item.release_year,
                        score=item.score,
                    )
                )
        return results[:limit]

    def get_by_id(self, category: MediaCategory, external_id: str) -> MediaDetailData | None:
        """Return seeded detail matching (category, external_id) or None."""
        cleaned = external_id.strip()
        for item in self._items:
            if item.category == category and item.external_id == cleaned:
                return item
        return None


def _extract_year(raw_date: object) -> str:
    return str(raw_date)[:4] if raw_date else ""


def _unix_to_year(raw_timestamp: object) -> str:
    if isinstance(raw_timestamp, int | float):
        return str(datetime.fromtimestamp(raw_timestamp, tz=UTC).year)
    return ""


class TmdbMediaProvider:
    """Adapter for TMDB v3 movies, series, and animation-filtered TV anime."""

    IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
    BACKDROP_BASE = "https://image.tmdb.org/t/p/w780"

    def __init__(
        self,
        transport: HttpTransport,
        api_key: str,
        base_url: str = "https://api.themoviedb.org/3",
    ) -> None:
        self._transport = transport
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "Authorization": f"Bearer {self._api_key}"}

    def _endpoint_type(self, category: MediaCategory) -> str:
        return "movie" if category == MediaCategory.MOVIE else "tv"

    def _full_url(self, prefix: str, path: object) -> str:
        return f"{prefix}{path}" if path else ""

    def search(self, category: MediaCategory, query: str, limit: int) -> list[MediaSearchResult]:
        """Search TMDB movies or TV shows, keeping animation genre 16 for anime."""
        media_type = self._endpoint_type(category)
        url = (
            f"{self._base_url}/search/{media_type}"
            f"?query={quote(query)}&include_adult=false&language=pt-BR&page=1"
        )
        payload = self._transport.request_json("GET", url, headers=self._headers())
        items: list[MediaSearchResult] = []
        for raw in payload.get("results", []):
            if category == MediaCategory.ANIME and 16 not in raw.get("genre_ids", []):
                continue
            items.append(self._map_search_item(category, raw))
        return items[:limit]

    def _map_search_item(self, category: MediaCategory, raw: dict[str, Any]) -> MediaSearchResult:
        title = str(raw.get("title") or raw.get("name") or "")
        release = raw.get("release_date") or raw.get("first_air_date")
        return MediaSearchResult(
            external_id=str(raw.get("id", "")),
            category=category,
            title=title,
            poster_url=self._full_url(self.IMAGE_BASE, raw.get("poster_path")),
            release_year=_extract_year(release),
            score=round(float(raw.get("vote_average") or 0.0), 1),
        )

    def get_by_id(self, category: MediaCategory, external_id: str) -> MediaDetailData | None:
        """Fetch TMDB detail by ID or return None on 404."""
        media_type = self._endpoint_type(category)
        url = f"{self._base_url}/{media_type}/{quote(external_id)}?language=pt-BR"
        try:
            raw = self._transport.request_json("GET", url, headers=self._headers())
        except HttpTransportError as exc:
            if exc.status_code == 404:
                return None
            raise
        genres = tuple(str(entry["name"]) for entry in raw.get("genres", []) if entry.get("name"))
        countries = ", ".join(str(code) for code in raw.get("origin_country", []))
        return MediaDetailData(
            external_id=str(raw.get("id", external_id)),
            category=category,
            title=str(raw.get("title") or raw.get("name") or ""),
            description=str(raw.get("overview") or ""),
            score=round(float(raw.get("vote_average") or 0.0), 1),
            poster_url=self._full_url(self.IMAGE_BASE, raw.get("poster_path")),
            banner_url=self._full_url(self.BACKDROP_BASE, raw.get("backdrop_path")),
            release_year=_extract_year(raw.get("release_date") or raw.get("first_air_date")),
            origin_country=countries,
            genres=genres,
        )


class IgdbMediaProvider:
    """Adapter for IGDB v4 games API."""

    COVER_BASE = "https://images.igdb.com/igdb/image/upload/t_cover_big"
    BANNER_BASE = "https://images.igdb.com/igdb/image/upload/t_screenshot_big"

    def __init__(
        self,
        transport: HttpTransport,
        client_id: str,
        access_token: str,
        base_url: str = "https://api.igdb.com/v4",
    ) -> None:
        self._transport = transport
        self._client_id = client_id
        self._access_token = access_token
        self._base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Client-ID": self._client_id,
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

    def _image_url(self, base: str, nested: object) -> str:
        if isinstance(nested, dict) and nested.get("image_id"):
            return f"{base}/{nested['image_id']}.jpg"
        return ""

    def search(self, category: MediaCategory, query: str, limit: int) -> list[MediaSearchResult]:
        """Search IGDB games using Apicalypse query body."""
        escaped = query.replace('"', "")
        apicalypse = (
            f'search "{escaped}"; '
            "fields id,name,cover.image_id,rating,first_release_date; "
            f"limit {limit};"
        )
        raw_items = self._transport.request_json(
            "POST",
            f"{self._base_url}/games",
            headers=self._headers(),
            body=apicalypse.encode("utf-8"),
        )
        return [
            MediaSearchResult(
                external_id=str(item.get("id", "")),
                category=category,
                title=str(item.get("name") or ""),
                poster_url=self._image_url(self.COVER_BASE, item.get("cover")),
                release_year=_unix_to_year(item.get("first_release_date")),
                score=round(float(item.get("rating") or 0.0) / 10.0, 1),
            )
            for item in raw_items
        ]

    def get_by_id(self, category: MediaCategory, external_id: str) -> MediaDetailData | None:
        """Fetch a single IGDB game record by numeric/string ID."""
        apicalypse = (
            f"where id={external_id}; "
            "fields id,name,summary,cover.image_id,artworks.image_id,"
            "genres.name,rating,first_release_date;"
        )
        raw_items = self._transport.request_json(
            "POST",
            f"{self._base_url}/games",
            headers=self._headers(),
            body=apicalypse.encode("utf-8"),
        )
        if not raw_items:
            return None
        raw = raw_items[0]
        artworks = raw.get("artworks") or []
        banner = self._image_url(self.BANNER_BASE, artworks[0]) if artworks else ""
        genres = tuple(str(g["name"]) for g in raw.get("genres", []) if g.get("name"))
        return MediaDetailData(
            external_id=str(raw.get("id", external_id)),
            category=category,
            title=str(raw.get("name") or ""),
            description=str(raw.get("summary") or ""),
            score=round(float(raw.get("rating") or 0.0) / 10.0, 1),
            poster_url=self._image_url(self.COVER_BASE, raw.get("cover")),
            banner_url=banner,
            release_year=_unix_to_year(raw.get("first_release_date")),
            origin_country="",
            genres=genres,
        )


class GoogleBooksMediaProvider:
    """Adapter for Google Books Volumes API."""

    def __init__(
        self,
        transport: HttpTransport,
        api_key: str,
        base_url: str = "https://www.googleapis.com/books/v1",
    ) -> None:
        self._transport = transport
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def _thumbnail(self, info: dict[str, Any]) -> str:
        links = info.get("imageLinks") or {}
        return str(links.get("thumbnail") or links.get("smallThumbnail") or "")

    def search(self, category: MediaCategory, query: str, limit: int) -> list[MediaSearchResult]:
        """Search Google Books volumes by text query."""
        max_results = min(limit, 40)
        url = (
            f"{self._base_url}/volumes?q={quote(query)}"
            f"&maxResults={max_results}&key={quote(self._api_key)}"
        )
        payload = self._transport.request_json("GET", url)
        items: list[MediaSearchResult] = []
        for raw in payload.get("items", [])[:limit]:
            info = raw.get("volumeInfo") or {}
            items.append(
                MediaSearchResult(
                    external_id=str(raw.get("id", "")),
                    category=category,
                    title=str(info.get("title") or ""),
                    poster_url=self._thumbnail(info),
                    release_year=_extract_year(info.get("publishedDate")),
                    score=round(float(info.get("averageRating") or 0.0) * 2.0, 1),
                )
            )
        return items

    def get_by_id(self, category: MediaCategory, external_id: str) -> MediaDetailData | None:
        """Fetch a single Google Books volume by volume ID or return None on 404."""
        url = f"{self._base_url}/volumes/{quote(external_id)}?key={quote(self._api_key)}"
        try:
            raw = self._transport.request_json("GET", url)
        except HttpTransportError as exc:
            if exc.status_code == 404:
                return None
            raise
        info = raw.get("volumeInfo") or {}
        thumb = self._thumbnail(info)
        categories = tuple(str(entry) for entry in info.get("categories", []) if entry)
        return MediaDetailData(
            external_id=str(raw.get("id", external_id)),
            category=category,
            title=str(info.get("title") or ""),
            description=str(info.get("description") or ""),
            score=round(float(info.get("averageRating") or 0.0) * 2.0, 1),
            poster_url=thumb,
            banner_url=thumb,
            release_year=_extract_year(info.get("publishedDate")),
            origin_country=str(info.get("language") or "").upper(),
            genres=categories,
        )


_PROVIDER_LABELS: dict[str, str] = {
    "TmdbMediaProvider": "TMDB",
    "IgdbMediaProvider": "IGDB",
    "GoogleBooksMediaProvider": "Google Books",
    "LocalCatalogProvider": "Catálogo Local",
}


class MediaProviderRegistry:
    """Resolve the active MediaProvider for each MediaCategory with local fallback."""

    def __init__(
        self,
        providers: dict[MediaCategory, MediaProvider] | None = None,
        fallback: MediaProvider | None = None,
    ) -> None:
        self._providers = providers or {}
        self._fallback: MediaProvider = fallback or LocalCatalogProvider()

    @classmethod
    def build_default(cls) -> "MediaProviderRegistry":
        """Build registry from env vars, falling back to LocalCatalogProvider when unset."""
        use_local = os.getenv("RANKIT_USE_LOCAL_CATALOG", "false").lower() == "true"
        transport = UrllibHttpTransport()
        providers: dict[MediaCategory, MediaProvider] = {}
        tmdb_key = "" if use_local else os.getenv("TMDB_API_KEY", "").strip()
        if tmdb_key:
            tmdb = TmdbMediaProvider(transport=transport, api_key=tmdb_key)
            providers[MediaCategory.MOVIE] = tmdb
            providers[MediaCategory.SERIE] = tmdb
            providers[MediaCategory.ANIME] = tmdb
        igdb_id = "" if use_local else os.getenv("IGDB_CLIENT_ID", "").strip()
        igdb_token = "" if use_local else os.getenv("IGDB_ACCESS_TOKEN", "").strip()
        if igdb_id and igdb_token:
            providers[MediaCategory.GAME] = IgdbMediaProvider(
                transport=transport,
                client_id=igdb_id,
                access_token=igdb_token,
            )
        books_key = "" if use_local else os.getenv("GOOGLE_BOOKS_API_KEY", "").strip()
        if books_key:
            providers[MediaCategory.BOOK] = GoogleBooksMediaProvider(
                transport=transport,
                api_key=books_key,
            )
        return cls(providers=providers, fallback=LocalCatalogProvider())

    def for_category(self, category: MediaCategory) -> MediaProvider:
        """Return configured provider for category or fallback LocalCatalogProvider."""
        return self._providers.get(category, self._fallback)

    def provider_label(self, category: MediaCategory) -> str:
        """Return human-readable label for the active provider serving category."""
        provider_cls_name = type(self.for_category(category)).__name__
        return _PROVIDER_LABELS.get(provider_cls_name, provider_cls_name)
