"""Django application configuration for Rankit media catalog."""

from django.apps import AppConfig


class MediaConfig(AppConfig):
    """Register the media domain application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.media"
