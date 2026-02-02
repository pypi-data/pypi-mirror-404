from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic.json_schema import SkipJsonSchema

from noqa_runner.domain.models.actions.base import BaseAction
from noqa_runner.domain.models.state.screen import ActiveElement


class Swipe(BaseAction):
    """Swipe on a mobile element"""

    name: Literal["swipe"] = "swipe"
    element_number: int = Field(
        description="Number of the element to swipe from the elements list", ge=1
    )
    direction: Literal["up", "down", "left", "right"] = Field(
        description="Direction to swipe"
    )
    element: SkipJsonSchema[ActiveElement | None] = None

    def get_action_description(self) -> str:
        """Get description of swipe action"""
        return f"Swiped {self.direction} on element: {self.element.string_description}"
