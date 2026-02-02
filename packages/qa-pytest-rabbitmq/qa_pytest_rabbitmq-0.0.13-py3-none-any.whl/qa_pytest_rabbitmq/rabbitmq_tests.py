# SPDX-License-Identifier: Apache-2.0

from typing import Any, override

import pika
from qa_pytest_commons.abstract_tests_base import AbstractTestsBase
from qa_pytest_rabbitmq.rabbitmq_configuration import RabbitMqConfiguration
from qa_pytest_rabbitmq.rabbitmq_steps import RabbitMqSteps


class RabbitMqTests[
    K,
    V,
    TSteps: RabbitMqSteps[Any, Any, Any],
    TConfiguration: RabbitMqConfiguration
](AbstractTestsBase[TSteps, TConfiguration]):
    """
    Base class for BDD-style RabbitMQ integration tests.
    Manages the lifecycle of a RabbitMQ connection for test scenarios.

    Type Args:
        K: The type of the message key.
        V: The type of the message content.
        TSteps: The steps implementation type.
        TConfiguration: The configuration type, must be a RabbitMqConfiguration.
    """
    _connection: pika.BlockingConnection

    @override
    def setup_method(self):
        """
        Sets up the RabbitMQ connection before each test method.
        """
        super().setup_method()
        self._connection = pika.BlockingConnection(
            self._configuration.connection_uri)

    @override
    def teardown_method(self):
        """
        Tears down the RabbitMQ connection after each test method.
        """
        try:
            self._connection.close()
        finally:
            super().teardown_method()
