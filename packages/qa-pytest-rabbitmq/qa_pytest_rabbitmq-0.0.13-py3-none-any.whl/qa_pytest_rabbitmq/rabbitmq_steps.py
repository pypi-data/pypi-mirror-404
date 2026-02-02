# SPDX-License-Identifier: Apache-2.0


from typing import Iterable, Iterator, Self, final

from hamcrest.core.matcher import Matcher
from qa_pytest_commons.generic_steps import GenericSteps
from qa_pytest_rabbitmq.queue_handler import Message, QueueHandler
from qa_pytest_rabbitmq.rabbitmq_configuration import RabbitMqConfiguration
from qa_testing_utils.logger import Context
from qa_testing_utils.object_utils import require_not_none


class RabbitMqSteps[K, V, TConfiguration: RabbitMqConfiguration](
        GenericSteps[TConfiguration]):
    """
    BDD-style step definitions for RabbitMQ queue operations.

    Type Parameters:
        K: The type of the message key.
        V: The type of the message content.
        TConfiguration: The configuration type, must be a RabbitMqConfiguration.
    """
    _queue_handler: QueueHandler[K, V]

    @Context.traced
    @final
    def a_queue_handler(self, queue_handler: QueueHandler[K, V]) -> Self:
        """
        Sets the queue handler to use for subsequent steps.

        Args:
            queue_handler (QueueHandler[K, V]): The handler instance.
        Returns:
            Self: The current step instance for chaining.
        """
        self._queue_handler = queue_handler
        return self

    @Context.traced
    @final
    def publishing(self, messages: Iterable[Message[V]]) -> Self:
        """
        Publishes the provided messages to the queue.

        Args:
            messages (Iterable[Message[V]]): The messages to publish.
        Returns:
            Self: The current step instance for chaining.
        """
        self._queue_handler.publish(iter(messages))
        return self

    @Context.traced
    @final
    def consuming(self) -> Self:
        """
        Starts consuming messages from the queue.

        Returns:
            Self: The current step instance for chaining.
        """
        self._queue_handler.consume()
        return self

    @Context.traced
    @final
    def the_received_messages(
            self, by_rule: Matcher[Iterator[Message[V]]]) -> Self:
        """
        Asserts that the received messages match the provided matcher rule.

        Args:
            by_rule (Matcher[Iterator[Message[V]]]): Matcher for the received messages iterator.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.eventually_assert_that(
            lambda: iter(self._queue_handler.received_messages.values()),
            by_rule)

    @Context.traced
    @final
    def the_message_by_key(
            self, key: K, by_rule: Matcher[Message[V]]) -> Self:
        """
        Asserts that the message with the given key matches the provided matcher rule.

        Args:
            key (K): The key to look up.
            by_rule (Matcher[Message[V]]): Matcher for the message.
        Returns:
            Self: The current step instance for chaining.
        """
        return self.eventually_assert_that(
            lambda: require_not_none(
                self._queue_handler.received_messages.get(key)),
            by_rule)
