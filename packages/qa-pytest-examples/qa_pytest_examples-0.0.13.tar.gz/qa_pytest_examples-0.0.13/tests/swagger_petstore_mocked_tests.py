# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import asdict

import pytest
import responses
from hamcrest import is_  # type: ignore
from qa_pytest_examples.model.swagger_petstore_pet import SwaggerPetstorePet
from qa_pytest_examples.swagger_petstore_configuration import (
    SwaggerPetstoreConfiguration,
)
from qa_pytest_examples.swagger_petstore_steps import SwaggerPetstoreSteps
from qa_pytest_rest.rest_tests import RestTests
from qa_testing_utils.matchers import tracing, yields_item
from qa_testing_utils.string_utils import EMPTY_STRING


# --8<-- [start:class]
class SwaggerPetstoreMockedTests(
    RestTests[SwaggerPetstoreSteps[SwaggerPetstoreConfiguration],
              SwaggerPetstoreConfiguration]):
    _steps_type = SwaggerPetstoreSteps
    _configuration = SwaggerPetstoreConfiguration()

    # --8<-- [start:func]
    @pytest.mark.parametrize("pet", SwaggerPetstorePet.random(range(10)))
    @responses.activate
    def should_add(self, pet: SwaggerPetstorePet):
        responses.add(
            responses.POST,
            self.configuration.resource_uri(path="pet"),
            json=EMPTY_STRING,
            status=200)
        responses.add(
            responses.GET,
            self.configuration.resource_uri(path="pet/findByStatus"),
            json=[asdict(pet)],
            status=200)
        (self.steps
            .given.swagger_petstore(self.rest_session)
            .when.adding(pet)
            .then.the_available_pets(yields_item(tracing(is_(pet)))))
    # --8<-- [end:func]

# --8<-- [end:class]
