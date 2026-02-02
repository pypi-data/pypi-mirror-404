from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic.json_schema import SkipJsonSchema

from noqa_runner.domain.models.actions.base import BaseAction
from noqa_runner.domain.models.state.screen import ActiveElement


class LongTap(BaseAction):
    """Long tap (press and hold) on a mobile element"""

    name: Literal["long_tap"] = "long_tap"
    element_number: int = Field(
        description="Number of the element to long tap from the elements list", ge=1
    )
    duration: int = Field(
        description="Duration of the long tap in seconds (from 3 to 10)", ge=3, le=10
    )
    element: SkipJsonSchema[ActiveElement | None] = Field(default=None)

    def get_action_description(self) -> str:
        """Get description of long tap action"""
        return f"Long tapped on element: {self.element.string_description} for {self.duration} seconds"
