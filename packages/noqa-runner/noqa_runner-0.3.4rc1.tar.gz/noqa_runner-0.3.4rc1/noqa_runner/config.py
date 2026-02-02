"""Runner settings"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import sentry_sdk
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


class NoqaSettings(BaseSettings):
    """Base settings class with common configurations"""

    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    SENTRY_DSN: str | None = Field(default=None)

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


class RunnerSettings(NoqaSettings):
    """Settings for remote runner"""

    # Agent API configuration
    AGENT_API_URL: str = Field(
        default="https://agent.noqa.ai", description="Base URL for the agent API"
    )
    DEFAULT_APPIUM_URL: str = Field(
        default="http://localhost:4723",
        description="Default Appium URL for the agent API",
    )
    MAX_STEPS: int = Field(
        default=100, gt=0, description="Maximum number of steps for test execution"
    )


settings = RunnerSettings()

# Type alias for Sentry before_send callback
BeforeSendCallback = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any] | None]


def sentry_init(
    dsn: str | None = None,
    environment: str = "development",
    enable_logs: bool = False,
    log_level: str = "INFO",
    before_send: BeforeSendCallback | None = None,
):
    """Initialize Sentry with optional before_send callback."""
    if not dsn:
        return

    integrations = [
        AsyncioIntegration(),
        LoggingIntegration(sentry_logs_level=log_level),
    ]
    try:
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        integrations.append(FastApiIntegration())
    except Exception:
        # FastApiIntegration requires starlette, which may not be installed
        pass

    init_kwargs: dict[str, Any] = {
        "dsn": dsn,
        "environment": environment,
        "traces_sample_rate": 0.1,
        "enable_logs": enable_logs,
        "integrations": integrations,
    }
    if before_send:
        init_kwargs["before_send"] = before_send

    sentry_sdk.init(**init_kwargs)
