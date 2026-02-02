# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

from qa_pytest_examples.model.credentials import Credentials


@dataclass(frozen=True)
class SwaggerPetstoreCredentials(Credentials):
    """
    Credentials for Swagger Petstore users.
    Inherits from Credentials.
    """
    pass
