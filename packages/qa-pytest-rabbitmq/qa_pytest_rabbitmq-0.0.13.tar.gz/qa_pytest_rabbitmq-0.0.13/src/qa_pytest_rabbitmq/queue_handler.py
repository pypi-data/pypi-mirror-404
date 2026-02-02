# SPDX-License-Identifier: Apache-2.0

import queue
import threading
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Callable, Final, Iterator, Mapping, final

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import BasicProperties
from qa_testing_utils.logger import LoggerMixin
from qa_testing_utils.object_utils import require_not_none
from qa_testing_utils.string_utils import EMPTY_STRING, to_string


@to_string()
@dataclass(frozen=True)
class Message[V]:
    """
    Represents a message to be published or consumed from a RabbitMQ queue.

    Attributes:
        content (V): The message payload.
        properties (BasicProperties): Optional message properties for RabbitMQ.
    """
    content: V
    properties: BasicProperties = field(default_factory=BasicProperties)


@to_string()
@dataclass
@final
class QueueHandler[K, V](LoggerMixin):
    """
    Handles publishing and consuming messages from a RabbitMQ queue in a thread-safe, asynchronous manner.

    Args:
        channel (BlockingChannel): The RabbitMQ channel to use.
        queue_name (str): The name of the queue to operate on.
        indexing_by (Callable): Function to extract a key from a message.
        consuming_by (Callable): Function to deserialize message bytes.
        publishing_by (Callable): Function to serialize message content.
    """
    channel: Final[BlockingChannel]
    queue_name: Final[str]
    indexing_by: Final[Callable[[Message[V]], K]]
    consuming_by: Final[Callable[[bytes], V]]
    publishing_by: Final[Callable[[V], bytes]]

    _received_messages: Final[dict[K, Message[V]]] = field(
        default_factory=lambda: dict())
    _command_queue: Final[queue.Queue[Callable[[], None]]] = field(
        default_factory=lambda: queue.Queue())

    _worker_thread: threading.Thread = field(init=False)
    _shutdown_event: threading.Event = field(
        default_factory=threading.Event, init=False)
    _consumer_tag: str | None = field(default=None, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def __post_init__(self) -> None:
        """
        Starts the worker thread for handling asynchronous queue operations.
        """
        self._worker_thread = threading.Thread(
            target=self._worker_loop, name="rabbitmq-handler", daemon=True)
        self._worker_thread.start()

    def __enter__(self) -> "QueueHandler[K, V]":
        """
        Context manager entry. Returns self.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None
    ) -> None:
        """
        Context manager exit. Ensures the handler is closed and resources are released.
        """
        self.close()

    def _worker_loop(self) -> None:
        """
        Internal worker loop for processing commands and RabbitMQ events.
        """
        while not self._shutdown_event.is_set():
            try:
                self.channel.connection.process_data_events()
                try:
                    command = self._command_queue.get_nowait()
                    command()
                except queue.Empty:
                    pass
            except Exception as e:
                self.log.error(f"Unhandled error in worker thread: {e}")

    def _submit(self, fn: Callable[[], None]) -> None:
        """
        Submits a callable to be executed by the worker thread.
        """
        self._command_queue.put(fn)

    def consume(self) -> str:
        """
        Starts consuming messages from the queue asynchronously.
        Returns:
            str: A placeholder consumer tag (actual tag is set internally).
        """
        def _consume():
            def on_message(ch: BlockingChannel, method: Any,
                           props: BasicProperties, body: bytes) -> None:
                try:
                    content = self.consuming_by(body)
                    message = Message(content=content, properties=props)
                    key = self.indexing_by(message)
                    with self._lock:
                        self._received_messages[key] = message
                    ch.basic_ack(
                        delivery_tag=require_not_none(
                            method.delivery_tag))
                    self.log.debug(f"received {key}")
                except Exception as e:
                    self.log.warning(f"skipping message due to error: {e}")
                    ch.basic_reject(
                        delivery_tag=require_not_none(
                            method.delivery_tag),
                        requeue=True)

            self._consumer_tag = self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=on_message
            )
            self.log.debug(f"consumer set up with tag {self._consumer_tag}")

        self._submit(_consume)
        return "pending-tag"

    def cancel(self) -> str:
        """
        Cancels the active consumer, if any.
        Returns:
            str: The previous consumer tag, or an empty string if none.
        """
        def _cancel():
            if self._consumer_tag:
                self.channel.connection.add_callback_threadsafe(
                    self.channel.stop_consuming)
                self._consumer_tag = None
                self.log.debug("consumer cancelled")
        self._submit(_cancel)
        return self._consumer_tag or ""

    def publish(self, messages: Iterator[Message[V]]) -> None:
        """
        Publishes an iterable of Message objects to the queue asynchronously.

        Args:
            messages (Iterator[Message[V]]): The messages to publish.
        """
        def _publish():
            for message in messages:
                body = self.publishing_by(message.content)
                self.channel.basic_publish(
                    exchange=EMPTY_STRING,
                    routing_key=self.queue_name,
                    body=body,
                    properties=message.properties
                )
                self.log.debug(f"published {message}")
        self._submit(_publish)

    def publish_values(self, values: Iterator[V]) -> None:
        """
        Publishes an iterable of values to the queue, wrapping each in a Message.

        Args:
            values (Iterator[V]): The values to publish.
        """
        self.publish((Message(content=value) for value in values))

    def close(self) -> None:
        """
        Gracefully shuts down the handler, cancels consumers, and joins the worker thread.
        """
        self.cancel()
        self._shutdown_event.set()
        self._worker_thread.join(timeout=5.0)

    @property
    def received_messages(self) -> Mapping[K, Message[V]]:
        """
        Returns a snapshot of all received messages, indexed by key.

        Returns:
            Mapping[K, Message[V]]: The received messages.
        """
        with self._lock:
            return dict(self._received_messages)
