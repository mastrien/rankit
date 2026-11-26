"""DRF serializers for user registration, login, and authenticated user output."""

import re
from typing import Any, Protocol

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import RankitUser

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")


class UserUniquenessChecker(Protocol):
    """Protocol for checking whether a username or email is already taken."""

    def username_exists(self, username: str) -> bool:
        """Return True when username is already registered."""

    def email_exists(self, email: str) -> bool:
        """Return True when email is already registered."""


class OrmUserUniquenessChecker:
    """Django ORM implementation of UserUniquenessChecker."""

    def username_exists(self, username: str) -> bool:
        """Check case-insensitively whether a RankitUser has this username."""
        return RankitUser.objects.filter(username__iexact=username).exists()

    def email_exists(self, email: str) -> bool:
        """Check case-insensitively whether a RankitUser has this email."""
        return RankitUser.objects.filter(email__iexact=email).exists()


class AuthenticatedUserSerializer(serializers.ModelSerializer[RankitUser]):
    """Public-safe representation of the currently authenticated user."""

    class Meta:
        model = RankitUser
        fields = (
            "id",
            "username",
            "display_name",
            "email",
            "bio",
            "icon_id",
            "banner_id",
            "created_at",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer[RankitUser]):
    """Validate signup payloads and create a hashed RankitUser record."""

    display_name = serializers.CharField(max_length=80)
    username = serializers.CharField(max_length=30)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    def __init__(
        self,
        *args: Any,
        uniqueness_checker: UserUniquenessChecker | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._uniqueness_checker = uniqueness_checker or OrmUserUniquenessChecker()

    def validate_username(self, value: str) -> str:
        """Enforce Rankit username format and uniqueness."""
        cleaned = value.lower()
        if not USERNAME_PATTERN.match(cleaned):
            raise serializers.ValidationError(
                f"Username inválido: {value!r} (esperado 3-30 caracteres [a-zA-Z0-9_.-])."
            )
        if self._uniqueness_checker.username_exists(cleaned):
            raise serializers.ValidationError("Já existe um usuário com este nome de usuário.")
        return cleaned

    def validate_email(self, value: str) -> str:
        """Normalize email to lowercase and enforce uniqueness."""
        cleaned = value.strip().lower()
        if self._uniqueness_checker.email_exists(cleaned):
            raise serializers.ValidationError("Este e-mail já está cadastrado.")
        return cleaned

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Verify matching passwords and run Django password strength validators."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "As senhas não coincidem."})
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data: dict[str, Any]) -> RankitUser:
        """Persist a new RankitUser with Django's password hashing."""
        return RankitUser.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            display_name=validated_data["display_name"],
        )


class LoginSerializer(serializers.Serializer[dict[str, Any]]):
    """Validate login credentials payload."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate_username(self, value: str) -> str:
        """Lowercase username before authentication."""
        return value.lower()
