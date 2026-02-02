# SPDX-License-Identifier: Apache-2.0

# qa-pytest-rabbitmq

BDD-style RabbitMQ testing utilities for pytest.

## Structure
- `queue_handler.py`: Core logic for publishing/consuming messages.
- `message.py`: Message wrapper.
- `rabbitmq_configuration.py`: Test configuration.
- `rabbitmq_fixtures.py`, `rabbitmq_actions.py`, `rabbitmq_verifications.py`: BDD step classes.
- `rabbitmq_tests.py`: Base BDD test class.

## Usage
See `tests/test_rabbitmq_bdd.py` for an example BDD test skeleton.

## Dependencies
- pytest
- pyhamcrest
- pika
- qa-pytest-commons
- qa-testing-utils
