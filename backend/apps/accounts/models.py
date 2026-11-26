"""Custom Rankit user model built on Django ORM."""

from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator
from django.db import models

MAX_PRESET_ICON_ID = 18
MAX_PRESET_BANNER_ID = 6


class RankitUser(AbstractUser):
    """Rankit user storing display profile metadata and preset visual IDs.

    Example:
        user = RankitUser.objects.create_user(
            username="joao",
            email="joao@example.com",
            password="strong-password-123",
            display_name="João Pedro",
        )
    """

    display_name = models.CharField(max_length=80)
    email = models.EmailField(unique=True)
    bio = models.CharField(max_length=200, blank=True, default="")
    icon_id = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(MAX_PRESET_ICON_ID)],
    )
    banner_id = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(MAX_PRESET_BANNER_ID)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS: ClassVar[list[str]] = ["email", "display_name"]

    class Meta:
        ordering = ("username",)

    def __str__(self) -> str:
        return f"@{self.username}"
