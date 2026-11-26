"""Integration tests for user profiles, presets, and follow graph against PostgreSQL."""

import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.accounts.models import RankitUser
from apps.profiles.models import UserFollow


def _create_user(username: str, display_name: str) -> RankitUser:
    return RankitUser.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="StrongPassword!2026",
        display_name=display_name,
    )


@pytest.mark.integration
@pytest.mark.django_db
def test_profile_presets_detail_and_customization_flow() -> None:
    alice = _create_user("alice_prof", "Alice")
    client = APIClient()

    presets_response = client.get("/api/v1/profiles/presets/")
    assert presets_response.status_code == 200
    assert presets_response.json()["icons"] == list(range(19))
    assert presets_response.json()["banners"] == list(range(7))

    public_profile = client.get("/api/v1/profiles/alice_prof/")
    assert public_profile.status_code == 200
    assert public_profile.json()["is_self"] is False
    assert public_profile.json()["is_following"] is False

    missing_profile = client.get("/api/v1/profiles/nonexistent_user/")
    assert missing_profile.status_code == 404

    client.force_authenticate(user=alice)
    patch_response = client.patch(
        "/api/v1/profiles/me/",
        {
            "display_name": "Alice Rankit",
            "bio": "Cinéfila e leitora de ficção científica.",
            "icon_id": 12,
            "banner_id": 4,
        },
        format="json",
    )
    assert patch_response.status_code == 200
    payload = patch_response.json()
    assert payload["display_name"] == "Alice Rankit"
    assert payload["bio"] == "Cinéfila e leitora de ficção científica."
    assert payload["icon_id"] == 12
    assert payload["banner_id"] == 4
    assert payload["is_self"] is True


@pytest.mark.integration
@pytest.mark.django_db
def test_follow_unfollow_lists_and_2hop_suggestions() -> None:
    alice = _create_user("alice_g", "Alice")
    bob = _create_user("bob_g", "Bob")
    carol = _create_user("carol_g", "Carol")
    dave = _create_user("dave_g", "Dave")

    UserFollow.objects.create(follower=bob, following=carol)
    UserFollow.objects.create(follower=dave, following=bob)

    client = APIClient()
    client.force_authenticate(user=alice)

    follow_bob = client.post("/api/v1/profiles/bob_g/follow/")
    assert follow_bob.status_code == 201

    dup_follow = client.post("/api/v1/profiles/bob_g/follow/")
    assert dup_follow.status_code == 400

    self_follow = client.post("/api/v1/profiles/alice_g/follow/")
    assert self_follow.status_code == 400

    missing_follow = client.post("/api/v1/profiles/nobody_x/follow/")
    assert missing_follow.status_code == 404

    bob_profile = client.get("/api/v1/profiles/bob_g/")
    assert bob_profile.status_code == 200
    assert bob_profile.json()["followers_count"] == 2
    assert bob_profile.json()["following_count"] == 1
    assert bob_profile.json()["is_following"] is True

    followers = client.get("/api/v1/profiles/bob_g/followers/")
    assert followers.status_code == 200
    assert {item["username"] for item in followers.json()} == {"alice_g", "dave_g"}

    following = client.get("/api/v1/profiles/bob_g/following/")
    assert following.status_code == 200
    assert [item["username"] for item in following.json()] == ["carol_g"]

    suggestions = client.get("/api/v1/profiles/bob_g/suggestions/")
    assert suggestions.status_code == 200
    assert [item["username"] for item in suggestions.json()] == ["carol_g", "dave_g"]

    assert client.get("/api/v1/profiles/nobody_x/followers/").status_code == 404
    assert client.get("/api/v1/profiles/nobody_x/following/").status_code == 404
    assert client.get("/api/v1/profiles/nobody_x/suggestions/").status_code == 404

    unfollow_bob = client.delete("/api/v1/profiles/bob_g/follow/")
    assert unfollow_bob.status_code == 204

    unfollow_again = client.delete("/api/v1/profiles/bob_g/follow/")
    assert unfollow_again.status_code == 404


@pytest.mark.integration
@pytest.mark.django_db
def test_postgres_check_constraint_prevents_self_follow() -> None:
    alice = _create_user("alice_db", "Alice DB")
    with pytest.raises(IntegrityError):
        UserFollow.objects.create(follower=alice, following=alice)
