"""HTTP client manager - registry for cleanup"""

from __future__ import annotations

import asyncio
import atexit
import logging

from noqa_runner.infrastructure.adapters.http.base_client import BaseHttpClient

logger = logging.getLogger(__name__)


class HttpClientManager:
    """Registry for HTTP clients cleanup"""

    def __init__(self):
        self._clients: list[BaseHttpClient] = []

    def register(self, client: BaseHttpClient) -> BaseHttpClient:
        """Register client for automatic cleanup"""
        if client not in self._clients:
            self._clients.append(client)
        return client

    async def cleanup(self):
        """Cleanup all registered HTTP clients"""
        if not self._clients:
            return

        for client in self._clients:
            if hasattr(client, "cleanup"):
                await client.cleanup()


def _sync_cleanup():
    """Synchronous cleanup wrapper for atexit (no logging to avoid I/O errors)"""
    manager = http_manager

    # Run cleanup without logging
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(manager.cleanup())
        finally:
            loop.close()
    except Exception:
        pass  # Silent cleanup, logging may fail during shutdown


# Global registry
http_manager = HttpClientManager()

# Register automatic cleanup on exit
atexit.register(_sync_cleanup)
