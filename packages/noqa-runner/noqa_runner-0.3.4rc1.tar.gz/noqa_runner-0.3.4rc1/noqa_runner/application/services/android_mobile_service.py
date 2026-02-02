"""Android-specific mobile service implementation"""

from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from noqa_runner.domain.models.state.screen import ActiveElement
from noqa_runner.logging_config import get_logger

from .base_mobile_service import BaseMobileService

logger = get_logger(__name__)


class AndroidMobileService(BaseMobileService):
    """Android-specific mobile service implementation"""

    def get_locator_strategy(self) -> str:
        """Get Android locator strategy (ANDROID_UIAUTOMATOR)"""
        return AppiumBy.ANDROID_UIAUTOMATOR

    def _escape_uiautomator_string(self, value: str) -> str:
        """
        Escape string for Android UIAutomator.

        Escapes backslashes first, then control characters (newline, tab, carriage return,
        backspace, formfeed), and finally double quotes to ensure proper UIAutomator parsing.

        Returns string wrapped in double quotes.
        """
        # Escape backslashes first to avoid double-escaping
        escaped = value.replace("\\", "\\\\")
        # Escape control characters by replacing with literal escape sequences
        escaped = escaped.replace("\n", "\\n")
        escaped = escaped.replace("\t", "\\t")
        escaped = escaped.replace("\r", "\\r")
        escaped = escaped.replace("\b", "\\b")
        escaped = escaped.replace("\f", "\\f")
        # Escape double quotes last
        escaped = escaped.replace('"', '\\"')
        return f'"{escaped}"'

    def get_locator(
        self, element: ActiveElement, *, for_input: bool = False
    ) -> str | None:
        """
        Generate Android UIAutomator selector for Appium element lookup.

        Args:
            element: ActiveElement to generate locator for
            for_input: If True, generate locator optimized for text input

        Returns:
            UIAutomator selector string or None if element is not from Appium

        Example UIAutomator selectors:
            new UiSelector().text("Login")
            new UiSelector().resourceId("com.example:id/username")
            new UiSelector().className("android.widget.EditText").instance(0)
        """
        if element.source != "appium" or not element.appium_data:
            return None

        # If valid resource-id exists, use it (most reliable for Android)
        if element.id:
            id_escaped = self._escape_uiautomator_string(element.id)
            return f"new UiSelector().resourceId({id_escaped})"

        # Build selector using available attributes
        selectors: list[str] = []

        # Add class name if present
        if element.appium_data.type:
            type_escaped = self._escape_uiautomator_string(element.appium_data.type)
            selectors.append(f"className({type_escaped})")

        # Add text if present (for text fields, this is the content)
        if element.appium_data.value and not for_input:
            # Don't use value for input fields as it may change during typing
            value_escaped = self._escape_uiautomator_string(element.appium_data.value)
            selectors.append(f"text({value_escaped})")

        # Add content description if present (Android's accessibility label)
        if element.appium_data.label:
            label_escaped = self._escape_uiautomator_string(element.appium_data.label)
            selectors.append(f"description({label_escaped})")

        if not selectors:
            return None

        # Combine selectors
        selector = "new UiSelector()." + ".".join(selectors)
        return selector

    def _has_overlay_ui(self, xml_source: str) -> bool:
        """Check if XML contains Android notification overlays"""
        # Android notifications typically have these package names
        return (
            "com.android.systemui" in xml_source
            or "StatusBarNotification" in xml_source
        )
