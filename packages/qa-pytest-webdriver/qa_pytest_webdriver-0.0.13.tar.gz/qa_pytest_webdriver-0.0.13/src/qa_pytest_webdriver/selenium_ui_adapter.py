
# SPDX-FileCopyrightText: 2026 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0
from typing import Any, Iterator, Optional

from qa_pytest_commons.ui_protocols import UiContext, UiElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

"""
Selenium adapter for backend-agnostic UiElement and UiContext protocols.
"""


class SeleniumUiElement(WebElement, UiElement):
    def __init__(self, element: WebElement) -> None:
        # Copy all attributes from the original WebElement
        self.__dict__ = element.__dict__

    def click(self) -> None:
        super().click()

    def type(self, text: str) -> None:
        self.clear()
        self.send_keys(text)

    def clear(self) -> None:
        super().clear()

    def send_keys(self, *value: str) -> None:
        super().send_keys(*value)

    @property
    def text(self) -> str:
        return super().text


class SeleniumUiContext(UiContext[SeleniumUiElement]):
    _driver: WebDriver

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver

    def find_element(self, by: str, value: Optional[str]) -> SeleniumUiElement:
        return SeleniumUiElement(self._driver.find_element(by, value))

    def find_elements(
            self, by: str, value: Optional[str]) -> Iterator[SeleniumUiElement]:
        return (SeleniumUiElement(e) for e in self._driver.find_elements(by, value))

    def get(self, url: str) -> None:
        self._driver.get(url)

    def execute_script(self, script: str, *args: UiElement) -> Any:
        return self._driver.execute_script(script, *args)  # type: ignore
