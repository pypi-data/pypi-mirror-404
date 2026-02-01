"""
Observer for testing, accumulates published data.
"""

# pylint: disable=missing-class-docstring,missing-function-docstring

from abc import ABCMeta
from typing import Dict, List, Optional

from pytest_relay.model import Message, MessageType, Observer, TestCase, TestSession


class Singleton(type):
    _instances: Dict = {}

    def __call__(cls, *args, **kwargs):  # type: ignore
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonABC(Singleton, ABCMeta):
    pass


class SimpleObserver(Observer, metaclass=SingletonABC):
    """
    Simple observer, doesn't parse message paths but only updates its state.
    """

    def __init__(self) -> None:
        self.tests: List[TestCase] = []
        self.session: Optional[TestSession] = None

    def reset(self) -> None:
        self.tests.clear()
        self.session = None

    def _update_session(self, session: TestSession) -> None:
        self.session = session

    def _update_testcase(self, testcase: TestCase) -> None:
        if testcase.idx < len(self.tests):
            # for any existing index the testcase name must match (state is obv. updated)
            assert self.tests[testcase.idx].name == testcase.name
            self.tests[testcase.idx] = testcase
        else:
            # if its a new testcase, its index should be strictly monotonic
            assert testcase.idx == len(self.tests)
            self.tests.append(testcase)

    def publish(self, message: Message) -> None:
        match message.type:
            case MessageType.SESSION:
                self._update_session(TestSession(**message.payload))
            case MessageType.TESTCASE:
                self._update_testcase(TestCase(**message.payload))
        # print(message.model_dump_json(indent=2))

    def unregister(self) -> None:
        pass
