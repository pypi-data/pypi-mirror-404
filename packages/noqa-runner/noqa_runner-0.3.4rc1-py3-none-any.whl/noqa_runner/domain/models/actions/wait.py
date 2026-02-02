from __future__ import annotations

from typing import Literal

from noqa_runner.domain.models.actions.base import BaseAction


class Wait(BaseAction):
    """Wait for app processing (loading, transitions, etc.)"""

    name: Literal["wait"] = "wait"

    def get_action_description(self) -> str:
        """Get description of wait action"""
        return "Waiting 3 seconds"
