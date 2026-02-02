from __future__ import annotations

from typing import Literal

from noqa_runner.domain.models.actions.base import BaseAction


class RestartApp(BaseAction):
    """Restart the application"""

    name: Literal["restart_app"] = "restart_app"

    def get_action_description(self) -> str:
        return "Restart app"
