# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import asdict
from typing import Iterator, Self

import requests
from hamcrest.core.matcher import Matcher
from qa_pytest_examples.model.swagger_petstore_pet import SwaggerPetstorePet
from qa_pytest_examples.swagger_petstore_configuration import (
    SwaggerPetstoreConfiguration,
)
from qa_pytest_rest.rest_steps import HttpMethod, RestSteps
from qa_testing_utils.logger import Context
from qa_testing_utils.matchers import adapted_object
from requests import Request


class SwaggerPetstoreSteps[TConfiguration: SwaggerPetstoreConfiguration](
        RestSteps[TConfiguration]):
    """
    BDD-style step definitions for Swagger Petstore API operations.

    Type Parameters:
        TConfiguration: The configuration type, must be a SwaggerPetstoreConfiguration.
    """

    @Context.traced
    def swagger_petstore(self, client: requests.Session):
        """
        Sets the REST session to use for subsequent steps.

        Args:
            client (requests.Session): The HTTP client session.
        Returns:
            Self: The current step instance for chaining.
        """
        self._rest_session = client
        return self

    @Context.traced
    def adding(self, pet: SwaggerPetstorePet) -> Self:
        """
        Adds a pet to the Swagger Petstore via the API.

        Args:
            pet (SwaggerPetstorePet): The pet to add.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.invoking(Request(
            method=HttpMethod.POST,
            url=self.configured.resource_uri(path="pet"),
            json=asdict(pet)
        ))

    @Context.traced
    def the_available_pets(self, by_rule: Matcher
                           [Iterator[SwaggerPetstorePet]]) -> Self:
        """
        Asserts that the available pets match the provided matcher rule.

        Args:
            by_rule (Matcher[Iterator[SwaggerPetstorePet]]): Matcher for the available pets iterator.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.the_invocation(Request(
            method=HttpMethod.GET,
            url=self.configured.resource_uri(path="pet/findByStatus"),
            params={"status": "available"}),
            adapted_object(
                lambda response: SwaggerPetstorePet.from_(response),
                by_rule))
