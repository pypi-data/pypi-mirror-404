"""
Observers.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel


class MessageType(str, Enum):
    """
    Supported message types.
    """

    TESTCASE = "testcase"
    SESSION = "session"


class Message(BaseModel):
    """
    Message format.
    """

    type: MessageType
    payload: dict[str, Any]


class Observer(ABC):  # pylint: disable=too-few-public-methods
    """
    Interface for an observer.
    """

    @abstractmethod
    def publish(self, message: Message) -> None:
        """
        Publishes the given message.
        """
        return None

    @abstractmethod
    def unregister(self) -> None:
        """
        Called when the pytest-relay plugin is unregistered.
        """
        return None
