from __future__ import annotations

import abc
import typing

if typing.TYPE_CHECKING:
    import httpx


class BaseHTTPAdapter(abc.ABC):
    """Abstract base class for HTTP adapters."""

    @abc.abstractmethod
    def request(
        self,
        method: str,
        url: str,
        params: dict[str, typing.Any] | None = None,
    ) -> httpx.Response:
        """Make an HTTP request."""
        ...

    @abc.abstractmethod
    def close(self) -> None:
        """Close the HTTP session."""
        ...


class AsyncBaseHTTPAdapter(abc.ABC):
    """Abstract base class for async HTTP adapters."""

    @abc.abstractmethod
    async def request(
        self,
        method: str,
        url: str,
        params: dict[str, typing.Any] | None = None,
    ) -> httpx.Response:
        """Make an async HTTP request."""
        ...

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the HTTP session."""
        ...
