"""Base mobile service with platform-agnostic logic"""

from __future__ import annotations

import asyncio
import base64
import time
from abc import ABC, abstractmethod
from functools import cached_property
from io import BytesIO

import numpy as np
from defusedxml import ElementTree as ET
from PIL import Image

from noqa_runner.domain.models.actions.activate_app import ActivateApp
from noqa_runner.domain.models.actions.background_app import BackgroundApp
from noqa_runner.domain.models.actions.base import BaseAction
from noqa_runner.domain.models.actions.input_text import InputText
from noqa_runner.domain.models.actions.long_tap import LongTap
from noqa_runner.domain.models.actions.open_url import OpenUrl
from noqa_runner.domain.models.actions.restart_app import RestartApp
from noqa_runner.domain.models.actions.scroll import Scroll
from noqa_runner.domain.models.actions.stop import Stop
from noqa_runner.domain.models.actions.swipe import Swipe
from noqa_runner.domain.models.actions.tap import Tap
from noqa_runner.domain.models.actions.terminate_app import TerminateApp
from noqa_runner.domain.models.actions.wait import Wait
from noqa_runner.domain.models.state.screen import ActiveElement, Screen
from noqa_runner.infrastructure.adapters.mobile.appium_adapter import AppiumClient
from noqa_runner.utils.retry_decorator import with_retry


class BaseMobileService(ABC):
    """Base service for mobile device interactions (platform-agnostic)"""

    # Screen data stability timeouts
    SCREENSHOT_STABILITY_TIMEOUT = 4.0
    ELEMENTS_STABILITY_TIMEOUT = 4.0
    NOTIFICATION_WAIT_TIMEOUT = 10.0
    SCREENSHOT_DIFF_THRESHOLD = 0.5

    def __init__(self, appium_client: AppiumClient, bundle_id: str):
        self.client = appium_client
        self.bundle_id = bundle_id

    async def get_app_state(self, bundle_id: str) -> int:
        """Get current app state"""
        return self.client.query_app_state(bundle_id)

    async def execute_action(self, action: BaseAction, screen: Screen | None = None):
        """Execute action based on its type using pattern matching"""
        match action:
            case Tap():
                await self.tap_element(action.element)

            case LongTap():
                await self.long_tap_element(action.element, action.duration)

            case Swipe():
                await self.swipe_element(action.element, action.direction)

            case InputText():
                await self.input_text_in_element(
                    action.element,
                    action.text,
                    screen.elements_tree if screen else None,
                )

            case Scroll():
                await self.scroll_element(action.element, action.direction)

            case ActivateApp():
                self.client.activate_app(self.bundle_id)

            case BackgroundApp():
                self.client.background_app()

            case TerminateApp():
                self.client.terminate_app(self.bundle_id)

            case RestartApp():
                self.client.terminate_app(self.bundle_id)
                self.client.activate_app(self.bundle_id)

            case OpenUrl():
                self.client.open_url(str(action.url))

            case Wait():
                await asyncio.sleep(3)

            case Stop():
                pass

            case _:
                raise ValueError(f"Unknown action type: {type(action).__name__}")

    # Abstract methods - must be implemented by platform-specific services
    @abstractmethod
    def get_locator(
        self, element: ActiveElement, *, for_input: bool = False
    ) -> str | None:
        """
        Generate platform-specific locator for Appium element lookup.

        Args:
            element: ActiveElement to generate locator for
            for_input: If True, generate locator optimized for text input

        Returns:
            Platform-specific locator string or None if element is not from Appium
        """
        pass

    @abstractmethod
    def get_locator_strategy(self) -> str:
        """
        Get platform-specific locator strategy (AppiumBy constant).

        Returns:
            AppiumBy constant (e.g., AppiumBy.IOS_PREDICATE or AppiumBy.ANDROID_UIAUTOMATOR)
        """
        pass

    @abstractmethod
    def _has_overlay_ui(self, xml_source: str) -> bool:
        """Platform-specific overlay detection"""
        pass

    async def tap_element(self, element: ActiveElement) -> None:
        """
        Smart tap - automatically chooses best tap method

        Strategy:
        1. OCR elements → use coordinates
        2. Element has locator → try locator, fallback to coordinates
        3. Otherwise → use coordinates
        """
        # For OCR elements, always use coordinates
        if element.source == "ocr":
            self.client.tap_by_coords(element.center_x, element.center_y)
            return

        # Try platform-specific locator first, fallback to coordinates
        element_locator = self.get_locator(element)
        if element_locator:
            tap_success = self.client.tap_element(
                by=self.get_locator_strategy(), locator=element_locator
            )
            if tap_success:
                return

        if element.center_x is not None and element.center_y is not None:
            self.client.tap_by_coords(element.center_x, element.center_y)
            return

        raise ValueError(f"Failed to tap element: invalid element data: {element}")

    async def input_text_in_element(
        self, element: ActiveElement, text: str, elements_tree: str | None = None
    ) -> None:
        """
        Smart text input with automatic keyboard handling

        Args:
            element: Target element for text input
            text: Text to input
            elements_tree: XML tree to check for keyboard presence
        """
        element_locator = self.get_locator(element, for_input=True)
        if element_locator:
            self.client.send_keys(
                by=self.get_locator_strategy(), locator=element_locator, text=text
            )

    @cached_property
    def resolution(self) -> dict[str, int]:
        """Get device resolution (cached)"""
        return self.client.resolution

    async def long_tap_element(self, element: ActiveElement, duration: int) -> None:
        """
        Smart long tap (press and hold) - uses coordinates for reliable long press

        Args:
            element: Element to long tap
            duration: Duration in seconds (3-10 seconds)
        """
        if element.center_x is None or element.center_y is None:
            raise ValueError(
                f"Failed to long tap element: invalid element data: {element}"
            )

        self.client.swipe(
            start_x=element.center_x,
            start_y=element.center_y,
            end_x=element.center_x,
            end_y=element.center_y,
            duration_ms=duration * 1000,
        )

    async def swipe_element(
        self, element: ActiveElement, direction: str, use_element_bounds: bool = False
    ) -> None:
        """
        Smart swipe from element with automatic start/end position calculation

        Start position is adjusted so finger movement feels natural:
        - up: start from bottom (3/4 height) → swipe upward
        - down: start from top (1/4 height) → swipe downward
        - left: start from right (3/4 width) → swipe leftward
        - right: start from left (1/4 width) → swipe rightward

        Distance calculation:
        - If use_element_bounds=True: use 80% of element size
        - Otherwise: use half of screen size

        Args:
            element: Element to swipe from
            direction: Swipe direction (up, down, left, right)
            use_element_bounds: If True, limit swipe distance to 80% of element size
        """
        start_x = element.center_x
        start_y = element.center_y

        # Get screen dimensions for boundary clamping
        screen_width = self.resolution["width"]
        screen_height = self.resolution["height"]

        # Calculate swipe distance based on element bounds or screen size
        if use_element_bounds:
            swipe_distance_vertical = int(element.height * 0.8)
            swipe_distance_horizontal = int(element.width * 0.8)
            # Ensure minimum scroll distance is 1/6 of screen size
            min_vertical_distance = screen_height // 6
            min_horizontal_distance = screen_width // 6
            swipe_distance_vertical = max(
                swipe_distance_vertical, min_vertical_distance
            )
            swipe_distance_horizontal = max(
                swipe_distance_horizontal, min_horizontal_distance
            )
        else:
            swipe_distance_vertical = screen_height // 2
            swipe_distance_horizontal = screen_width // 2

        # Adjust start position and calculate end position based on direction
        if direction == "up":
            # Start from bottom of element to swipe UP
            start_y = element.y + element.height * 3 // 4
            end_x = start_x
            end_y = max(0, start_y - swipe_distance_vertical)
        elif direction == "down":
            # Start from top of element to swipe DOWN
            start_y = element.y + element.height // 4
            end_x = start_x
            end_y = min(screen_height, start_y + swipe_distance_vertical)
        elif direction == "left":
            # Start from right of element to swipe LEFT
            start_x = element.x + element.width * 3 // 4
            end_x = max(0, start_x - swipe_distance_horizontal)
            end_y = start_y
        elif direction == "right":
            # Start from left of element to swipe RIGHT
            start_x = element.x + element.width // 4
            end_x = min(screen_width, start_x + swipe_distance_horizontal)
            end_y = start_y
        else:
            raise ValueError(f"Invalid swipe direction: {direction}")

        self.client.swipe(start_x=start_x, start_y=start_y, end_x=end_x, end_y=end_y)

    async def scroll_element(self, element: ActiveElement, direction: str) -> None:
        """
        Smart scroll on element by delegating to swipe_element with inverted direction

        SCROLL semantics: direction = where content moves (what you want to see)
        - scroll down = see content below = finger swipes UP
        - scroll up = see content above = finger swipes DOWN
        - scroll left = see content on left = finger swipes RIGHT
        - scroll right = see content on right = finger swipes LEFT

        Scroll distance is limited to element bounds (80% of element size)
        to prevent scrolling beyond the element boundaries.

        Args:
            element: Element to scroll
            direction: Scroll direction (up, down, left, right) - content movement
        """
        # Invert direction: scroll down = swipe up, scroll up = swipe down
        direction_mapping = {
            "up": "down",  # scroll up (see above) = swipe finger down
            "down": "up",  # scroll down (see below) = swipe finger up
            "left": "right",  # scroll left (see left) = swipe finger right
            "right": "left",  # scroll right (see right) = swipe finger left
        }
        swipe_direction = direction_mapping.get(direction, direction)
        # Use element bounds to limit scroll distance
        await self.swipe_element(
            element=element, direction=swipe_direction, use_element_bounds=True
        )

    def _resize_image(self, image: Image.Image, max_size: int) -> Image.Image:
        """Resize image so that minimum side is max_size"""
        width, height = image.size
        min_side = min(width, height)

        if min_side <= max_size:
            return image

        scale_factor = max_size / min_side
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _resize_screenshot(self, screenshot_base64: str, max_size: int = 500) -> str:
        """Resize screenshot to max_size on minimum side, return base64"""
        image_data = base64.b64decode(screenshot_base64)
        with Image.open(BytesIO(image_data)) as img:
            resized = self._resize_image(image=img, max_size=max_size)
            buffer = BytesIO()
            resized.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _get_screenshot_thumbnail(self, screenshot_base64: str) -> np.ndarray:
        """Get screenshot thumbnail as numpy array for comparison"""
        image_data = base64.b64decode(screenshot_base64)
        with Image.open(BytesIO(image_data)) as img:
            # Reuse _resize_image for consistency (50px for fast comparison)
            resized = self._resize_image(image=img.convert("RGB"), max_size=50)
        return np.asarray(resized)

    def _calculate_image_difference(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Calculate percentage difference between two images
        Returns percentage of different pixels (0.0 to 100.0)
        """
        if img1.shape != img2.shape:
            return 100.0

        # Calculate absolute difference
        diff = np.abs(img1.astype(float) - img2.astype(float))

        # Use L2 norm (Euclidean distance) per pixel for more robust comparison
        # This considers the magnitude of differences across all channels
        pixel_diff_magnitude = np.sqrt(np.sum(diff**2, axis=-1))

        # Define threshold for considering pixels as different (default: 5.0)
        # This helps ignore minor rendering artifacts and anti-aliasing differences
        threshold = 5.0

        # Count pixels that exceed threshold
        different_pixels = (pixel_diff_magnitude > threshold).sum()
        total_pixels = img1.shape[0] * img1.shape[1]

        # Return percentage
        return (different_pixels / total_pixels) * 100.0

    def _has_non_fullscreen_elements(self, xml_source: str) -> bool:
        """Check if XML has elements smaller than screen resolution"""
        root = ET.fromstring(xml_source)
        for elem in root.iter():
            width = elem.get("width")
            height = elem.get("height")
            if width and height:
                if (
                    int(width) < self.resolution["width"]
                    or int(height) < self.resolution["height"]
                ):
                    return True
        return False

    @with_retry(max_attempts=3)
    async def get_appium_screen_data(self) -> tuple[str, str]:
        """
        Get synchronized XML and screenshot from Appium with three-phase stability check

        Phase 1: Wait for screenshot stability
        Phase 2: Wait for element tree to have content
        Phase 3: Wait for notifications to disappear
        """
        start_time = time.time()

        # Phase 1: Wait for screenshot stability
        while time.time() - start_time < self.SCREENSHOT_STABILITY_TIMEOUT:
            screenshot_before = self.client.get_screenshot()
            thumbnail_before = self._get_screenshot_thumbnail(
                screenshot_base64=screenshot_before
            )

            screenshot_after = self.client.get_screenshot()
            thumbnail_after = self._get_screenshot_thumbnail(
                screenshot_base64=screenshot_after
            )

            diff_percent = self._calculate_image_difference(
                img1=thumbnail_before, img2=thumbnail_after
            )

            if diff_percent <= self.SCREENSHOT_DIFF_THRESHOLD:
                # Screenshot is stable, move to Phase 2
                break

            await asyncio.sleep(0.05)

        # Phase 2: Wait for element tree to have active elements
        elements_start_time = time.time()
        xml_source = None

        while time.time() - elements_start_time < self.ELEMENTS_STABILITY_TIMEOUT:
            xml_source = self.client.get_page_source()

            # Check if there are non-fullscreen elements (real UI content)
            if self._has_non_fullscreen_elements(xml_source):
                # Move to Phase 3
                break

            await asyncio.sleep(0.05)

        # Phase 3: Wait for notifications to disappear
        notification_start_time = time.time()

        while time.time() - notification_start_time < self.NOTIFICATION_WAIT_TIMEOUT:
            # Check if overlay UI is gone (use xml_source from Phase 2 on first iteration)
            if not self._has_overlay_ui(xml_source):
                # Take fresh screenshot when UI is clean
                fresh_screenshot = self.client.get_screenshot()
                screenshot_resized = self._resize_screenshot(
                    screenshot_base64=fresh_screenshot, max_size=500
                )
                return xml_source, screenshot_resized

            # Get fresh XML for next iteration
            await asyncio.sleep(0.2)
            xml_source = self.client.get_page_source()

        # Timeout: take fresh screenshot and return what we have (even with overlay)
        fresh_screenshot = self.client.get_screenshot()
        screenshot_resized = self._resize_screenshot(
            screenshot_base64=fresh_screenshot, max_size=500
        )
        return xml_source, screenshot_resized
