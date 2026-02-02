"""Custom exceptions for noqa runner"""

from __future__ import annotations


class RunnerException(Exception):
    """Base exception for runner errors"""

    pass


class AppiumError(RunnerException):
    """Appium error"""

    def __init__(self, appium_url: str, original_error: str) -> None:
        self.appium_url = appium_url
        self.original_error = original_error
        message = f"❌ Appium error at {appium_url}. " f"Error: {original_error}"
        super().__init__(message)


class BuildNotFoundError(RunnerException):
    """Build file not found"""

    def __init__(self, build_path: str) -> None:
        self.build_path = build_path
        message = (
            f"❌ Build file not found at {build_path}. "
            f"Please check the path and try again."
        )
        super().__init__(message)


class AgentAPIError(RunnerException):
    """Agent API error"""

    def __init__(self, status_code: int, error_message: str) -> None:
        self.status_code = status_code
        self.error_message = error_message
        message = (
            f"❌ Agent API error (HTTP {status_code}). " f"Details: {error_message}"
        )
        super().__init__(message)


class InvalidTokenError(AgentAPIError):
    """Invalid noqa API token"""

    def __init__(self) -> None:
        super().__init__(
            status_code=401,
            error_message="Invalid noqa API token. Please check your --noqa-api-token and try again.",
        )
