# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from hamcrest import is_  # type: ignore
from qa_pytest_examples.model.swagger_petstore_pet import SwaggerPetstorePet
from qa_pytest_examples.swagger_petstore_configuration import (
    SwaggerPetstoreConfiguration,
)
from qa_pytest_examples.swagger_petstore_steps import SwaggerPetstoreSteps
from qa_pytest_rest.rest_tests import RestTests
from qa_testing_utils.matchers import tracing, yields_item


# --8<-- [start:class]
@pytest.mark.external
class SwaggerPetstoreTests(
    RestTests[SwaggerPetstoreSteps[SwaggerPetstoreConfiguration],
              SwaggerPetstoreConfiguration]):
    _steps_type = SwaggerPetstoreSteps
    _configuration = SwaggerPetstoreConfiguration()

    # --8<-- [start:func]
    @pytest.mark.parametrize("pet", SwaggerPetstorePet.random(range(4)))
    def should_add(self, pet: SwaggerPetstorePet):
        (self.steps
            .given.swagger_petstore(self.rest_session)
            .when.adding(pet)
            .then.the_available_pets(yields_item(tracing(is_(pet)))))
    # --8<-- [end:func]

# --8<-- [end:class]
