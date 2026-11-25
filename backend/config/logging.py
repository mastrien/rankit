"""Structured JSON log formatter for backend observability."""

import json
import logging
from datetime import UTC, datetime
from typing import Any


class StructuredJsonLogFormatter(logging.Formatter):
    """Format log records as single-line JSON objects for machine parsing.

    Example:
        formatter = StructuredJsonLogFormatter()
        handler.setFormatter(formatter)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a LogRecord into a structured JSON string."""
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
