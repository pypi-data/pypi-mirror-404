# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

from qa_pytest_examples.model.terminalx_credentials import TerminalXCredentials


@dataclass(frozen=True)
class TerminalXUser:
    """
    Represents a TerminalX user with credentials and a display name.
    """

    credentials: TerminalXCredentials
    name: str
