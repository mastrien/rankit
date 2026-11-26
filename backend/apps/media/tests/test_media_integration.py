"""PostgreSQL integration tests for Rankit media catalog endpoints and DB caching."""

import pytest
from rest_framework.test import APIClient

from apps.media.models import MediaCategory, MediaItem


@pytest.mark.integration
@pytest.mark.django_db
def test_media_categories_search_and_postgresql_lazy_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RANKIT_USE_LOCAL_CATALOG", "true")
    client = APIClient()

    categories_res = client.get("/api/v1/media/categories/")
    assert categories_res.status_code == 200
    assert [entry["id"] for entry in categories_res.json()] == [
        "movie",
        "serie",
        "anime",
        "game",
        "book",
    ]

    movie_search = client.get("/api/v1/media/search/?category=movie&q=batman")
    assert movie_search.status_code == 200
    hits = movie_search.json()
    assert len(hits) == 1
    assert hits[0]["external_id"] == "tt0468569"

    game_search = client.get("/api/v1/media/search/?category=game&q=elden&limit=1")
    assert game_search.status_code == 200
    assert game_search.json()[0]["title"] == "Elden Ring"

    assert client.get("/api/v1/media/search/?category=movie&q=").status_code == 400
    assert client.get("/api/v1/media/search/?category=invalid&q=batman").status_code == 400
    assert client.get("/api/v1/media/search/?category=movie&q=batman&limit=0").status_code == 400

    assert MediaItem.objects.count() == 0
    first_detail = client.get("/api/v1/media/movie/tt0468569/")
    assert first_detail.status_code == 200
    assert first_detail.json()["universal_id"] == "movie_tt0468569"
    assert (
        MediaItem.objects.filter(
            category=MediaCategory.MOVIE,
            external_id="tt0468569",
        ).count()
        == 1
    )

    cached_row = MediaItem.objects.get(category=MediaCategory.MOVIE, external_id="tt0468569")
    cached_row.title = "Batman (Cache PostgreSQL)"
    cached_row.save(update_fields=["title", "updated_at"])

    second_detail = client.get("/api/v1/media/movie/tt0468569/")
    assert second_detail.status_code == 200
    assert second_detail.json()["title"] == "Batman (Cache PostgreSQL)"

    assert client.get("/api/v1/media/invalid/tt0468569/").status_code == 400
    assert client.get("/api/v1/media/movie/nonexistent-id/").status_code == 404
