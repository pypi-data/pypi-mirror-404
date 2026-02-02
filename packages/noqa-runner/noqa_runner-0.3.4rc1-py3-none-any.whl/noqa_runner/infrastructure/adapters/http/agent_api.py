"""Agent API client using httpx"""

from __future__ import annotations

import functools

import httpx

from noqa_runner.domain.exceptions import AgentAPIError, InvalidTokenError
from noqa_runner.domain.models.state.test_state import TestState
from noqa_runner.infrastructure.adapters.http.base_client import BaseHttpClient
from noqa_runner.logging_config import get_logger
from noqa_runner.utils.retry_decorator import with_retry

logger = get_logger(__name__)


def handle_agent_api_errors(func):
    """Decorator to catch HTTP errors and convert them to AgentAPIError or InvalidTokenError"""

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            # Try to extract status code and error message from httpx exceptions
            status_code = (
                getattr(e, "response", None)
                and getattr(e.response, "status_code", None)
                or 0
            )
            error_message = str(e)

            if hasattr(e, "response") and hasattr(e.response, "text"):
                error_message = e.response.text or error_message

            logger.error(
                "agent_api_error",
                method=func.__name__,
                status_code=status_code,
                error=error_message,
                exc_info=True,
            )

            # Handle 401 Unauthorized
            if status_code == 401:
                raise InvalidTokenError

            raise AgentAPIError(status_code=status_code, error_message=error_message)

    return wrapper


class AgentApiAdapter(BaseHttpClient):
    """Adapter for Agent API operations"""

    def __init__(self, base_url: str, api_token: str):
        super().__init__(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_token}"},
            timeout=30.0,
            limits=httpx.Limits(
                max_connections=10, max_keepalive_connections=5, keepalive_expiry=30.0
            ),
            verify=False,
        )

    @handle_agent_api_errors
    @with_retry(max_attempts=5)
    async def prepare_test(self, state: TestState) -> TestState:
        """Prepare test by sending state to agent API"""
        response = await self._post("/v1/agent/preparation", json=state.model_dump())
        response.raise_for_status()
        return TestState(**response.json())

    @handle_agent_api_errors
    @with_retry(max_attempts=5)
    async def execute_step(self, state: TestState) -> TestState:
        """Execute test step by sending state to agent API"""
        response = await self._post("/v1/agent/step", json=state.model_dump())
        response.raise_for_status()
        return TestState(**response.json())

    @handle_agent_api_errors
    @with_retry(max_attempts=5)
    async def get_screenshot_urls(
        self, test_id: str, step_number: int
    ) -> tuple[str, str]:
        """Get presigned URLs for screenshot upload

        Returns:
            Tuple of (upload_url, download_url)
        """
        response = await self._get(
            "/v1/agent/screenshot-urls",
            params={"test_id": test_id, "step_number": step_number},
        )
        response.raise_for_status()
        data = response.json()

        return data["upload_url"], data["download_url"]
