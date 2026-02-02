from __future__ import annotations

import random
from typing import Literal

from pydantic import BaseModel, Field, create_model, model_validator
from pydantic.json_schema import SkipJsonSchema
from slugify import slugify


class ConditionUpdate(BaseModel):
    """Condition update model for LLM responses"""

    alias: str = Field(description="Alias of the condition to update")
    is_verified: bool = Field(description="Whether condition is verified (true/false)")
    evidence: str | None = Field(
        default=None,
        description="Evidence for the verification, or null if no evidence",
    )
    confidence: int | None = Field(
        default=None, ge=0, le=100, description="Confidence of the evidence (0-100)"
    )

    @classmethod
    def with_constrained_aliases(
        cls, conditions: list[Condition]
    ) -> type[ConditionUpdate]:
        """
        Create a dynamic ConditionUpdate model with Literal type for aliases.

        This constrains LLM output to only valid alias values from the test conditions.
        """
        if not conditions:
            return cls

        aliases = tuple(c.alias for c in conditions if c.alias)

        if not aliases:
            return cls

        alias_literal = Literal[aliases]  # type: ignore

        return create_model(
            "ConditionUpdate",
            __base__=cls,
            alias=(
                alias_literal,
                Field(
                    description=f"Alias of the condition to update. Valid values: {', '.join(aliases)}"
                ),
            ),
        )


class Condition(BaseModel):
    """Single condition update schema"""

    condition: str = Field(description="Test condition to update")
    alias: str = Field(
        default="",
        description="Short unique identifier for the condition (e.g. 'login_success')",
    )
    is_verified: bool = Field(
        default=False, description="Whether condition is verified (true/false)"
    )
    evidence: str | None = Field(
        default=None,
        description="Evidence for the verification, or null if no evidence",
    )
    step_number: SkipJsonSchema[int | None] = Field(
        default=None, description="Step number where evidence was found, or null"
    )
    confidence: int | None = Field(
        default=None, ge=0, le=100, description="Confidence of the evidence (0-100)"
    )

    @model_validator(mode="after")
    def ensure_alias(self) -> "Condition":
        """Generate alias from condition if not provided, with random suffix to avoid collisions"""
        if not self.alias:
            base_slug = slugify(self.condition, separator="_", max_length=26)
            random_suffix = random.randint(
                100, 999
            )  # nosec B311 - not for cryptographic use
            self.alias = f"{base_slug}_{random_suffix}"
        return self

    def __str__(self):
        status = "✅" if self.is_verified else "❌"
        return f"{status}({self.confidence or 0}%) [{self.alias}] {self.condition} ({self.evidence})"
