"""Follow relationship ORM model with database-enforced uniqueness and anti-self-follow."""

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.core.models import TimestampedModel


class UserFollow(TimestampedModel):
    """Directed social follow edge from follower to following RankitUser.

    Example:
        UserFollow.objects.create(follower=alice, following=bob)
    """

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relations",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relations",
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_user_follow",
            ),
            models.CheckConstraint(
                condition=~Q(follower=F("following")),
                name="prevent_self_follow",
            ),
        )
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"@{self.follower.username} -> @{self.following.username}"
