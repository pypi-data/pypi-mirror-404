# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator
from uuid import uuid4

from qa_testing_utils.string_utils import to_string
from requests import Response


@dataclass(eq=True, frozen=True)
@to_string()
class SwaggerPetstorePet:
    """
    Represents a pet in the Swagger Petstore API.
    """
    name: str
    status: str

    @staticmethod
    def random(range: range = range(1)) -> Iterator['SwaggerPetstorePet']:
        """
        Generates a random SwaggerPetstorePet with a unique name and 'available' status.

        Returns:
            SwaggerPetstorePet: The generated pet.
        """
        for _ in range:
            yield SwaggerPetstorePet(name=str(uuid4()), status="available")

    @staticmethod
    def from_(response: Response) -> Iterator['SwaggerPetstorePet']:
        """
        Parses a response and yields SwaggerPetstorePet objects for each valid pet entry.

        Args:
            response (Response): The HTTP response containing pet data.
        Returns:
            Iterator[SwaggerPetstorePet]: Iterator over parsed pets.
        """
        return (
            SwaggerPetstorePet(name=pet["name"], status=pet["status"])
            for pet in response.json()
            if "name" in pet and "status" in pet
        )
