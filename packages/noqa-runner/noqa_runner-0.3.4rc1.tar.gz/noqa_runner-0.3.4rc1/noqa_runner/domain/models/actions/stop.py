from __future__ import annotations

from typing import Literal

from pydantic import Field

from noqa_runner.domain.models.actions.base import BaseAction


class Stop(BaseAction):
    """Stop test execution with success/failure status"""

    name: Literal["stop"] = "stop"
    is_success: bool = Field(
        description="Whether the test case was completed successfully"
    )

    def get_action_description(self) -> str:
        """Get description of stop action"""
        return "Test complete"
