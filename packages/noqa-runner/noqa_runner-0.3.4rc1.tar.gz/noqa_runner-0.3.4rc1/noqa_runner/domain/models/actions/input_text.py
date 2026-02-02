from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field, field_validator
from pydantic.json_schema import SkipJsonSchema

from noqa_runner.domain.models.actions.base import BaseAction
from noqa_runner.domain.models.state.screen import ActiveElement


class InputText(BaseAction):
    """Input text into a mobile element"""

    model_config = ConfigDict(validate_assignment=True)

    name: Literal["input_text"] = "input_text"
    element_number: int = Field(
        description="Number of the element to input text into", ge=1
    )
    text: str = Field(description="Text to input into the element", min_length=1)
    element: SkipJsonSchema[ActiveElement | None] = None

    @field_validator("element")
    @classmethod
    def validate_element_type(
        cls, element: ActiveElement | None
    ) -> ActiveElement | None:
        """Ensure input targets only text input elements"""
        if element is not None and element.type != "TextInputField":
            raise ValueError(
                "Input action can only be performed on TextInputField elements"
            )
        return element

    def get_action_description(self) -> str:
        """Get description of input text action"""
        return f"Input text '{self.text}' in element: {self.element.string_description}"
