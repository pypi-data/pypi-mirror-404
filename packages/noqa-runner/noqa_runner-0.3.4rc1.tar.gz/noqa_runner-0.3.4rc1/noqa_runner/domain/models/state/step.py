from __future__ import annotations

from pydantic import BaseModel, Field

from noqa_runner.domain.models.actions.action_data import ActionData
from noqa_runner.domain.models.state.screen import Screen


class Step(BaseModel):
    """Domain model for a single test step with screen state and action results"""

    number: int = Field(default=1, ge=1, description="Step number in the test sequence")
    screen: Screen | None = Field(default=None)

    previous_action_validation: str | None = Field(
        default=None, description="Validation result for previous action"
    )
    screen_description: str | None = Field(
        default=None, description="Screen description from validation"
    )
    action_data: ActionData | None = Field(
        default=None, description="Action performed on this step"
    )
    stop_validations: list[str] = Field(
        default_factory=list,
        description="History of stop validation feedback messages for this step",
    )
