# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any, override

from playwright.sync_api import Browser, Page, Playwright
from qa_pytest_commons.abstract_tests_base import AbstractTestsBase
from qa_pytest_commons.ui_protocols import UiContext, UiElement
from qa_pytest_playwright.playwright_configuration import (
    PlaywrightConfiguration,
)
from qa_pytest_playwright.playwright_steps import PlaywrightSteps
from qa_pytest_playwright.playwright_ui_adapter import PlaywrightUiContext


class PlaywrightTests[
    TSteps: PlaywrightSteps[Any],
    TConfiguration: PlaywrightConfiguration
](AbstractTestsBase[TSteps, TConfiguration]):
    """
    Base class for Playwright-based UI test cases.

    This class manages the lifecycle of a Playwright browser and page for each test method.
    It is generic over the types of steps and configuration used.

    Attributes:
        _playwright (Playwright): The Playwright instance.
        _browser (Browser): The Playwright browser instance (not thread safe).
        _page (Page): The Playwright page instance (not thread safe).
    Type Parameters:
        TSteps: The type of the steps class, typically derived from PlaywrightSteps.
        TConfiguration: The type of the configuration class, typically derived from PlaywrightConfiguration.
    """
    _playwright: Playwright  # not thread safe
    _browser: Browser  # not thread safe
    _page: Page  # not thread safe

    @property
    def browser(self) -> Browser:
        """
        Returns the Playwright browser instance.

        Returns:
            Browser: The Playwright browser instance.
        """
        return self._browser

    @property
    def page(self) -> Page:
        """
        Returns the Playwright page instance.

        Returns:
            Page: The Playwright page instance.
        """
        return self._page

    @property
    def ui_context(self) -> UiContext[UiElement]:
        return PlaywrightUiContext(self._page)

    @override
    def setup_method(self):
        """
        Initializes Playwright browser and page before each test method.

        If you need to customize browser options or use a different browser,
        override this method in your test class.
        """
        super().setup_method()

        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()
        self._browser = self._configuration.service(self._playwright)
        self._page = self._browser.new_page()

    @override
    def teardown_method(self):
        """
        Closes the Playwright page, browser, and context after each test method.
        """
        try:
            try:
                self._page.close()
            finally:
                try:
                    self._browser.close()
                finally:
                    self._playwright.stop()
        finally:
            super().teardown_method()
