# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import configparser
import random
from functools import cached_property
from typing import Protocol, final

from qa_pytest_examples.model.terminalx_credentials import TerminalXCredentials
from qa_pytest_examples.model.terminalx_user import TerminalXUser


class _HasParser(Protocol):
    @property
    def parser(self) -> configparser.ConfigParser: ...


class TerminalXUsersConfigurationMixin:
    """
    Shared TerminalX user configuration helpers.
    """

    @cached_property
    @final
    def users(self: _HasParser) -> tuple[TerminalXUser, ...]:
        """
        Returns the list of TerminalX users from the configuration parser.

        Returns:
            Iterable[TerminalXUser]: The list of users.
        """
        users_section = self.parser["users"]
        return tuple(
            TerminalXUser(TerminalXCredentials.from_(
                username_password), name=key)
            for key, username_password in users_section.items()
        )

    @final
    @property
    def random_user(self: "TerminalXUsersConfigurationMixin") -> TerminalXUser:
        """
        Returns a random user from the list of users.

        Returns:
            TerminalXUser: A randomly selected user.
        """
        return random.choice(self.users)
