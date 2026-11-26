"""Admin registration for UserFollow."""

from typing import TYPE_CHECKING

from django.contrib import admin

from .models import UserFollow

if TYPE_CHECKING:
    _TypedModelAdmin = admin.ModelAdmin[UserFollow]
else:
    _TypedModelAdmin = admin.ModelAdmin


@admin.register(UserFollow)
class UserFollowAdmin(_TypedModelAdmin):
    """Expose social follow edges in Django Admin."""

    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")
