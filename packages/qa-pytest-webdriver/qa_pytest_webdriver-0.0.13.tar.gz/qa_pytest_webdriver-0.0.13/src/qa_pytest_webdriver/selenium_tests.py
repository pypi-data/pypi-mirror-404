# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any, override

from qa_pytest_commons.abstract_tests_base import AbstractTestsBase
from qa_pytest_webdriver.selenium_configuration import SeleniumConfiguration
from qa_pytest_webdriver.selenium_steps import (
    SeleniumSteps,
    UiContext,
    UiElement,
)
from qa_pytest_webdriver.selenium_ui_adapter import SeleniumUiContext
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver


class SeleniumTests[
    TSteps: SeleniumSteps[Any],
    TConfiguration: SeleniumConfiguration
](AbstractTestsBase[TSteps, TConfiguration]):
    """
    Base class for Selenium-based UI test cases.

    This class manages the lifecycle of a Selenium WebDriver for each test method.
    It is generic over the types of steps and configuration used.

    Attributes:
        _web_driver (WebDriver): The Selenium WebDriver instance (not thread safe).

    Type Parameters:
        TSteps: The type of the steps class, typically derived from SeleniumSteps.
        TConfiguration: The type of the configuration class, typically derived from SeleniumConfiguration.
    """
    _web_driver: WebDriver  # not thread safe

    @property
    def ui_context(self) -> UiContext[UiElement]:
        '''
        Returns the web driver instance.

        Returns:
            UiContext[UiElement]: The web driver instance.
        '''
        return SeleniumUiContext(self._web_driver)

    @override
    def setup_method(self):
        '''
        Initializes a local Chrome WebDriver before each test method.

        If you need to customize or use other driver, override this method in your test class.
        '''
        super().setup_method()

        options = Options()
        options.add_argument("--start-maximized")  # type: ignore
        options.add_argument("--disable-gpu")
        self._web_driver = Chrome(
            options,
            self._configuration.service)

    @override
    def teardown_method(self):
        '''
        Quits the Selenium WebDriver after each test method.
        '''
        try:
            self._web_driver.quit()
        finally:
            super().teardown_method()
