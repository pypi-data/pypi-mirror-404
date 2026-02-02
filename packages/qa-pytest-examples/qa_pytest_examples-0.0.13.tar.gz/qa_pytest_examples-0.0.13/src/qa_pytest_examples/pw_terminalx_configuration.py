# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from qa_pytest_examples.terminalx_users_configuration import (
    TerminalXUsersConfigurationMixin,
)
from qa_pytest_playwright.playwright_configuration import (
    PlaywrightConfiguration,
)


class PwTerminalXConfiguration(
        PlaywrightConfiguration, TerminalXUsersConfigurationMixin):
    """
    Configuration for TerminalX Playwright-based tests.
    Provides access to users and random user selection.
    """

    pass
