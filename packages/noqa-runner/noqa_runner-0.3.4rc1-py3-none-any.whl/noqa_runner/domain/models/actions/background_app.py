from __future__ import annotations

from typing import Literal

from noqa_runner.domain.models.actions.base import BaseAction


class BackgroundApp(BaseAction):
    """Send app to background"""

    name: Literal["background_app"] = "background_app"

    def get_action_description(self) -> str:
        return "Background app"
