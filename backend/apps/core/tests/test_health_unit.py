"""Unit tests for core health service and structured JSON logging."""

import json
import logging

import pytest
from django.db import DatabaseError

from apps.core.services import DatabaseHealthService
from apps.core.views import health_report_to_dict
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
def test_health_report_to_dict_serializes_report() -> None:
    service = DatabaseHealthService(probe=HealthyDatabaseProbe())
    payload = health_report_to_dict(service)

    assert payload == {"status": "ok", "database": "ok", "is_healthy": True}


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
