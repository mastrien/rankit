"""Thin HTTP JSON transport with explicit timeouts and bounded retries on GET."""

import json
import time
import urllib.request
from collections.abc import Callable
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request


class HttpTransportError(Exception):
    """Raised when an outbound provider HTTP call fails or returns invalid JSON."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class HttpTransport(Protocol):
    """Abstraction over outbound HTTP JSON requests for external media providers."""

    def request_json(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ) -> Any:
        """Execute an HTTP request and parse the JSON response."""


def _default_open(request: Request, timeout_seconds: float) -> Any:
    return urllib.request.urlopen(request, timeout=timeout_seconds)


class UrllibHttpTransport:
    """Stdlib urllib transport enforcing timeouts and idempotent GET retries.

    Example:
        transport = UrllibHttpTransport(timeout_seconds=5.0, max_retries=2)
    """

    def __init__(
        self,
        timeout_seconds: float = 5.0,
        max_retries: int = 2,
        backoff_seconds: float = 0.25,
        opener: Callable[[Request, float], Any] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._opener = opener
        self._sleeper = sleeper

    def _sleep_backoff(self, attempt: int) -> None:
        sleep_fn = self._sleeper or time.sleep
        sleep_fn(self._backoff_seconds * (2**attempt))

    def _perform_request(self, request: Request) -> Any:
        open_fn = self._opener or _default_open
        with open_fn(request, self._timeout_seconds) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)

    def request_json(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ) -> Any:
        """Execute HTTP method against url with retry/backoff only on GET 5xx/network faults."""
        normalized_method = method.upper()
        attempt = 0
        while True:
            request = Request(url, data=body, headers=headers or {}, method=normalized_method)
            can_retry = normalized_method == "GET" and attempt < self._max_retries
            try:
                return self._perform_request(request)
            except HTTPError as exc:
                if exc.code >= 500 and can_retry:
                    self._sleep_backoff(attempt)
                    attempt += 1
                    continue
                raise HttpTransportError(
                    f"Erro HTTP {exc.code} ao consultar {url!r} (esperado 2xx).",
                    status_code=exc.code,
                ) from exc
            except (URLError, TimeoutError) as exc:
                if can_retry:
                    self._sleep_backoff(attempt)
                    attempt += 1
                    continue
                raise HttpTransportError(
                    f"Falha de rede/timeout ao consultar {url!r}: {exc}.",
                ) from exc
            except json.JSONDecodeError as exc:
                raise HttpTransportError(
                    f"Resposta JSON inválida recebida de {url!r}.",
                ) from exc
