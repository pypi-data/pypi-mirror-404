# SPDX-License-Identifier: Apache-2.0

from functools import cached_property

import pika
from qa_pytest_commons.base_configuration import BaseConfiguration


class RabbitMqConfiguration(BaseConfiguration):
    """
    RabbitMQ-specific test configuration.
    Provides access to the RabbitMQ connection URI from the configuration parser.
    """

    @cached_property
    def connection_uri(self) -> pika.URLParameters:
        """
        Returns the RabbitMQ connection URI as a pika.URLParameters object.

        Returns:
            pika.URLParameters: The connection URI for RabbitMQ.
        """
        return pika.URLParameters(self.parser.get("rabbitmq", "connection_uri"))
