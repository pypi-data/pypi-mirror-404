
# SPDX-FileCopyrightText: 2026 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Iterator, Optional

from playwright.sync_api import Locator as PlaywrightLocator
from playwright.sync_api import Page
from qa_pytest_commons.selector import Selector
from qa_pytest_commons.ui_protocols import UiContext, UiElement

"""
Playwright adapter for backend-agnostic UiElement and UiContext protocols.
"""


class PlaywrightUiElement(UiElement):
    """
    Playwright adapter for UiElement protocol.
    Wraps a Playwright Locator and implements the backend-agnostic UiElement interface.
    """

    _locator: PlaywrightLocator

    def __init__(self, locator: PlaywrightLocator) -> None:
        object.__setattr__(self, '_locator', locator)

    def click(self) -> None:
        self._locator.click()

    def type(self, text: str) -> None:
        self._locator.clear()
        self._locator.fill(text)

    def clear(self) -> None:
        self._locator.clear()

    def send_keys(self, *value: str) -> None:
        self._locator.fill(''.join(value))

    def execute_script(self, script: str, *args: object) -> object:
        """Execute script on this element using the page's evaluate method."""
        return self._locator.evaluate(script, *args)

    @property
    def text(self) -> str:
        """Get element text content, returning empty string if None."""
        return self._locator.text_content() or ""

    def scroll_into_view_if_needed(self) -> None:
        """Playwright-specific method for scrolling."""
        self._locator.scroll_into_view_if_needed()

    def __getattr__(self, name: str) -> Any:
        """Delegate all other attribute access to the wrapped Playwright Locator."""
        return getattr(self._locator, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Delegate attribute setting to the wrapped Playwright Locator."""
        if name == '_locator':
            object.__setattr__(self, name, value)
        else:
            setattr(self._locator, name, value)

    def __repr__(self) -> str:
        return repr(self._locator)

    def __str__(self) -> str:
        return str(self._locator)


# Alias for backward compatibility
LocatorWrapper = PlaywrightUiElement


class PlaywrightUiContext(UiContext[PlaywrightUiElement]):
    _page: Page

    def __init__(self, page: Page) -> None:
        self._page = page

    def find_element(
            self, by: str, value: Optional[str]) -> PlaywrightUiElement:
        selector_str = self._build_playwright_selector(
            Selector(by, value or ""))
        return PlaywrightUiElement(self._page.locator(selector_str).first)

    def find_elements(
            self, by: str, value: Optional[str]) -> Iterator[PlaywrightUiElement]:
        selector_str = self._build_playwright_selector(
            Selector(by, value or ""))
        return (PlaywrightUiElement(e) for e in self._page.locator(selector_str).all())

    def get(self, url: str) -> None:
        self._page.goto(url)

    def execute_script(self, script: str, *args: object) -> Any:
        return self._page.evaluate(script, *args)

    @staticmethod
    def _build_playwright_selector(selector: Selector) -> str:
        """
        Converts a Selector object to a Playwright selector string.
        """
        if selector.by == "id":
            return f"#{selector.value}"
        elif selector.by == "xpath":
            return selector.value
        elif selector.by == "css selector":
            return selector.value
        elif selector.by == "link text":
            return f"text={selector.value}"
        elif selector.by == "partial link text":
            return f"text={selector.value}"
        elif selector.by == "name":
            return f"[name='{selector.value}']"
        elif selector.by == "tag name":
            return selector.value
        elif selector.by == "class name":
            return f".{selector.value}"
        else:
            return selector.value
