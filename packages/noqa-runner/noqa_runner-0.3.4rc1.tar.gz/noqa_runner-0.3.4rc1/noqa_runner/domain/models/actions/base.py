"""
Base schemas for mobile actions
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class BaseAction(BaseModel, ABC):
    name: str

    @abstractmethod
    def get_action_description(self) -> str:
        """Return a human-readable description of this action."""
        pass
