"""Core infrastructure services including database health probing."""

import logging
from dataclasses import dataclass
from typing import Protocol

from django.db import DatabaseError, connections

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HealthReport:
    """Typed result of system health verification."""

    status: str
    database: str
    is_healthy: bool


class DatabaseProbe(Protocol):
    """Protocol for checking database connectivity."""

    def ping(self) -> None:
        """Execute a lightweight probe query or raise on failure."""


class DjangoDatabaseProbe:
    """Database probe backed by Django's configured default connection."""

    def __init__(self, alias: str = "default") -> None:
        self._alias = alias

    def ping(self) -> None:
        """Execute SELECT 1 against the configured Django database alias."""
        with connections[self._alias].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()


class DatabaseHealthService:
    """Evaluate API and PostgreSQL readiness via an injected probe.

    Example:
        service = DatabaseHealthService(probe=DjangoDatabaseProbe())
        report = service.check()
    """

    def __init__(self, probe: DatabaseProbe | None = None) -> None:
        self._probe = probe or DjangoDatabaseProbe()

    def check(self) -> HealthReport:
        """Return a HealthReport indicating whether the database responds."""
        try:
            self._probe.ping()
        except (DatabaseError, OSError) as exc:
            logger.error("Database health probe failed: %s", exc)
            return HealthReport(status="degraded", database="error", is_healthy=False)

        return HealthReport(status="ok", database="ok", is_healthy=True)
