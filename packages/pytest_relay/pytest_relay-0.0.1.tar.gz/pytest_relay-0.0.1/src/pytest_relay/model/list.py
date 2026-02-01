"""
Eat me.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Dict, Iterator

from pytest_relay.model.common import State
from pytest_relay.model.record import Record
from pytest_relay.model.testcase import TestCase, TestCategory


class TestList(Mapping):
    """
    Wrapper class for managing tests as an "ordered" dictionary.
    """

    #: dictionary to access tests by their node ID
    _tests: Dict[str, TestCase]
    #: current number of tests
    _cnt: int

    def __add_or_create(
        self, key: str, session_id: str | None = None, tc: None | TestCase = None
    ) -> TestCase:
        if tc is None and session_id is not None:
            tc = TestCase(session_id=session_id, name=key, state=State.OPEN)
        assert tc is not None

        tc.idx = self._cnt
        self._cnt += 1
        self._tests[key] = tc
        return tc

    def __init__(self) -> None:
        self._cnt = 0
        self._tests: Dict[str, TestCase] = {}

    def __getitem__(self, key: str) -> TestCase:
        return self._tests[key]

    def __setitem__(self, key: str, value: TestCase) -> None:
        assert key == value.name

        if key in self._tests:
            raise ValueError(f"Duplicate test case '{key}'")

        self.__add_or_create(key=key, tc=value)

    def __iter__(self) -> Iterator[str]:
        return iter(self._tests)

    def __len__(self) -> int:
        return len(self._tests)

    def append(self, value: TestCase) -> None:
        """
        List-like access to add a new test case.
        """
        self._tests[value.name] = value

    # deleting items is not allowed
    # def __delitem__(self, key):

    def __contains__(self, key: object) -> bool:
        return key in self._tests

    def __repr__(self) -> str:
        items = sorted(self._tests.items(), key=lambda item: item[1].idx)
        body = ", ".join(f"{k!r}: {v!r}" for k, v in items)
        return f"{self.__class__.__name__}({{{body}}})"

    def get_or_create(self, session_id: str, key: str) -> TestCase:
        """
        If a testcase for the given ``key`` exists, then it returns the test case.
        Otherwise, a new test case instance is created and returned.
        """
        if key in self._tests:
            return self._tests[key]
        return self.__add_or_create(key=key, session_id=session_id)

    def cancel_all(self, record: Record) -> None:
        """
        Marks all tests with open results as failed and sets the stop time.
        """
        for tc in self._tests.values():
            if tc.category is None:
                tc.records.append(record)
                tc.time_stop = datetime.now()
                tc.category = TestCategory.FAIL
                tc.state = State.DONE
