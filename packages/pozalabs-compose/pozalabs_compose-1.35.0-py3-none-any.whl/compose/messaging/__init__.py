from .consumer import MessageConsumer
from .consumer_runner import FastAPIMessageConsumerRunner, ThreadMessageConsumerRunner
from .messagebus import MessageBus
from .model import EventMessage, SqsEventMessage
from .publisher import EventPublisher
from .queue.base import MessageQueue
from .queue.local import LocalMessageQueue, event_store
from .signal_handler import DefaultSignalHandler, SignalHandler, ThreadSignalHandler

__all__ = [
    "DefaultSignalHandler",
    "EventMessage",
    "EventPublisher",
    "FastAPIMessageConsumerRunner",
    "LocalMessageQueue",
    "MessageBus",
    "MessageConsumer",
    "MessageQueue",
    "SignalHandler",
    "SqsEventMessage",
    "ThreadMessageConsumerRunner",
    "ThreadSignalHandler",
    "event_store",
]

try:
    from .queue.sqs import SqsMessageQueue  # noqa: F401

    __all__.append("SqsMessageQueue")
except ImportError:
    pass


try:
    from .consumer.fastapi import MessageConsumerASGIMiddleware  # noqa: F401

    __all__.append("MessageConsumerASGIMiddleware")
except ImportError:
    pass
