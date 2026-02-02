# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    """
    Represents user credentials with username and password.
    """

    username: str
    password: str

    @classmethod
    def from_(cls, colon_separated: str):
        """
        Creates a Credentials instance from a colon-separated string.

        Args:
            colon_separated (str): String in the format 'username:password'.

        Returns:
            Credentials: The created credentials instance.
        """
        return cls(*colon_separated.split(":"))
