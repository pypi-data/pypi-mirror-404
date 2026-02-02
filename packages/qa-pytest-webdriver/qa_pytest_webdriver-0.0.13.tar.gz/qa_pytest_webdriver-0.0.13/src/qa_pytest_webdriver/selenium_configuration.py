# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from functools import cached_property
from typing import final

from qa_pytest_commons.ui_configuration import UiConfiguration
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class SeleniumConfiguration(UiConfiguration):
    """
    SeleniumConfiguration extends BaseConfiguration to provide Selenium-specific configuration options.

    This class exposes properties for retrieving the UI URL and initializing the Selenium WebDriver Service,
    leveraging configuration values and dynamic driver management.
    """

    # FIXME Service here is imported from selenium.webdriver.chrome.service
    # which makes this method specific to ChromeDriver.
    @cached_property
    @final
    def service(self) -> Service:
        """
        Creates and returns a Selenium WebDriver Service instance using the ChromeDriverManager.

        Returns:
            Service: An instance of Selenium's Service class, initialized with the path to the ChromeDriver executable
            installed by ChromeDriverManager.

        Note:
            This method currently supports only ChromeDriver, but may be extended to support different services
            based on configuration in the future.
        """
        # NOTE may add support for providing different services per configuration
        return Service(ChromeDriverManager().install())
