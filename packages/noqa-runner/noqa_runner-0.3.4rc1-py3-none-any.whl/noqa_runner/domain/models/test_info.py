"""Domain models for test information"""

from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field


class RunnerTestInfo(BaseModel):
    """Test case information for runner"""

    test_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique test identifier"
    )
    case_instructions: str = Field(description="Natural language test instructions")
    case_name: str = Field(default="", description="Test case name")
