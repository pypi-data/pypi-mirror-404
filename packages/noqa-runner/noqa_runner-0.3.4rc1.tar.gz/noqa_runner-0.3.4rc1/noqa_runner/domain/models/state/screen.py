from __future__ import annotations

import logging

from pydantic import BaseModel, Field
from typing_extensions import Self

logger = logging.getLogger(__name__)


class AppiumData(BaseModel):
    type: str
    value: str | None = None
    name: str | None = None
    label: str | None = None
    x: int
    y: int
    width: int
    height: int

    @classmethod
    def factory(cls, xml_element) -> Self:
        return cls(
            type=xml_element.tag,
            value=xml_element.attrib.get("value"),
            name=(
                xml_element.attrib["appium_name"]
                if "appium_name" in xml_element.attrib
                else xml_element.attrib.get("name")
            ),
            label=(
                xml_element.attrib["appium_label"]
                if "appium_label" in xml_element.attrib
                else xml_element.attrib.get("label")
            ),
            x=(
                int(xml_element.attrib["appium_x"])
                if "appium_x" in xml_element.attrib
                else int(xml_element.attrib.get("x"))
            ),
            y=(
                int(xml_element.attrib["appium_y"])
                if "appium_y" in xml_element.attrib
                else int(xml_element.attrib.get("y"))
            ),
            width=int(xml_element.attrib.get("width")),
            height=int(xml_element.attrib.get("height")),
        )


class ActiveElement(BaseModel):
    source: str
    appium_data: AppiumData | None = None

    type: str
    id: str | None = None

    x: int
    y: int
    width: int
    height: int

    scrollable: str | None = None

    @classmethod
    def factory(cls, xml_element) -> Self:
        source_data = AppiumData.factory(xml_element)

        return cls(
            source=xml_element.attrib.get("source") or "appium",
            appium_data=source_data,
            type=xml_element.attrib.get("type"),
            id=xml_element.attrib.get("id"),
            x=int(xml_element.attrib.get("x")),
            y=int(xml_element.attrib.get("y")),
            width=int(xml_element.attrib.get("width")),
            height=int(xml_element.attrib.get("height")),
            scrollable=xml_element.attrib.get("scrollable"),
        )

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2

    @property
    def value(self) -> str | None:
        return self.appium_data.value if self.appium_data else None

    @property
    def name(self) -> str | None:
        return self.appium_data.name if self.appium_data else None

    @property
    def label(self) -> str | None:
        return self.appium_data.label if self.appium_data else None

    @property
    def string_description(self) -> str:
        coordinates = f"(x:{self.center_x}, y:{self.center_y})"

        parts = []
        if self.type != "Element":
            parts.append(f"type='{self.type}'")
        if self.label:
            parts.append(f"label='{self.label}'")
        if self.id:
            parts.append(f"id='{self.id}'")
        parts.append(f"coordinates={coordinates}")
        return " ".join(parts)

    def _escape_predicate_string(self, value: str) -> str:
        """Escape string for iOS Predicate - escape backslashes and double quotes."""
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    def get_ios_locator(self, *, for_input: bool = False) -> str | None:
        """
        Generate iOS Predicate String for Appium element lookup.
        """
        if self.source != "appium" or not self.appium_data:
            return None

        # If valid id exists, use only it for locator
        if self.id:
            id_escaped = self._escape_predicate_string(self.id)
            return f"name == {id_escaped}"

        conditions: list[str] = []

        if self.appium_data.type in (
            "XCUIElementTypeTextField",
            "XCUIElementTypeSecureTextField",
        ):
            # For text fields, always include type OR condition to match both types
            conditions.append(
                '(type == "XCUIElementTypeTextField" OR type == "XCUIElementTypeSecureTextField")'
            )
        else:
            # For non-text-field elements, include type only when not for_input
            conditions.append(f'type == "{self.appium_data.type}"')

        # Add coordinates unless for_input is True
        if not for_input:
            # Add x/y coordinates for precise matching
            conditions.append(f"rect.y == {self.appium_data.y}")

        conditions.append(f"rect.x == {self.appium_data.x}")

        # Add label if present (most reliable identifier)
        if self.appium_data.label:
            label = self._escape_predicate_string(self.appium_data.label)
            conditions.append(f"label == {label}")

        # Add name if present
        if self.appium_data.name:
            name = self._escape_predicate_string(self.appium_data.name)
            conditions.append(f"name == {name}")

        # Add size coordinates (always included)
        conditions.append(f"rect.width == {self.appium_data.width}")
        conditions.append(f"rect.height == {self.appium_data.height}")

        return " AND ".join(conditions)


class Screen(BaseModel):
    elements_tree: str | None = Field(default=None)
    screenshot_url: str | None = Field(
        default=None
    )  # Public URL for screenshot retrieval
