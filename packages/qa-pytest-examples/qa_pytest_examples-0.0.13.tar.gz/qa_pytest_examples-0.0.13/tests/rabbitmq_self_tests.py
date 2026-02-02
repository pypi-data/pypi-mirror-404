# SPDX-License-Identifier: Apache-2.0
from typing import override

from hamcrest import is_  # type: ignore
from qa_pytest_examples.rabbitmq_self_configuration import (
    RabbitMqSelfConfiguration,
)
from qa_pytest_rabbitmq.queue_handler import Message, QueueHandler
from qa_pytest_rabbitmq.rabbitmq_steps import RabbitMqSteps
from qa_pytest_rabbitmq.rabbitmq_tests import RabbitMqTests
from qa_testing_utils.matchers import tracing, yields_item
from qa_testing_utils.object_utils import require_not_none
from qa_testing_utils.string_utils import EMPTY_STRING


# --8<-- [start:class]
class RabbitMqSelfTests(
    RabbitMqTests[int, str,
                  RabbitMqSteps[int, str, RabbitMqSelfConfiguration],
                  RabbitMqSelfConfiguration]):
    _queue_handler: QueueHandler[int, str]
    _steps_type = RabbitMqSteps
    _configuration = RabbitMqSelfConfiguration()

    # --8<-- [start:func]
    def should_publish_and_consume(self) -> None:
        (self.steps
            .given.a_queue_handler(self._queue_handler)
            .when.publishing([Message("test_queue")])
            .and_.consuming()
            .then.the_received_messages(yields_item(
                tracing(is_(Message("test_queue"))))))
    # --8<-- [end:func]

    @override
    def setup_method(self) -> None:
        super().setup_method()
        self._queue_handler = QueueHandler(
            channel := self._connection.channel(),
            queue_name=require_not_none(
                channel.queue_declare(
                    queue=EMPTY_STRING, exclusive=True).method.queue),
            indexing_by=lambda message: hash(message.content),
            consuming_by=lambda bytes: bytes.decode(),
            publishing_by=lambda string: string.encode())

    @override
    def teardown_method(self) -> None:
        try:
            self._queue_handler.close()
        finally:
            super().teardown_method()
# --8<-- [end:class]
