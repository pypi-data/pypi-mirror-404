import random

import pytest
from hamcrest import is_  # type: ignore
from qa_pytest_examples.combined_configuration import CombinedConfiguration
from qa_pytest_examples.combined_steps import CombinedSteps
from qa_pytest_examples.model.swagger_petstore_pet import SwaggerPetstorePet
from qa_pytest_rest.rest_tests import RestTests
from qa_pytest_webdriver.selenium_tests import SeleniumTests
from qa_testing_utils.matchers import tracing, yields_item


# --8<-- [start:class]
@pytest.mark.external
@pytest.mark.ui
class CombinedTests(
        RestTests[CombinedSteps, CombinedConfiguration],
        SeleniumTests[CombinedSteps, CombinedConfiguration]):
    _steps_type = CombinedSteps
    _configuration = CombinedConfiguration()

    def should_run_combined_tests(self):
        random_pet = next(SwaggerPetstorePet.random())
        random_user = random.choice(self.configuration.users)

        (self.steps
            .given.swagger_petstore(self.rest_session)
            .when.adding(random_pet)
            .then.the_available_pets(yields_item(tracing(is_(random_pet))))
            .given.terminalx(self.ui_context)
            .when.logging_in_with(random_user.credentials)
            .then.the_user_logged_in(is_(random_user.name)))
# --8<-- [end:class]
