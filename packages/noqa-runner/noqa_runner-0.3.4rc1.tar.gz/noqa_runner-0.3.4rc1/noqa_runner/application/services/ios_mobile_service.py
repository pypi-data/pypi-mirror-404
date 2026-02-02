"""iOS-specific mobile service implementation"""

from __future__ import annotations

import json
import time

from appium.webdriver.common.appiumby import AppiumBy

from noqa_runner.domain.models.state.screen import ActiveElement
from noqa_runner.logging_config import get_logger

from .base_mobile_service import BaseMobileService

logger = get_logger(__name__)


def get_appstore_url(app_store_id: str, country_code: str = "us") -> str:
    """Get App Store URL for a given app"""
    return f"https://apps.apple.com/{country_code}/app/{app_store_id}"


class IOSMobileService(BaseMobileService):
    """iOS-specific mobile service implementation"""

    def get_locator_strategy(self) -> str:
        """Get iOS locator strategy (IOS_PREDICATE)"""
        return AppiumBy.IOS_PREDICATE

    def _escape_predicate_string(self, value: str) -> str:
        """Escape string for iOS Predicate - escape backslashes and double quotes."""
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def get_locator(
        self, element: ActiveElement, *, for_input: bool = False
    ) -> str | None:
        """
        Generate iOS Predicate String for Appium element lookup.

        Args:
            element: ActiveElement to generate locator for
            for_input: If True, generate locator optimized for text input (without y coordinate)

        Returns:
            iOS Predicate string or None if element is not from Appium
        """
        if element.source != "appium" or not element.appium_data:
            return None

        # If valid id exists, use only it for locator
        if element.id:
            id_escaped = self._escape_predicate_string(element.id)
            return f"name == {id_escaped}"

        conditions: list[str] = []

        if element.appium_data.type in (
            "XCUIElementTypeTextField",
            "XCUIElementTypeSecureTextField",
        ):
            # For text fields, always include type OR condition to match both types
            conditions.append(
                '(type == "XCUIElementTypeTextField" OR type == "XCUIElementTypeSecureTextField")'
            )
        else:
            # For non-text-field elements, include type only when not for_input
            conditions.append(f'type == "{element.appium_data.type}"')

        # Add coordinates unless for_input is True
        if not for_input:
            # Add x/y coordinates for precise matching
            conditions.append(f"rect.y == {element.appium_data.y}")

        conditions.append(f"rect.x == {element.appium_data.x}")

        # Add label if present (most reliable identifier)
        if element.appium_data.label:
            label = self._escape_predicate_string(element.appium_data.label)
            conditions.append(f"label == {label}")

        # Add name if present
        if element.appium_data.name:
            name = self._escape_predicate_string(element.appium_data.name)
            conditions.append(f"name == {name}")

        # Add size coordinates (always included)
        conditions.append(f"rect.width == {element.appium_data.width}")
        conditions.append(f"rect.height == {element.appium_data.height}")

        return " AND ".join(conditions)

    def hide_keyboard(self) -> None:
        """Hide keyboard using iOS-specific approach"""
        element = self.client.find_element(
            by=AppiumBy.IOS_PREDICATE,
            locator="type CONTAINS 'TextField' or type CONTAINS 'TextView'",
        )
        if element:
            rect = json.loads(element.get_attribute("rect"))
            self.client.tap_by_coords(rect.get("x"), rect.get("y"))

    def _has_overlay_ui(self, xml_source: str) -> bool:
        """Check if XML contains iOS notification overlays"""
        return "NotificationShortLookView" in xml_source

    def install_app_testflight(
        self, app_bundle_id: str, app_store_id: str | None = None
    ) -> bool:
        """
        Install app via TestFlight by simulating user interaction.

        Args:
            app_bundle_id: The bundle ID of the app to install
            app_store_id: The TestFlight app store ID

        Returns:
            True if installation succeeded, False otherwise
        """
        # Remove existing app
        self.client.remove_app(app_bundle_id)
        self.client.terminate_app("com.apple.TestFlight")
        logger.info("Existing app removed", bundle_id=app_bundle_id)

        # Activate TestFlight app
        self.client.activate_app("com.apple.TestFlight")
        logger.info("TestFlight activated")

        initial_button_name = None

        # Wait for app to be installed
        max_wait_time = 40
        wait_start = 0
        while wait_start < max_wait_time:
            time.sleep(1)
            wait_start += 1

            try:
                xml_str = self.client.get_page_source()

                # Handle alerts (e.g., "Do you want to install this app?")
                if "XCUIElementTypeAlert" in xml_str:
                    alert_buttons = self.client.find_elements(
                        by=AppiumBy.XPATH,
                        locator="//XCUIElementTypeAlert//XCUIElementTypeButton",
                    )
                    if alert_buttons:
                        alert_buttons[-1].click()
                        continue

                main_buttons = self.client.find_elements(
                    by=AppiumBy.XPATH,
                    locator=f"//XCUIElementTypeOther[@name='{app_store_id}']//XCUIElementTypeButton",
                )
                if main_buttons:
                    main_button = main_buttons[-1]
                    if (
                        main_button.get_attribute("name")
                        and len(main_button.get_attribute("name")) > 2
                    ):
                        if not initial_button_name:
                            initial_button_name = main_button.get_attribute("name")
                        else:
                            self.client.terminate_app("com.apple.TestFlight")
                            time.sleep(1)
                            self.client.activate_app(app_bundle_id)
                            return True
                        # Get button coordinates and tap at center
                        rect = json.loads(main_button.get_attribute("rect"))
                        center_x = rect["x"] + rect["width"] // 2
                        center_y = rect["y"] + rect["height"] // 2
                        self.client.tap_by_coords(center_x, center_y)
                        continue

            except Exception:
                pass

        logger.error(
            "TestFlight installation timeout",
            bundle_id=app_bundle_id,
            timeout_seconds=max_wait_time,
        )
        return False

    def install_app_appstore(
        self, app_bundle_id: str, app_store_id: str | None = None
    ) -> bool | None:
        """
        Install app from App Store by simulating user interaction.

        Args:
            app_bundle_id: The bundle ID of the app to install
            app_store_id: The App Store ID

        Returns:
            True if installation succeeded, None if timeout
        """
        # Remove existing app
        self.client.remove_app(app_bundle_id)
        self.client.terminate_app("com.apple.AppStore")
        logger.info("Existing app removed", bundle_id=app_bundle_id)

        max_wait_time = 40
        wait_start = 0
        while wait_start < max_wait_time:
            time.sleep(1)
            wait_start += 1

            try:
                app_state = self.client.query_app_state(app_bundle_id)
                if app_state == 4:
                    logger.info(
                        "App installed and running",
                        bundle_id=app_bundle_id,
                        app_state=app_state,
                    )
                    return True

                appstore_state = self.client.query_app_state("com.apple.AppStore")
                if appstore_state != 4:
                    self.client.open_url(get_appstore_url(app_store_id=app_store_id))
                    continue

                # Get current page source
                xml_str = self.client.get_page_source()

                if "payment-sheet" in xml_str:
                    buttons = self.client.find_elements(
                        by=AppiumBy.XPATH,
                        locator="//XCUIElementTypeOther[@name='payment-sheet']//XCUIElementTypeButton",
                    )
                    if buttons:
                        buttons[-1].click()
                        continue

                if "AppStore.offerButton" in xml_str:
                    if (
                        "AppStore.offerButton[state=downloading]" in xml_str
                        or "AppStore.offerButton[state=loading]" in xml_str
                    ):
                        logger.info("App is downloading, waiting...")
                        continue
                    elif "AppStore.offerButton[state=open]" in xml_str:
                        open_button = self.client.find_element(
                            by=AppiumBy.XPATH,
                            locator="//XCUIElementTypeCell[contains(@name, 'AppStore.shelfItem.productTopLockup')]//XCUIElementTypeButton[@name='AppStore.offerButton[state=open]']",
                        )
                        if open_button:
                            self.client.terminate_app("com.apple.AppStore")
                            time.sleep(1)
                            self.client.activate_app(app_bundle_id)
                            continue
                    elif "AppStore.offerButton[state=redownload]" in xml_str:
                        main_button = self.client.find_element(
                            by=AppiumBy.XPATH,
                            locator="//XCUIElementTypeCell[contains(@name, 'AppStore.shelfItem.productTopLockup')]//XCUIElementTypeButton[@name='AppStore.offerButton[state=redownload]']",
                        )
                        if main_button:
                            main_button.click()
                            continue
                    elif "AppStore.offerButton[state=get]" in xml_str:
                        main_button = self.client.find_element(
                            by=AppiumBy.XPATH,
                            locator="//XCUIElementTypeCell[contains(@name, 'AppStore.shelfItem.productTopLockup')]//XCUIElementTypeButton[@name='AppStore.offerButton[state=get]']",
                        )
                        if main_button:
                            main_button.click()
                            continue
            except Exception as e:
                logger.info("Transient error during installation check", error=str(e))

        logger.error(
            "App Store installation timeout",
            bundle_id=app_bundle_id,
            timeout_seconds=max_wait_time,
        )
        return None
