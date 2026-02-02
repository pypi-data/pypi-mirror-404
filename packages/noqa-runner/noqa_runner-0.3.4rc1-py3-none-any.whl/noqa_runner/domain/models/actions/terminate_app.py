from __future__ import annotations

from typing import Literal

from noqa_runner.domain.models.actions.base import BaseAction


class TerminateApp(BaseAction):
    """Terminate the application"""

    name: Literal["terminate_app"] = "terminate_app"

    def get_action_description(self) -> str:
        """Get description of terminate app action"""
        return "Terminated app"
