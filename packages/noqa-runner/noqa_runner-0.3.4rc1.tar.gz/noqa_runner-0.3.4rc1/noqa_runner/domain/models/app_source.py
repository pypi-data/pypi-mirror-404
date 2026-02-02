"""Application source enumeration"""

from __future__ import annotations

from enum import Enum


class AppSource(str, Enum):
    """Source for the application to be tested"""

    FILE = "file"
    TESTFLIGHT = "testflight"
    APPSTORE = "appstore"
