"""Unit tests for 2-hop follow suggestions, UserFollow model, and view auth guards."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import ValidationError

from apps.accounts.models import RankitUser
from apps.profiles.models import UserFollow
from apps.profiles.services import FollowService, FollowSuggestionService, UserSummary
from apps.profiles.views import (
    FollowSuggestionsView,
    FollowUserView,
    UpdateOwnProfileView,
    _parse_bounded_int,
)


class FakeFollowGraphRepository:
    """In-memory fake social graph repository for unit-testing FollowSuggestionService."""

    def __init__(
        self,
        following_map: dict[str, list[UserSummary]],
        followers_map: dict[str, list[UserSummary]],
    ) -> None:
        self._following = following_map
        self._followers = followers_map

    def following_of(self, username: str) -> list[UserSummary]:
        return list(self._following.get(username, []))

    def followers_of(self, username: str) -> list[UserSummary]:
        return list(self._followers.get(username, []))

    def following_usernames(self, username: str) -> set[str]:
        return {item.username for item in self._following.get(username, [])}


def _summary(uid: int, username: str) -> UserSummary:
    return UserSummary(id=uid, username=username, display_name=username.title(), icon_id=0)


@pytest.mark.unit
def test_follow_suggestion_prioritizes_following_over_followers_and_deduplicates() -> None:
    alice = _summary(1, "alice")
    bob = _summary(2, "bob")
    carol = _summary(3, "carol")
    dave = _summary(4, "dave")
    eve = _summary(5, "eve")
    already = _summary(6, "already")

    repo = FakeFollowGraphRepository(
        following_map={
            "alice": [bob, already],
            "bob": [carol, already, alice],
        },
        followers_map={
            "bob": [dave, carol, eve, alice],
        },
    )
    service = FollowSuggestionService(repository=repo)

    result = service.suggest(actor_username="alice", target_username="bob")

    assert [item.username for item in result] == ["carol", "dave", "eve"]


@pytest.mark.unit
def test_follow_suggestion_returns_empty_for_isolated_profile() -> None:
    repo = FakeFollowGraphRepository(following_map={}, followers_map={})
    service = FollowSuggestionService(repository=repo)

    assert service.suggest(actor_username="alice", target_username="bob") == []


@pytest.mark.unit
def test_user_follow_str_formats_directed_edge() -> None:
    alice = RankitUser(username="alice", display_name="Alice", email="a@example.com")
    bob = RankitUser(username="bob", display_name="Bob", email="b@example.com")
    relation = UserFollow(follower=alice, following=bob)

    assert str(relation) == "@alice -> @bob"


@pytest.mark.unit
def test_profile_authenticated_views_reject_anonymous_user_defensively() -> None:
    anon_request = SimpleNamespace(user=AnonymousUser(), data={})

    assert UpdateOwnProfileView().patch(anon_request).status_code == 401  # type: ignore[arg-type]
    assert FollowUserView().post(anon_request, "bob").status_code == 401  # type: ignore[arg-type]
    assert FollowUserView().delete(anon_request, "bob").status_code == 401  # type: ignore[arg-type]
    assert FollowSuggestionsView().get(anon_request, "bob").status_code == 401  # type: ignore[arg-type]


@pytest.mark.unit
def test_follow_suggestion_normalizes_mixed_case_and_respects_limit() -> None:
    alice = _summary(1, "Alice")
    bob = _summary(2, "Bob")
    carol = _summary(3, "Carol")
    dave = _summary(4, "Dave")
    already = _summary(5, "Already")

    repo = FakeFollowGraphRepository(
        following_map={
            "alice": [bob, already],
            "bob": [carol, alice],
        },
        followers_map={
            "bob": [dave, _summary(6, "ALREADY")],
        },
    )
    service = FollowSuggestionService(repository=repo)

    result = service.suggest(actor_username=" Alice ", target_username="BOB", limit=1)
    assert [item.username for item in result] == ["Carol"]


@pytest.mark.unit
def test_parse_bounded_int_validates_defaults_bounds_and_integers() -> None:
    empty_req = SimpleNamespace(query_params={})
    assert _parse_bounded_int(empty_req, "limit", 50, 1, 100) == 50  # type: ignore[arg-type]

    valid_req = SimpleNamespace(query_params={"limit": "25"})
    assert _parse_bounded_int(valid_req, "limit", 50, 1, 100) == 25  # type: ignore[arg-type]

    non_int_req = SimpleNamespace(query_params={"limit": "abc"})
    with pytest.raises(ValidationError):
        _parse_bounded_int(non_int_req, "limit", 50, 1, 100)  # type: ignore[arg-type]

    out_of_bounds_req = SimpleNamespace(query_params={"limit": "0"})
    with pytest.raises(ValidationError):
        _parse_bounded_int(out_of_bounds_req, "limit", 50, 1, 100)  # type: ignore[arg-type]


@pytest.mark.unit
def test_follow_service_lists_apply_limit_and_offset_slice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    users = [_summary(1, "u1"), _summary(2, "u2"), _summary(3, "u3")]
    repo = FakeFollowGraphRepository(
        following_map={"bob": users},
        followers_map={"bob": users},
    )
    monkeypatch.setattr(
        "apps.profiles.services._find_user_or_raise", lambda username: _summary(99, username)
    )
    service = FollowService(repository=repo)

    assert [u.username for u in service.list_followers("bob", limit=1, offset=1)] == ["u2"]
    assert [u.username for u in service.list_following("bob", limit=2, offset=1)] == ["u2", "u3"]
