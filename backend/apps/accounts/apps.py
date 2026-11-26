"""Accounts Django app configuration."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """AppConfig for Rankit user accounts and JWT authentication."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
