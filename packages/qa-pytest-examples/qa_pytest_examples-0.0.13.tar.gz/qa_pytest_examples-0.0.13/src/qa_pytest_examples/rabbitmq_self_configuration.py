# SPDX-License-Identifier: Apache-2.0

from qa_pytest_rabbitmq.rabbitmq_configuration import RabbitMqConfiguration


class RabbitMqSelfConfiguration(RabbitMqConfiguration):
    """
    Configuration for self-contained RabbitMQ test scenarios.
    Inherits all settings from RabbitMqConfiguration and can be extended for
    test-specific overrides or additional configuration.
    """
    pass
