"""
Models related to test sessions.
"""

import json
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Set

from _pytest.config import ExitCode
from pydantic import BaseModel, Field

from pytest_relay.model.common import Result, State
from pytest_relay.model.observer import Message, MessageType
from pytest_relay.model.record import Record, RecordPhase, RecordSeverity
from pytest_relay.model.testcase import TestCase

# custom exit code that is larger than pytest's own
_EXIT_MAX = max(code.value for code in ExitCode) + 1


class TestRuntimeCfg(BaseModel):
    """
    Pytest runtime configuration.
    """

    #: directory from which pytest was executed
    invocation_dir: str
    #: rootpath of the execution
    rootpath: str
    #: positional arguments passed to pytest
    args: List[str] = Field(default_factory=list)


class TestSession(BaseModel):
    """
    Test sessions represent a single run of a set of discovered test cases.
    """

    #: fields that are ignored when comparing test cases
    exclude: ClassVar[set[str]] = {
        "id",
        "time_start",
        "time_stop",
    }

    #: unique identifier for the session
    id: str
    #: session-related errors, e.g., collection errors
    records: List[Record] = Field(default_factory=list)
    #: discovered test cases; only the test IDs are stored
    tests: List[str] = Field(default_factory=list)
    #: start of the execution
    time_start: Optional[datetime] = None
    #: end of the execution
    time_stop: Optional[datetime] = None
    #: simplified result type
    result: Optional[Result] = None
    #: runtime configuration
    config: Optional[TestRuntimeCfg] = None
    #: session state
    state: State

    def to_message(self) -> Message:
        """
        'Serialize' into a message.
        """
        return Message(
            type=MessageType.SESSION,
            payload=self.model_dump(),
        )

    def record(self, rep: Record) -> None:
        """
        Simple helper to add a record.
        """
        self.records.append(rep)

    def _record_exitcode(self, exitstatus: int | ExitCode) -> None:
        msg: Optional[str] = None
        match exitstatus:
            case ExitCode.OK | ExitCode.TESTS_FAILED:
                # nothing to do, the test execution should show all problems
                pass
            case ExitCode.INTERRUPTED:
                msg = "pytest execution interrupted"
            case ExitCode.INTERNAL_ERROR:
                msg = "pytest encountered an internal error"
            case ExitCode.USAGE_ERROR:
                msg = "pytest invocation (usage) error encountered"
            case ExitCode.NO_TESTS_COLLECTED:
                msg = "pytest couldn't find any tests"
            case _:
                msg = f"pytest execution failed with the exit status {exitstatus}"

        if msg is not None:
            rep = Record(
                phase=RecordPhase.TEARDOWN,
                msg=msg,
                severity=RecordSeverity.DBG,
                source="pytest",
            )
            self.records.append(rep)

    def _verify_testcases(
        self, testcases: List[TestCase], exitstatus: int | ExitCode
    ) -> int | ExitCode:
        # verify: check that there are no testcases that have no result
        tc_no_result = [tc.name for tc in testcases if tc.category is None]

        # raise ValidationError(
        #     "pytest execution did not provide results exist the following testcases: "
        #         + json.dumps(tc_no_result, indent=2))

        if tc_no_result:
            rep = Record(
                phase=RecordPhase.TEARDOWN,
                msg="pytest execution did not provide results exist the following testcases: "
                + json.dumps(tc_no_result, indent=2),
                severity=RecordSeverity.ERR,
                source="verify(pytest)",
            )
            self.records.append(rep)
            exitstatus = _EXIT_MAX

        # verify: find testcases that have been executed but are not part of the discovery list
        miss_disc = [tc.name for tc in testcases if tc.name not in self.tests]

        if miss_disc:
            rep = Record(
                phase=RecordPhase.TEARDOWN,
                msg="the following tests have been executed "
                + "but were not reported in the collection phase by pytest: "
                + json.dumps(miss_disc, indent=2),
                severity=RecordSeverity.ERR,
                source="verify(pytest)",
            )
            self.records.append(rep)
            exitstatus = _EXIT_MAX

        return exitstatus

    def finalize(self, exitstatus: int | ExitCode, testcases: List[TestCase]) -> int | ExitCode:
        """
        Finalizes the test session by evaluating the exit code and triggering internal
        validation methods.
        """
        self._record_exitcode(exitstatus)
        exitstatus = self._verify_testcases(testcases, exitstatus)

        # verify: pytest must not report "OK" if there are failed tests
        n_tc_fail = sum(1 for test in testcases if test.category and test.category.is_failure)

        if n_tc_fail > 0 and exitstatus == ExitCode.OK:
            rep = Record(
                phase=RecordPhase.TEARDOWN,
                msg=f"{n_tc_fail} testcases failed but pytest attempts to "
                + "report the exit code 'OK'. override active.",
                severity=RecordSeverity.ERR,
                source="verify(pytest)",
            )
            self.records.append(rep)
            exitstatus = _EXIT_MAX

        n_warn = sum(1 for report in self.records if report.severity == RecordSeverity.WARN) + sum(
            1 for tc in testcases if tc.result == Result.YELLOW
        )
        n_err = sum(1 for report in self.records if report.severity == RecordSeverity.ERR)

        if exitstatus != ExitCode.OK or n_err > 0:
            self.result = Result.RED
            exitstatus = exitstatus if exitstatus != ExitCode.OK else ExitCode.INTERNAL_ERROR
        elif n_warn > 0:
            self.result = Result.YELLOW
        else:
            self.result = Result.GREEN
        return exitstatus

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

    def get_testcase(self, **kwargs: Any) -> TestCase:
        """
        Creates a testcase that has the session's ID.
        """
        return TestCase(session_id=self.id, **kwargs)
