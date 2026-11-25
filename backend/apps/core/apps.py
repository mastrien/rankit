"""Core Django app configuration."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """AppConfig for shared Rankit core utilities."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
