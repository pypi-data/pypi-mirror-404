"""Platform enumeration"""

from __future__ import annotations

from enum import Enum


class Platform(str, Enum):
    """Mobile platform for test execution"""

    IOS = "ios"
    ANDROID = "android"
