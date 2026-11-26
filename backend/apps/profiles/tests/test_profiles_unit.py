"""Unit tests for 2-hop follow suggestions, UserFollow model, and view auth guards."""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser

from apps.accounts.models import RankitUser
from apps.profiles.models import UserFollow
from apps.profiles.services import FollowSuggestionService, UserSummary
from apps.profiles.views import (
    FollowSuggestionsView,
    FollowUserView,
    UpdateOwnProfileView,
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
