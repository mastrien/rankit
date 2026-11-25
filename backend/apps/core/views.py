"""Core HTTP views for Rankit API."""

from dataclasses import asdict

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import DatabaseHealthService


class HealthCheckView(APIView):
    """Return service and database readiness for Docker and CI probes."""

    authentication_classes = ()
    permission_classes = ()

    def get(self, request: Request) -> Response:
        """Return 200 OK when PostgreSQL responds or 503 when degraded."""
        report = DatabaseHealthService().check()
        http_status = (
            status.HTTP_200_OK if report.is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        payload = {"status": report.status, "database": report.database}
        return Response(payload, status=http_status)


def health_report_to_dict(service: DatabaseHealthService) -> dict[str, object]:
    """Serialize a health check report for diagnostic callers.

    Example:
        payload = health_report_to_dict(DatabaseHealthService())
    """
    return asdict(service.check())
