"""DRF serializers for user registration, login, and authenticated user output."""

import re
from typing import Any, Protocol

from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import RankitUser

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")
RESERVED_USERNAMES = frozenset({"me", "presets", "edit", "login", "register", "admin", "api"})


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
        """Enforce Rankit username format, reserved list, and uniqueness."""
        cleaned = value.lower()
        if not USERNAME_PATTERN.match(cleaned):
            raise serializers.ValidationError(
                f"Username inválido: {value!r} (esperado 3-30 caracteres [a-zA-Z0-9_.-])."
            )
        if cleaned in RESERVED_USERNAMES:
            raise serializers.ValidationError(f"O nome de usuário {cleaned!r} é reservado.")
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
        candidate = RankitUser(
            username=attrs["username"],
            email=attrs["email"],
            display_name=attrs["display_name"],
        )
        validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data: dict[str, Any]) -> RankitUser:
        """Persist a new RankitUser with Django's password hashing."""
        try:
            with transaction.atomic():
                return RankitUser.objects.create_user(
                    username=validated_data["username"],
                    email=validated_data["email"],
                    password=validated_data["password"],
                    display_name=validated_data["display_name"],
                )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"username": "Já existe um usuário com este nome de usuário ou e-mail."}
            ) from exc


class LoginSerializer(serializers.Serializer[dict[str, Any]]):
    """Validate login credentials payload."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

    def validate_username(self, value: str) -> str:
        """Lowercase username before authentication."""
        return value.lower()
