from __future__ import annotations

from typing import TYPE_CHECKING, Union

from pydantic import BaseModel, Field, create_model

from noqa_runner.domain.models.actions.activate_app import ActivateApp
from noqa_runner.domain.models.actions.background_app import BackgroundApp
from noqa_runner.domain.models.actions.input_text import InputText
from noqa_runner.domain.models.actions.long_tap import LongTap
from noqa_runner.domain.models.actions.open_url import OpenUrl
from noqa_runner.domain.models.actions.restart_app import RestartApp
from noqa_runner.domain.models.actions.scroll import Scroll
from noqa_runner.domain.models.actions.stop import Stop
from noqa_runner.domain.models.actions.swipe import Swipe
from noqa_runner.domain.models.actions.tap import Tap
from noqa_runner.domain.models.actions.terminate_app import TerminateApp
from noqa_runner.domain.models.actions.wait import Wait
from noqa_runner.domain.models.state.condition import ConditionUpdate

if TYPE_CHECKING:
    from noqa_runner.domain.models.state.condition import Condition


class ActionData(BaseModel):
    """Response schema for mobile actions"""

    action: Union[
        Tap,
        LongTap,
        InputText,
        Swipe,
        Scroll,
        Wait,
        Stop,
        ActivateApp,
        BackgroundApp,
        TerminateApp,
        RestartApp,
        OpenUrl,
    ] = Field(discriminator="name")
    reasoning: str = Field(
        description="Explanation of your decision and reasoning for this action"
    )
    conditions_updates: list[ConditionUpdate] | None = Field(
        default=None, description="List of test condition updates by alias"
    )

    @classmethod
    def with_constrained_conditions(
        cls, conditions: list[Condition]
    ) -> type[BaseModel]:
        """
        Create dynamic ActionData model with constrained condition aliases.

        This ensures LLM can only use valid alias values in conditions_updates.
        """
        condition_update_model = ConditionUpdate.with_constrained_aliases(
            conditions=conditions
        )

        return create_model(
            "ActionData",
            __base__=cls,
            conditions_updates=(
                list[condition_update_model] | None,
                Field(
                    default=None, description="List of test condition updates by alias"
                ),
            ),
        )
