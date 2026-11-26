"""Domain services for user profiles, follow relationships, and 2-hop suggestions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from django.db import IntegrityError, transaction

from apps.accounts.models import MAX_PRESET_BANNER_ID, MAX_PRESET_ICON_ID, RankitUser

from .models import UserFollow

PRESET_ICON_IDS: tuple[int, ...] = tuple(range(MAX_PRESET_ICON_ID + 1))
PRESET_BANNER_IDS: tuple[int, ...] = tuple(range(MAX_PRESET_BANNER_ID + 1))


class ProfileNotFoundError(Exception):
    """Raised when a target profile username does not exist."""


class FollowConflictError(Exception):
    """Raised when a follow operation violates self-follow or uniqueness rules."""


class FollowRelationNotFoundError(Exception):
    """Raised when attempting to remove a non-existent follow relationship."""


@dataclass(frozen=True)
class UserSummary:
    """Compact representation of a Rankit user for follow lists and suggestions."""

    id: int
    username: str
    display_name: str
    icon_id: int


@dataclass(frozen=True)
class ProfileDetail:
    """Public profile read model enriched with follow counts and viewer relation."""

    id: int
    username: str
    display_name: str
    bio: str
    icon_id: int
    banner_id: int
    followers_count: int
    following_count: int
    is_following: bool
    is_self: bool
    created_at: datetime


class FollowGraphRepository(Protocol):
    """Repository abstraction for reading 1-hop social connections."""

    def following_of(self, username: str) -> list[UserSummary]:
        """Return users that username follows, ordered deterministically."""

    def followers_of(self, username: str) -> list[UserSummary]:
        """Return users who follow username, ordered deterministically."""

    def following_usernames(self, username: str) -> set[str]:
        """Return set of usernames followed by username."""


def _user_to_summary(user: RankitUser) -> UserSummary:
    return UserSummary(
        id=int(user.pk),
        username=user.username,
        display_name=user.display_name,
        icon_id=user.icon_id,
    )


def _find_user_or_raise(username: str) -> RankitUser:
    normalized = username.strip().lower()
    user = RankitUser.objects.filter(username__iexact=normalized).first()
    if user is None:
        raise ProfileNotFoundError(
            f"Perfil {username!r} não encontrado (esperado username existente)."
        )
    return user


class OrmFollowGraphRepository:
    """Django ORM implementation of FollowGraphRepository."""

    def following_of(self, username: str) -> list[UserSummary]:
        """Return users followed by username ordered by most recent follow."""
        relations = UserFollow.objects.filter(follower__username__iexact=username).select_related(
            "following"
        )
        return [_user_to_summary(rel.following) for rel in relations]

    def followers_of(self, username: str) -> list[UserSummary]:
        """Return followers of username ordered by most recent follow."""
        relations = UserFollow.objects.filter(following__username__iexact=username).select_related(
            "follower"
        )
        return [_user_to_summary(rel.follower) for rel in relations]

    def following_usernames(self, username: str) -> set[str]:
        """Return the set of usernames that username currently follows."""
        qs = UserFollow.objects.filter(follower__username__iexact=username).values_list(
            "following__username", flat=True
        )
        return set(qs)


class FollowSuggestionService:
    """Compute 2-hop follow suggestions prioritizing target's following then followers.

    Example:
        suggestions = FollowSuggestionService(repo).suggest(
            actor_username="alice",
            target_username="bob",
        )
    """

    def __init__(self, repository: FollowGraphRepository | None = None) -> None:
        self._repo = repository or OrmFollowGraphRepository()

    def suggest(self, actor_username: str, target_username: str) -> list[UserSummary]:
        """Suggest users connected to target that actor does not already follow."""
        actor_key = actor_username.strip().lower()
        target_key = target_username.strip().lower()
        excluded = {actor_key, target_key, *self._repo.following_usernames(actor_key)}

        candidates = [
            *self._repo.following_of(target_key),
            *self._repo.followers_of(target_key),
        ]
        suggestions: list[UserSummary] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = candidate.username.lower()
            if key in excluded or key in seen:
                continue
            seen.add(key)
            suggestions.append(candidate)
        return suggestions


class ProfileService:
    """Fetch and update Rankit user profiles."""

    def get_profile(self, target_username: str, actor: RankitUser | None) -> ProfileDetail:
        """Build a ProfileDetail read model for target_username relative to actor."""
        target = _find_user_or_raise(target_username)
        followers_count = UserFollow.objects.filter(following=target).count()
        following_count = UserFollow.objects.filter(follower=target).count()
        is_self = actor is not None and actor.pk == target.pk
        is_following = (
            actor is not None
            and not is_self
            and UserFollow.objects.filter(follower=actor, following=target).exists()
        )
        return ProfileDetail(
            id=int(target.pk),
            username=target.username,
            display_name=target.display_name,
            bio=target.bio,
            icon_id=target.icon_id,
            banner_id=target.banner_id,
            followers_count=followers_count,
            following_count=following_count,
            is_following=is_following,
            is_self=is_self,
            created_at=target.created_at,
        )

    def update_profile(
        self,
        actor: RankitUser,
        display_name: str,
        bio: str,
        icon_id: int,
        banner_id: int,
    ) -> ProfileDetail:
        """Persist profile customization fields on actor and return updated detail."""
        actor.display_name = display_name
        actor.bio = bio
        actor.icon_id = icon_id
        actor.banner_id = banner_id
        actor.save(update_fields=["display_name", "bio", "icon_id", "banner_id", "updated_at"])
        return self.get_profile(actor.username, actor)


class FollowService:
    """Create, delete, and list directed follow relationships."""

    def __init__(self, repository: FollowGraphRepository | None = None) -> None:
        self._repo = repository or OrmFollowGraphRepository()

    def follow_user(self, actor: RankitUser, target_username: str) -> None:
        """Create a follow edge from actor to target_username or raise domain error."""
        target = _find_user_or_raise(target_username)
        if actor.pk == target.pk:
            raise FollowConflictError(
                f"Não é possível seguir a si mesmo (username={target.username!r})."
            )
        try:
            with transaction.atomic():
                UserFollow.objects.create(follower=actor, following=target)
        except IntegrityError as exc:
            raise FollowConflictError(
                f"Você já segue @{target.username} (follower={actor.username!r})."
            ) from exc

    def unfollow_user(self, actor: RankitUser, target_username: str) -> None:
        """Remove a follow edge from actor to target_username or raise if missing."""
        target = _find_user_or_raise(target_username)
        deleted_count, _ = UserFollow.objects.filter(follower=actor, following=target).delete()
        if deleted_count == 0:
            raise FollowRelationNotFoundError(
                f"Relação de follow inexistente de @{actor.username} para @{target.username}."
            )

    def list_followers(self, target_username: str) -> list[UserSummary]:
        """List followers of target_username after verifying target exists."""
        target = _find_user_or_raise(target_username)
        return self._repo.followers_of(target.username)

    def list_following(self, target_username: str) -> list[UserSummary]:
        """List users followed by target_username after verifying target exists."""
        target = _find_user_or_raise(target_username)
        return self._repo.following_of(target.username)
