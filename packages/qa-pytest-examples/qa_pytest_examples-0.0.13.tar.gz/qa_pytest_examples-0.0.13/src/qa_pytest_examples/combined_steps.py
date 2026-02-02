from qa_pytest_examples.combined_configuration import CombinedConfiguration
from qa_pytest_examples.swagger_petstore_steps import SwaggerPetstoreSteps
from qa_pytest_examples.terminalx_steps import TerminalXSteps


class CombinedSteps(
        SwaggerPetstoreSteps[CombinedConfiguration],
        TerminalXSteps[CombinedConfiguration]):
    """
    Combined steps implementation that inherits step definitions from both
    SwaggerPetstoreSteps and TerminalXSteps, using CombinedConfiguration.
    Useful for scenarios requiring both sets of step logic in a single test suite.
    """
    pass
