from __future__ import annotations

from typing import Literal

from pydantic import AnyUrl, Field

from noqa_runner.domain.models.actions.base import BaseAction


class OpenUrl(BaseAction):
    """Navigate to specific URL within the app"""

    name: Literal["open_url"] = "open_url"
    url: AnyUrl = Field(
        description="URL to navigate to (must contain protocol like https:// or myapp://)"
    )

    def get_action_description(self) -> str:
        """Get description of open URL action"""
        return f"Opened URL: {self.url}"
