"""Base HTTP client with common functionality"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx


class BaseHttpClient:
    """Base class for HTTP clients with lazy initialization and cleanup"""

    def __init__(self, **client_kwargs: Any) -> None:
        """Initialize with httpx.AsyncClient kwargs

        Default timeout is 10.0 seconds. Subclasses can override it by passing timeout parameter.
        Individual requests can override timeout by passing timeout parameter to request methods.
        """
        # Set default timeout if not provided
        if "timeout" not in client_kwargs:
            client_kwargs["timeout"] = 10.0

        self._client_kwargs = client_kwargs
        self._client: httpx.AsyncClient | None = None
        self._client_lock = asyncio.Lock()

    async def _get_http(self) -> httpx.AsyncClient:
        """Get or create HTTP client (lazy initialization)"""
        async with self._client_lock:
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(**self._client_kwargs)
        return self._client

    async def cleanup(self):
        """Close HTTP client"""
        async with self._client_lock:
            if self._client and not self._client.is_closed:
                try:
                    await self._client.aclose()
                except RuntimeError:
                    # Event loop is closed, skip cleanup
                    pass
                finally:
                    self._client = None

    async def __aenter__(self):
        """Enter async context"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup"""
        await self.cleanup()

    # Helper methods for HTTP requests
    async def _get(self, *args, **kwargs) -> httpx.Response:
        """GET request using lazy-initialized client"""
        client = await self._get_http()
        return await client.get(*args, **kwargs)

    async def _head(self, *args, **kwargs) -> httpx.Response:
        """HEAD request using lazy-initialized client"""
        client = await self._get_http()
        return await client.head(*args, **kwargs)

    async def _post(self, *args, **kwargs) -> httpx.Response:
        """POST request using lazy-initialized client"""
        client = await self._get_http()
        return await client.post(*args, **kwargs)

    async def _put(self, *args, **kwargs) -> httpx.Response:
        """PUT request using lazy-initialized client"""
        client = await self._get_http()
        return await client.put(*args, **kwargs)

    async def _delete(self, *args, **kwargs) -> httpx.Response:
        """DELETE request using lazy-initialized client"""
        client = await self._get_http()
        return await client.delete(*args, **kwargs)

    async def _patch(self, *args, **kwargs) -> httpx.Response:
        """PATCH request using lazy-initialized client"""
        client = await self._get_http()
        return await client.patch(*args, **kwargs)

    def stream(self, *args, **kwargs) -> _StreamContext:
        """Stream request using lazy-initialized client (returns context manager)"""
        return self._StreamContext(self, *args, **kwargs)

    class _StreamContext:
        """Context manager for streaming requests"""

        def __init__(self, parent: "BaseHttpClient", *args, **kwargs) -> None:
            self.parent = parent
            self.args = args
            self.kwargs = kwargs
            self.client: httpx.AsyncClient | None = None
            self.stream: Any | None = None

        async def __aenter__(self):
            self.client = await self.parent._get_http()
            self.stream = self.client.stream(*self.args, **self.kwargs)
            return await self.stream.__aenter__()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self.stream:
                return await self.stream.__aexit__(exc_type, exc_val, exc_tb)
