# SPDX-License-Identifier: Apache-2.0
"""
Abstract base for QueueHandler tests, ported from Java AbstractQueueHandlerTest.
"""
import logging
from abc import ABC
from functools import cached_property

import pika
from qa_testing_utils.logger import LoggerMixin
from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class AbstractQueueHandlerTests(ABC, LoggerMixin):
    """
    Abstract base class for QueueHandler tests.
    Provides RabbitMQ connection parameters and retry logic for subclasses.
    """

    @cached_property
    def local_rabbit_mq(self) -> pika.URLParameters:
        """
        Returns the local RabbitMQ connection parameters.

        Returns:
            pika.URLParameters: Connection parameters for local RabbitMQ.
        """
        return pika.URLParameters("amqp://guest:guest@localhost")

    @cached_property
    def retrying(self) -> Retrying:
        """
        Returns a configured Retrying object for retrying test assertions.

        Returns:
            Retrying: The tenacity.Retrying instance for retries.
        """
        return Retrying(
            stop=stop_after_attempt(4),
            wait=wait_exponential(min=1, max=10),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(self.log, logging.DEBUG),
        )
