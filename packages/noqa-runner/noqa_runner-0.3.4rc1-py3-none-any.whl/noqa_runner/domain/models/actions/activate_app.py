from __future__ import annotations

from typing import Literal

from noqa_runner.domain.models.actions.base import BaseAction


class ActivateApp(BaseAction):
    """Activate the application"""

    name: Literal["activate_app"] = "activate_app"

    def get_action_description(self) -> str:
        return "Activate app"
