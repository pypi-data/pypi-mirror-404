# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from functools import cached_property
from typing import Callable, final

from playwright.sync_api import Browser, Playwright
from qa_pytest_commons.ui_configuration import UiConfiguration


class PlaywrightConfiguration(UiConfiguration):

    @cached_property
    @final
    def service(self) -> Callable[[Playwright], Browser]:
        """
        Creates and returns a browser launcher function.

        Returns:
            Callable[[Playwright], Browser]: A function that takes a Playwright instance and returns a Browser.
                Currently launches Chromium with headless=False and GPU disabled.

        Note:
            This method currently supports only Chromium, but may be extended to support different browsers
            (Firefox, WebKit) based on configuration in the future.
        """
        # NOTE may add support for providing different browser launchers per configuration
        def launch_browser(playwright: Playwright) -> Browser:
            return playwright.chromium.launch(
                headless=False, args=["--disable-gpu"]
            )
        return launch_browser
