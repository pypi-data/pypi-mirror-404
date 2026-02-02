"""Generic HTTP operations using httpx"""

from __future__ import annotations

from typing import AsyncIterator

import httpx

from noqa_runner.infrastructure.adapters.http.base_client import BaseHttpClient
from noqa_runner.infrastructure.adapters.http.client_manager import http_manager
from noqa_runner.utils.retry_decorator import with_retry

DOWNLOAD_CHUNK_SIZE_MB = UPLOAD_CHUNK_SIZE_MB = 10


class GenericHttpAdapter(BaseHttpClient):
    """Generic HTTP adapter for one-off requests

    Note: This adapter supports async context manager usage.
    For one-off requests, you can use:
        async with GenericHttpAdapter() as http:
            await http.download_to_temp_file(url)

    Or use the singleton instance for convenience:
        from noqa_runner.infrastructure.adapters.http.generic import generic_adapter
        await generic_adapter.download_to_temp_file(url)
    """

    def __init__(self):
        super().__init__(
            timeout=60.0, limits=httpx.Limits(max_connections=100), http2=True
        )

    @with_retry(max_attempts=3, exceptions=(httpx.HTTPError,))
    async def get_content_length(self, url: str) -> int:
        """Get content length from presigned URL using GET with streaming

        Uses GET instead of HEAD because presigned URLs are signed specifically for GET.
        With stream(), headers are received immediately without downloading the full file.
        """
        async with self.stream("GET", url) as response:
            response.raise_for_status()
            content_length = response.headers.get("Content-Length")
            if content_length is None:
                raise ValueError(f"Content-Length header not found for URL: {url}")
            return int(content_length)

    async def stream_download(
        self, url: str, chunk_size: int | None = None
    ) -> AsyncIterator[bytes]:
        """Stream download from URL as async iterator without saving to disk"""
        if chunk_size is None:
            chunk_size = DOWNLOAD_CHUNK_SIZE_MB * 1024 * 1024

        async with self.stream("GET", url) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                yield chunk

    @with_retry(max_attempts=3, exceptions=(httpx.HTTPError,))
    async def upload_file_chunks(
        self,
        url: str,
        data_iterator: AsyncIterator[bytes],
        content_length: int | None = None,
    ) -> None:
        """Upload file in chunks using streaming"""
        headers = {}
        if content_length is not None:
            headers["Content-Length"] = str(content_length)

        response = await self._put(
            url, content=data_iterator, headers=headers, timeout=120
        )
        response.raise_for_status()

    @with_retry(max_attempts=2, exceptions=(httpx.HTTPError,))
    async def upload_bytes(
        self, url: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> None:
        """Upload bytes directly to URL (e.g., presigned URL)"""
        # For presigned URLs, only send Content-Type header (as specified in signature)
        response = await self._put(
            url, content=data, headers={"Content-Type": content_type}
        )
        response.raise_for_status()


# Singleton instance - auto-registered for cleanup
generic_adapter = http_manager.register(GenericHttpAdapter())
