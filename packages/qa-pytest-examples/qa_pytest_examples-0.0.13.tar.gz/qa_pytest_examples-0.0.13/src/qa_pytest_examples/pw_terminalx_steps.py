# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from typing import Iterator, Self

from hamcrest.core.matcher import Matcher
from qa_pytest_commons.selector import By
from qa_pytest_examples.model.terminalx_credentials import TerminalXCredentials
from qa_pytest_examples.pw_terminalx_configuration import (
    PwTerminalXConfiguration,
)
from qa_pytest_playwright import PlaywrightSteps
from qa_pytest_webdriver.selenium_ui_adapter import UiContext, UiElement
from qa_testing_utils.logger import Context
from qa_testing_utils.matchers import adapted_iterator, adapted_object


class PwTerminalXSteps[TConfiguration: PwTerminalXConfiguration](
        PlaywrightSteps[TConfiguration]):
    """
    BDD-style step definitions for TerminalX UI operations using Playwright.

    Type Parameters:
        TConfiguration: The configuration type, must be a PwTerminalXConfiguration.
    """
    @Context.traced
    def terminalx(self, page: UiContext[UiElement]) -> Self:
        """
        Sets the Playwright Page and navigates to the landing page.

        Args:
            page (UiContext[UiElement]): The Playwright Page instance.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.ui_context(page).at(self.configured.entry_point)

    def clicking_login(self) -> Self:
        """
        Clicks the login button on the TerminalX landing page.

        Returns:
            Self: The current step instance for chaining.
        """
        return self.clicking(By.xpath("//div[contains(text(), 'התחברות')]"))

    @Context.traced
    def clicking_search(self) -> Self:
        """
        Clicks the search button in the TerminalX header.

        Returns:
            Self: The current step instance for chaining.
        """
        return self.clicking(
            By.xpath("//button[@data-test-id='qa-header-search-button']"))

    def submitting_login(self) -> Self:
        """
        Clicks the submit button on the login form.

        Returns:
            Self: The current step instance for chaining.
        """
        return self.clicking(By.xpath("//button[contains(text(), 'התחברות')]"))

    @Context.traced
    def logging_in_with(self, credentials: TerminalXCredentials) -> Self:
        """
        Logs in using the provided credentials.

        Args:
            credentials (TerminalXCredentials): The credentials to use for login.
        Returns:
            Self: The current step instance for chaining.
        """
        return (self.clicking_login()
                .and_.typing(
                    By.id("qa-login-email-input"), credentials.username)
                .and_.typing(
                    By.id("qa-login-password-input"), credentials.password)
                .and_.submitting_login())

    @Context.traced
    def the_user_logged_in(self, by_rule: Matcher[str]) -> Self:
        """
        Asserts that the user is logged in by checking the profile button text.

        Args:
            by_rule (Matcher[str]): Matcher for the user name text.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.the_element(
            By.xpath(
                "//button[@data-test-id='qa-header-profile-button']/span[2]"),
            adapted_object(lambda element: element.text, by_rule))

    @Context.traced
    def searching_for(self, text: str) -> Self:
        """
        Types the given text into the search box.

        Args:
            text (str): The text to search for.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.typing(
            By.xpath("//input[@data-test-id='qa-search-box-input']"),
            text)

    @Context.traced
    def the_search_hints(self, by_rule: Matcher[Iterator[str]]) -> Self:
        """
        Asserts that the search hints match the provided matcher rule.

        Args:
            by_rule (Matcher[Iterator[str]]): Matcher for the search hints iterator.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.the_elements(
            By.xpath("(//ul[@class='list_3tWy'])[2]/li/div/div/a"),
            adapted_iterator(lambda element: element.text, by_rule))
