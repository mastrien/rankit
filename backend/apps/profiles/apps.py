"""Profiles Django app configuration."""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """AppConfig for Rankit public profiles, customization, and follow graph."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.profiles"
