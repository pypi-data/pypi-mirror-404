# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from typing import Iterator, Optional, Self, final, overload

from hamcrest.core.matcher import Matcher
from qa_pytest_commons.generic_steps import GenericSteps
from qa_pytest_commons.selector import Selector
from qa_pytest_commons.ui_protocols import (
    ElementSupplier,
    SelectorOrSupplier,
    UiContext,
    UiElement,
)
from qa_pytest_playwright.playwright_configuration import (
    PlaywrightConfiguration,
)
from qa_testing_utils.logger import Context


class PlaywrightSteps[TConfiguration: PlaywrightConfiguration](
    GenericSteps[TConfiguration]
):
    """
    BDD-style step definitions for Playwright-based UI operations.

    Type Parameters:
        TConfiguration: The configuration type, must be a PlaywrightConfiguration.

    Attributes:
        _ui_context (UiContext[UiElement]): The Playwright UI context used for browser automation.
    """

    _ui_context: UiContext[UiElement]

    @final
    @Context.traced
    def ui_context(self, ui_context: UiContext[UiElement]) -> Self:
        """
        Sets the Playwright Page instance.

        Args:
            ui_context (UiContext[UiElement]): The Playwright Page instance.
        Returns:
            Self: The current step instance for chaining.
        """
        self._ui_context = ui_context
        return self

    @final
    @Context.traced
    def at(self, url: str) -> Self:
        """
        Navigates to the specified URL with retry logic.

        Args:
            url (str): The URL to navigate to.
        Returns:
            Self: The current step instance for chaining.
        """
        def _navigate() -> Self:
            self._ui_context.get(url)
            return self

        return self.retrying(_navigate)

    @final
    @Context.traced
    def clicking_once(self, element_supplier: ElementSupplier) -> Self:
        """
        Clicks the element supplied by the given callable.

        Args:
            element_supplier (ElementSupplier): Callable returning a Playwright Locator.
        Returns:
            Self: The current step instance for chaining.
        """
        element_supplier().click()
        return self

    @overload
    def clicking(
        self, element: Selector) -> Self: ...

    @overload
    def clicking(
        self, element: ElementSupplier) -> Self: ...

    @final
    def clicking(self, element: SelectorOrSupplier) -> Self:
        """
        Clicks the element specified by a selector or supplier, with retry logic.

        Args:
            element (SelectorOrSupplier): Selector or callable returning a Playwright Locator.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.retrying(lambda: self.clicking_once(self._resolve(element)))

    @final
    @Context.traced
    def typing_once(self, element_supplier: ElementSupplier, text: str) -> Self:
        """
        Types the given text into the element supplied by the callable.

        Args:
            element_supplier (ElementSupplier): Callable returning a Playwright Locator.
            text (str): The text to type.
        Returns:
            Self: The current step instance for chaining.
        """
        element = element_supplier()
        element.clear()
        element.type(text)
        return self

    @overload
    def typing(self, element: Selector,
               text: str) -> Self: ...

    @overload
    def typing(self, element: ElementSupplier,
               text: str) -> Self: ...

    @final
    def typing(self, element: SelectorOrSupplier, text: str) -> Self:
        """
        Types the given text into the element specified by a selector or supplier, with retry logic.

        Args:
            element (SelectorOrSupplier): Selector or callable returning a Playwright Locator.
            text (str): The text to type.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.retrying(lambda: self.typing_once(
            self._resolve(element),
            text))

    @final
    def the_element(
            self, selector: Selector, by_rule: Matcher[UiElement],
            context: Optional[UiContext[UiElement]] = None) -> Self:
        """
        Asserts that the element found by the selector matches the given matcher.

        Args:
            selector (Selector): The selector to find the element.
            by_rule (Matcher[UiElement]): Matcher for the element.
            context (Optional[UiContext[UiElement]]): Optional page context (defaults to _page).
        Returns:
            Self: The current step instance for chaining.
        """
        return self.eventually_assert_that(
            lambda: self._element(selector, context),
            by_rule)

    @final
    def the_elements(
            self, selector: Selector, by_rule:
            Matcher[Iterator[UiElement]],
            context: Optional[UiContext[UiElement]] = None) -> Self:
        """
        Asserts that the elements found by the selector match the given matcher.

        Args:
            selector (Selector): The selector to find the elements.
            by_rule (Matcher[Iterator[LocatorWrapper]]): Matcher for the elements iterator.
            context (Optional[Page]): Optional page context (defaults to _page).
        Returns:
            Self: The current step instance for chaining.
        """
        return self.eventually_assert_that(
            lambda: self._elements(selector, context),
            by_rule)

    @final
    @Context.traced
    def _elements(
        self, selector: Selector, context: Optional[UiContext[UiElement]] = None
    ) -> Iterator[UiElement]:
        search_ctx = context or self._ui_context
        return search_ctx.find_elements(*selector.as_tuple())

    @final
    @Context.traced
    def _element(
        self, selector: Selector, context: Optional[UiContext[UiElement]] = None
    ) -> UiElement:
        element = (
            context or self._ui_context).find_element(
            *selector.as_tuple())
        return self._scroll_into_view(element)

    def _scroll_into_view(self, element: UiElement) -> UiElement:
        # Use hasattr to check for Playwright-specific method
        if hasattr(element, 'scroll_into_view_if_needed'):
            element.scroll_into_view_if_needed()  # type: ignore[attr-defined]
        return element

    @final
    def _resolve(self, element: SelectorOrSupplier) -> ElementSupplier:
        if isinstance(element, Selector):
            return lambda: self._element(element)
        return element
