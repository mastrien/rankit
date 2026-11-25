"""Integration tests for core API endpoints against PostgreSQL."""

import pytest
from rest_framework.test import APIClient


@pytest.mark.integration
@pytest.mark.django_db
def test_health_endpoint_returns_ok_with_real_postgres() -> None:
    client = APIClient()
    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
