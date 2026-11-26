"""Unit tests for core health service, HealthCheckView, and JSON logging."""

import json
import logging
import sys

import pytest
from django.db import DatabaseError
from rest_framework.test import APIRequestFactory

from apps.core.services import DatabaseHealthService
from apps.core.views import HealthCheckView
from config.logging import StructuredJsonLogFormatter


class HealthyDatabaseProbe:
    """Fake database probe that succeeds immediately."""

    def ping(self) -> None:
        return None


class FailingDatabaseProbe:
    """Fake database probe that simulates a PostgreSQL outage."""

    def ping(self) -> None:
        raise DatabaseError("simulated postgres connection failure")


@pytest.mark.unit
def test_health_service_returns_ok_when_probe_succeeds() -> None:
    service = DatabaseHealthService(probe=HealthyDatabaseProbe())
    report = service.check()

    assert report.is_healthy is True
    assert report.status == "ok"
    assert report.database == "ok"


@pytest.mark.unit
def test_health_service_returns_degraded_when_probe_fails() -> None:
    service = DatabaseHealthService(probe=FailingDatabaseProbe())
    report = service.check()

    assert report.is_healthy is False
    assert report.status == "degraded"
    assert report.database == "error"


@pytest.mark.unit
def test_health_check_view_returns_200_when_healthy() -> None:
    factory = APIRequestFactory()
    request = factory.get("/api/v1/health/")
    service = DatabaseHealthService(probe=HealthyDatabaseProbe())
    view = HealthCheckView.as_view(health_service=service)

    response = view(request)

    assert response.status_code == 200
    assert response.data == {"status": "ok", "database": "ok"}


@pytest.mark.unit
def test_health_check_view_returns_503_when_database_degraded() -> None:
    factory = APIRequestFactory()
    request = factory.get("/api/v1/health/")
    service = DatabaseHealthService(probe=FailingDatabaseProbe())
    view = HealthCheckView.as_view(health_service=service)

    response = view(request)

    assert response.status_code == 503
    assert response.data == {"status": "degraded", "database": "error"}


@pytest.mark.unit
def test_structured_json_log_formatter_emits_valid_json() -> None:
    formatter = StructuredJsonLogFormatter()
    record = logging.LogRecord(
        name="rankit.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="health check executed",
        args=(),
        exc_info=None,
    )

    parsed = json.loads(formatter.format(record))

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "rankit.test"
    assert parsed["message"] == "health check executed"
    assert "timestamp" in parsed


@pytest.mark.unit
def test_structured_json_log_formatter_includes_exception_traceback() -> None:
    formatter = StructuredJsonLogFormatter()
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="rankit.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=20,
        msg="failure recorded",
        args=(),
        exc_info=exc_info,
    )

    parsed = json.loads(formatter.format(record))

    assert parsed["level"] == "ERROR"
    assert "RuntimeError: boom" in parsed["exception"]
