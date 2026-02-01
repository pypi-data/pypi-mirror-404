"""
Models related to test cases.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Set

from pydantic import BaseModel, Field, ValidationError, computed_field

from pytest_relay.model.common import Result, State
from pytest_relay.model.observer import Message, MessageType
from pytest_relay.model.record import Record, RecordSeverity

logger: logging.Logger = logging.getLogger(__name__)


class TestCategory(str, Enum):
    """
    Test result category.
    See also, ``_pytest/terminal.py::pytest_terminal_summary``.
    """

    PASS = "passed"
    """The execution passed."""

    XFAIL = "xfailed"
    """The execution was expected to fail and failed."""

    FAIL = "failed"
    """The test execution failed."""

    ERR = "error"
    """
    The test's setup or teardown failed.

    In such a case, the test execution itself may have been successful (e.g., if only the teardown
    of the fixture failed), but the overall execution of the test failed.
    """

    XPASS = "xpassed"
    """
    The execution was expected to fail but passed.

    Without the argument ``--strict-markers`` or without the ``strict=True`` annotation at the
    test case, this result is also considered as "passed" by convention (e.g., a bug was fixed
    which was previously expected to fail). With the mentioned arguments and for any test that
    is marked as "expected to fail", the ``pytest`` uses the result ``FAIL``.
    """

    SKIPPED = "skipped"
    """The test has not been executed"""

    @property
    def is_failure(self) -> bool:
        """
        Determines whether the category is considered a failure or error (unsuccessful).
        """
        if self in [
            TestCategory.PASS,
            TestCategory.XFAIL,
            TestCategory.XPASS,  # notice that with --strict-markers the result is FAIL
            TestCategory.SKIPPED,
        ]:
            return False
        return True

    @property
    def is_success(self) -> bool:
        """
        Determines whether the category is considered a successful execution.
        """
        return not self.is_failure

    def to_result(self) -> Result:
        """
        Converts the category to the simplified ``Result`` type.
        """
        match self:
            case TestCategory.PASS:
                return Result.GREEN
            case TestCategory.XFAIL | TestCategory.XPASS:
                # notice that TestCategory.XPASS is also considered YELLOW since in strict
                # mode the reported result is actually FAIL
                return Result.YELLOW
            case TestCategory.SKIPPED:
                return Result.NONE
            case _:
                return Result.RED


class TestCase(BaseModel):
    """Test case."""

    #: fields that are ignored when comparing test cases
    exclude: ClassVar[Set[str]] = {
        "idx",
        "time_start",
        "time_stop",
    }

    #: associated session
    session_id: str
    #: unique execution index _within a session_
    idx: int = -1
    # the nodeid of the item
    name: str
    #: start of the execution
    time_start: Optional[datetime] = None
    #: end of the execution
    time_stop: Optional[datetime] = None
    #: result category, determines the actual outcome
    category: Optional[TestCategory] = None
    #: errors, warnings, report representations added by pytest, e.g., XPASS(STRICT)
    records: List[Record] = Field(default_factory=list)
    #: testcase state
    state: State

    def to_message(self) -> Message:
        """
        'Serialize' into a message.
        """
        return Message(
            type=MessageType.TESTCASE,
            payload=self.model_dump(),
        )

    def update_category(self, category: str) -> bool:
        """
        Updates the category of test case, if applicable. The category is update if it has either
        not been set yet, or if a successful execution turnes into a failure (transformation
        of ``success`` into ``failure``).

        Returns ``True`` if the category was updated, otherwise ``False``
        """
        cat = self.category
        try:
            res = TestCategory(category)
        except ValidationError as exc:
            logger.error("Invalid category '%s': %s", category, exc)
            res = TestCategory.FAIL

        if (cat is None) or (cat.is_success and res.is_failure):
            self.category = res
        return cat == res

    @computed_field  # type: ignore[prop-decorator]
    @property
    def result(self) -> Optional[Result]:
        """
        Computed property to determine the simplified result of the test case.
        """
        if self.category is None:
            return None
        res = self.category.to_result()
        if res == Result.GREEN:
            # override the result if there is a reported warning
            if (
                next((r for r in self.records if r.severity == RecordSeverity.WARN), None)
                is not None
            ):
                res = Result.YELLOW
        return res

    def record(self, rep: Record) -> None:
        """
        Simple helper to add a record.
        """
        self.records.append(rep)

    def model_dump_reduce(self, exclude: None | Set[str] = None) -> Dict[str, Any]:
        """
        Reduces the model for comparison against other objects, ignoring fields that are set during
        runtime and are always different from other instance's values, e.g., timestamps or unique
        identifiers.
        """
        if exclude is None:
            exclude = self.exclude
        return self.model_dump(exclude=exclude)

    def prettify(self, indent: int = 2) -> str:
        """
        Pretty-prints the session to a string, replacing escaped newline characters within
        records with actual newlines for command-line output.
        """
        return (
            json.dumps(json.loads(self.model_dump_json(indent=indent)), indent=indent)
            .encode()
            .decode("unicode-escape")
        )
