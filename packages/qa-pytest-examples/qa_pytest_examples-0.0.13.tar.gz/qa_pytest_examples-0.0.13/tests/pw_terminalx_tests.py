# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from typing import override

import pytest
from hamcrest import is_  # type: ignore
from qa_pytest_examples import PwTerminalXSteps
from qa_pytest_examples.model.terminalx_user import TerminalXUser
from qa_pytest_examples.pw_terminalx_configuration import (
    PwTerminalXConfiguration,
)
from qa_pytest_playwright import PlaywrightTests
from qa_testing_utils.matchers import (
    contains_string_ignoring_case,
    tracing,
    yields_item,
)


# --8<-- [start:class]
@pytest.mark.external
@pytest.mark.ui
class PwTerminalXTests(
    PlaywrightTests[PwTerminalXSteps[PwTerminalXConfiguration],
                    PwTerminalXConfiguration]):
    _steps_type = PwTerminalXSteps
    _configuration = PwTerminalXConfiguration()

    # --8<-- [start:func]
    # NOTE sections may be further collected in superclasses and reused across tests
    def login_section(
            self, user: TerminalXUser) -> PwTerminalXSteps[PwTerminalXConfiguration]:
        return (self.steps
                .given.terminalx(self.ui_context)
                .when.logging_in_with(user.credentials)
                .then.the_user_logged_in(is_(user.name)))

    def should_login(self):
        self.login_section(self.configuration.random_user)

    def should_find(self):
        (self.login_section(self.configuration.random_user)
            .when.clicking_search())

        for word in ["hello", "kitty"]:
            (self.steps
             .when.searching_for(word)
             .then.the_search_hints(yields_item(tracing(
                 contains_string_ignoring_case(word)))))
    # --8<-- [end:func]

    # --8<-- [start:setup_method]
    @override
    def setup_method(self) -> None:
        from playwright.sync_api import sync_playwright
        if self._configuration.parser.has_option("playwright", "browser_type") \
                and self._configuration.parser["playwright"]["browser_type"] == "firefox":
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.firefox.launch()
            self._page = self._browser.new_page(
                viewport={"width": 1920, "height": 1080})
        else:
            super().setup_method()
    # --8<-- [end:setup_method]

# --8<-- [end:class]
