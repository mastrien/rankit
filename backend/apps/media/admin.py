"""Django admin configuration for cached MediaItem rows."""

from typing import TYPE_CHECKING

from django.contrib import admin

from .models import MediaItem

if TYPE_CHECKING:
    _TypedModelAdmin = admin.ModelAdmin[MediaItem]
else:
    _TypedModelAdmin = admin.ModelAdmin


@admin.register(MediaItem)
class MediaItemAdmin(_TypedModelAdmin):
    """Expose cached media metadata in Django admin."""

    list_display = ("category", "external_id", "title", "score", "views_count", "updated_at")
    list_filter = ("category",)
    search_fields = ("title", "external_id")
