# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from qa_pytest_examples.terminalx_users_configuration import (
    TerminalXUsersConfigurationMixin,
)
from qa_pytest_webdriver.selenium_configuration import SeleniumConfiguration


class TerminalXConfiguration(SeleniumConfiguration,
                             TerminalXUsersConfigurationMixin):
    """
    Configuration for TerminalX Selenium-based tests.
    Provides access to users and random user selection.
    """
    pass
