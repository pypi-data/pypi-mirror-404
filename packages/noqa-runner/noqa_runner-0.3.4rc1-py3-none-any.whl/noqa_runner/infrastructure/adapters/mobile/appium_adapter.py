from __future__ import annotations

import functools
import time
from typing import List

from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.client_config import AppiumClientConfig
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.remote.webelement import WebElement

from noqa_runner.domain.exceptions import AppiumError
from noqa_runner.logging_config import get_logger
from noqa_runner.utils.retry_decorator import with_retry

logger = get_logger(__name__)


def handle_appium_errors(func):
    """Decorator to catch Appium errors and convert them to AppiumError"""

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except WebDriverException as e:
            logger.error(
                "appium_command_error",
                command=func.__name__,
                error=str(e),
                exc_info=True,
            )
            raise AppiumError(
                appium_url=self.appium_url, original_error=f"{func.__name__}: {str(e)}"
            )

    return wrapper


class AppiumClient:
    """Appium client adapter for mobile automation (context manager)

    Supports both local Appium and remote execution (BrowserStack, etc.) via client_config.
    """

    driver: webdriver.Remote
    resolution: dict
    _capabilities: dict | None
    _platform_name: str | None

    @with_retry(
        max_attempts=3, min_wait=1, max_wait=3, exceptions=(WebDriverException,)
    )
    def __init__(
        self,
        appium_url: str,
        appium_capabilities: dict | None = None,
        client_config: AppiumClientConfig | dict | None = None,
    ):
        """
        Initialize Appium client.

        Args:
            appium_url: Appium server URL (local or remote hub like BrowserStack)
            appium_capabilities: Appium capabilities dict
            client_config: Optional AppiumClientConfig or dict for authentication
                           (e.g., BrowserStack username/password)
        """
        self.appium_url = appium_url
        self.appium_capabilities = appium_capabilities

        # Convert dict to AppiumClientConfig if needed
        if isinstance(client_config, dict):
            self.client_config = AppiumClientConfig(**client_config)
        else:
            self.client_config = client_config

        self._capabilities = None
        self._platform_name = None

        logger.info(
            "Initializing Appium session",
            appium_url=appium_url,
            has_client_config=self.client_config is not None,
        )

        # Initialize driver immediately with retry
        try:
            driver_kwargs = {
                "command_executor": self.appium_url,
                "options": AppiumOptions().load_capabilities(
                    self.appium_capabilities or {}
                ),
            }

            # Add client_config if provided (for remote auth like BrowserStack)
            if self.client_config is not None:
                driver_kwargs["client_config"] = self.client_config

            self.driver = webdriver.Remote(**driver_kwargs)
            self.driver.implicitly_wait(5)
            self.resolution = self.driver.get_window_size()
        except Exception as e:
            # Any other error during driver initialization
            raise AppiumError(appium_url=self.appium_url, original_error=str(e))

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup driver"""
        self.close()
        return False

    @property
    def capabilities(self) -> dict:
        """Get driver capabilities"""
        if self._capabilities is None:
            self._capabilities = self.driver.capabilities
        return self._capabilities

    @property
    def platform_name(self) -> str:
        """Get platform name (iOS or Android)"""
        if self._platform_name is None:
            self._platform_name = self.capabilities.get("platformName", "iOS").lower()
        return self._platform_name

    @handle_appium_errors
    @with_retry(max_attempts=3)
    def get_page_source(self) -> str:
        """Get page source XML from driver"""
        return self.driver.page_source

    @handle_appium_errors
    def find_element(self, by: str, locator: str):
        """Find single element by locator strategy"""
        try:
            element = self.driver.find_element(by, locator)
            return element
        except Exception:
            logger.debug(f"Element with locator '{locator}' (by={by}) not found")
            return None

    @handle_appium_errors
    def find_elements(self, by: str, locator: str) -> List[WebElement]:
        """Find multiple elements by locator strategy"""
        try:
            elements = self.driver.find_elements(by, locator)
            return elements
        except Exception:
            logger.debug(f"Elements with locator '{locator}' (by={by}) not found")
            return []

    @handle_appium_errors
    def tap_by_coords(self, x: int, y: int) -> None:
        """Tap at specific coordinates"""
        self.driver.tap([(x, y)])

    @handle_appium_errors
    @with_retry(
        max_attempts=3,
        min_wait=1,
        max_wait=2,
        exceptions=(StaleElementReferenceException,),
    )
    def tap_element(self, by: str, locator: str) -> bool:
        """Tap element by locator strategy"""
        try:
            element = self.driver.find_element(by, locator)
        except Exception:
            logger.debug(f"Element with locator '{locator}' (by={by}) not found")
            return False

        element.click()
        return True

    @handle_appium_errors
    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration_ms: int = 1000,
    ) -> None:
        """Swipe from start coordinates to end coordinates

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration_ms: Swipe duration in milliseconds (default 1000)
        """
        self.driver.swipe(start_x, start_y, end_x, end_y, duration_ms)

    @handle_appium_errors
    def open_url(self, url: str) -> None:
        """Navigate to URL"""
        self.driver.get(url)

    def accept_system_alert(self) -> None:
        """Accept system alert"""
        self.driver.switch_to.alert.accept()

    def dismiss_system_alert(self) -> None:
        """Dismiss system alert"""
        self.driver.switch_to.alert.dismiss()

    @handle_appium_errors
    @with_retry(max_attempts=3)
    def get_screenshot(self) -> str:
        """Get current screenshot as base64"""
        return self.driver.get_screenshot_as_base64()

    @handle_appium_errors
    @with_retry(
        max_attempts=3,
        min_wait=1,
        max_wait=2,
        exceptions=(StaleElementReferenceException,),
    )
    def send_keys(self, by: str, locator: str, text: str) -> bool:
        """Input text into element. Clears the field before input."""
        try:
            element = self.driver.find_element(by, locator)
        except Exception:
            logger.debug(f"Element with locator '{locator}' (by={by}) not found")
            return False

        if element.get_attribute("value"):
            element.clear()
        element.send_keys(text)
        return True

    @handle_appium_errors
    def get_alert_text(self) -> str | None:
        """Get alert text"""
        try:
            return self.driver.switch_to.alert.text
        except Exception:
            return None

    @handle_appium_errors
    @with_retry(max_attempts=3)
    def activate_app(self, bundle_id: str) -> None:
        """Activate app by bundle ID"""
        self.driver.activate_app(bundle_id)

    @handle_appium_errors
    @with_retry(max_attempts=3)
    def terminate_app(self, bundle_id: str) -> None:
        """Terminate app by bundle ID"""
        self.driver.terminate_app(bundle_id)

    @handle_appium_errors
    @with_retry(max_attempts=3)
    def background_app(self) -> None:
        """Background app"""
        self.driver.background_app(-1)

    @handle_appium_errors
    @with_retry(max_attempts=3)
    def remove_app(self, bundle_id: str) -> None:
        """Remove app by bundle ID"""
        self.driver.remove_app(bundle_id)

    @handle_appium_errors
    @with_retry(max_attempts=3)
    def query_app_state(self, bundle_id: str) -> int:
        """Query app state by bundle ID. Returns state code (4 = running)"""
        return self.driver.query_app_state(bundle_id)

    @handle_appium_errors
    @with_retry(max_attempts=3)
    def get_active_app_info(self) -> dict | None:
        """Get information about the currently active app. Returns dict with bundleId key or None on error."""
        return self.driver.execute_script("mobile: activeAppInfo")

    @handle_appium_errors
    def execute_script(self, script: str):
        """
        Execute JavaScript/script on the device.
        """
        return self.driver.execute_script(script)

    def close(self) -> None:
        """Close the Appium driver connection"""
        if self.driver and hasattr(self.driver, "quit"):
            try:
                self.driver.quit()
            finally:
                self.driver = None

    @staticmethod
    def cleanup_all_sessions() -> None:
        """Delete all active Appium sessions and kill stale WebDriverAgent processes"""
        import subprocess  # nosec B404 - needed for cleanup of stale WebDriverAgent processes

        # Kill WebDriverAgent processes occupying port 8100
        try:
            # Use full paths to system utilities for security
            result = subprocess.run(  # nosec B603 B607 - safe: hardcoded command with controlled arguments
                ["/usr/sbin/lsof", "-ti", ":8100"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    try:
                        # Check if it's WebDriverAgent (not Appium server)
                        ps_result = subprocess.run(  # nosec B603 B607 - safe: hardcoded command with validated PID
                            ["/bin/ps", "-p", pid, "-o", "comm="],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )

                        if ps_result.returncode == 0:
                            process_name = ps_result.stdout.strip()
                            # Kill only if it's WebDriverAgent, not node/Appium
                            if (
                                "WebDriverAgent" in process_name
                                or "xcodebuild" in process_name
                            ):
                                subprocess.run(  # nosec B603 B607 - safe: hardcoded command, validated PID from lsof
                                    ["/bin/kill", "-9", pid], timeout=5, check=False
                                )
                                logger.debug(
                                    "Killed WebDriverAgent process",
                                    pid=pid,
                                    process_name=process_name,
                                )
                            else:
                                logger.debug(
                                    "Skipping non-WDA process on port 8100",
                                    pid=pid,
                                    process_name=process_name,
                                )
                    except Exception as e:
                        logger.debug(
                            "Failed to check/kill process", pid=pid, error=str(e)
                        )

                # Give time for port to be released
                time.sleep(2)
        except Exception as e:
            logger.info("WebDriverAgent cleanup failed (non-critical)", error=str(e))
