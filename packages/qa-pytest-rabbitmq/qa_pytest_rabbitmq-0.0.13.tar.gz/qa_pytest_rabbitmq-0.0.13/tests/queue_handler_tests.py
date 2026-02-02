# SPDX-License-Identifier: Apache-2.0

from contextlib import closing
from typing import cast

import pika
from hamcrest import assert_that, equal_to, has_length
from qa_pytest_rabbitmq._abstract_queue_handler_tests import (
    AbstractQueueHandlerTests,
)
from qa_pytest_rabbitmq.queue_handler import QueueHandler
from qa_testing_utils.object_utils import require_not_none
from qa_testing_utils.string_utils import EMPTY_STRING
from string_utils.generation import random_string


class QueueHandlerTests(AbstractQueueHandlerTests):
    """
    Integration tests for the QueueHandler class, verifying publish and consume operations with RabbitMQ.
    """

    # NOTE: sudo rabbitmqctl status -- ensure RabbitMQ is running
    # otherwise, sudo rabbitmq-server -detached
    def should_have_a_working_rabbitmq(self) -> None:
        """
        Verifies that RabbitMQ is running and can publish/consume a message directly using pika.
        """
        some_text = random_string(10)
        with closing(pika.BlockingConnection(self.local_rabbit_mq)) as connection:
            with closing(connection.channel()) as channel:

                channel.basic_publish(
                    exchange=EMPTY_STRING,
                    routing_key=self.trace(
                        queue_name := require_not_none(
                            channel.queue_declare(
                                queue=EMPTY_STRING,
                                exclusive=True)
                            .method
                            .queue)),
                    body=some_text.encode())

                # NOTE types-pika incorrectly stubs body as str...
                _, _, body = channel.basic_get(
                    queue=queue_name,
                    auto_ack=True)

                assert_that(cast(bytes, body).decode(), equal_to(some_text))

    def should_publish_and_retrieve(self) -> None:
        """
        Tests publishing and consuming messages using QueueHandler, ensuring all messages are received.
        """
        with pika.BlockingConnection(self.local_rabbit_mq) as connection:
            with connection.channel() as channel:
                with QueueHandler(
                        channel=channel,
                        queue_name=require_not_none(channel.queue_declare(
                            queue=EMPTY_STRING, exclusive=True).method.queue),
                        indexing_by=lambda message: message.content,
                        consuming_by=lambda bytes: bytes.decode(),
                        publishing_by=lambda string: string.encode()) as queue_handler:

                    queue_handler.publish_values(iter(["a", "b", "c"]))
                    queue_handler.consume()
                    queue_handler.cancel()
                    queue_handler.publish_values(iter(["d", "e", "f"]))
                    queue_handler.consume()

                    self.retrying(
                        lambda: assert_that(
                            queue_handler.received_messages,
                            has_length(6)))
