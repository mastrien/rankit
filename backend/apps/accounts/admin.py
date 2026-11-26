"""Admin registration for RankitUser."""

from typing import TYPE_CHECKING

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import RankitUser

if TYPE_CHECKING:
    _TypedUserAdmin = UserAdmin[RankitUser]
else:
    _TypedUserAdmin = UserAdmin


@admin.register(RankitUser)
class RankitUserAdmin(_TypedUserAdmin):
    """Expose Rankit profile fields in Django Admin."""

    list_display = ("username", "display_name", "email", "is_staff", "created_at")
    fieldsets = (
        *(UserAdmin.fieldsets or ()),
        ("Perfil Rankit", {"fields": ("display_name", "bio", "icon_id", "banner_id")}),
    )
