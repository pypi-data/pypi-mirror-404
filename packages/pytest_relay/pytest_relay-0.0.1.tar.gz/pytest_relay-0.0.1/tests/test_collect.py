# pylint: disable=missing-function-docstring,missing-module-docstring,wrong-import-order

import textwrap
from pathlib import Path
from typing import Optional

from _pytest.config import ExitCode
from _pytest.pytester import Pytester, RunResult

from pytest_relay import model

import helpers  # isort: skip
from observer import SimpleObserver  # isort: skip


def test_collect_ok(pytester: Pytester, obs: SimpleObserver) -> None:
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text("def test_a(): pass\n")
    (package / "test_b.py").write_text("def test_b(): pass\n")

    result: RunResult = pytester.runpytest(
        str(package),
        "--collect-only",
        "-q",
        "--strip-paths",
    )
    assert result.ret == ExitCode.OK
    assert obs.session is not None

    # no tests have been executed and no problems are expected while collecting
    assert len(obs.tests) == 0
    # the tests discovered in the session match the package
    assert obs.session.tests == [
        "sub/test_a.py::test_a",
        "sub/test_b.py::test_b",
    ]

    # the overall result of the collection is OK
    assert obs.session.result == model.Result.GREEN
    # the state of the session is "DONE" due to the invocation with --collect-only
    assert obs.session.state == model.State.DONE


def test_collect_err(pytester: Pytester, obs: SimpleObserver) -> None:
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text("def test_a( : typo\n")
    (package / "test_b.py").write_text("def test_b(): pass\n")

    result: RunResult = pytester.runpytest(
        str(package),
        "--collect-only",
        "-q",
        "--strip-paths",
    )
    assert result.ret == ExitCode.INTERRUPTED
    assert obs.session is not None

    # no tests have been executed and therefore no tests are reported
    assert len(obs.tests) == 0
    # only test_b is discovered since the module test_a.py has an issue
    assert obs.session.tests == [
        "sub/test_b.py::test_b",
    ]

    # for test_a.py there is an error report in the session information
    rep: Optional[model.Record] = next(
        (r for r in obs.session.records if r.source == "sub/test_a.py"), None
    )
    assert rep is not None
    assert rep.phase == model.RecordPhase.COLLECT
    assert "SyntaxError" in rep.msg

    assert obs.session.result == model.Result.RED
    assert obs.session.state == model.State.DONE


def test_collect_none(pytester: Pytester, obs: SimpleObserver) -> None:
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    result: RunResult = pytester.runpytest(
        str(package),
        "--collect-only",
        "-q",
        "--strip-paths",
    )
    assert result.ret == ExitCode.NO_TESTS_COLLECTED
    assert obs.session is not None

    # no tests have been executed and therefore no tests are reported
    assert len(obs.tests) == 0
    # only test_b is discovered since the module test_a.py has an issue
    assert len(obs.session.tests) == 0

    # there is a single report stating that no tests were found
    assert len(obs.session.records) == 1

    rep = obs.session.records[0]
    assert rep.phase == model.RecordPhase.TEARDOWN
    assert rep.severity == model.RecordSeverity.DBG
    assert rep.msg == "pytest couldn't find any tests"
    assert rep.source == "pytest"

    assert obs.session.result == model.Result.RED
    assert obs.session.state == model.State.DONE


def test_collect_warn(pytester: Pytester, obs: SimpleObserver) -> None:
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_warn.py").write_text(
        textwrap.dedent(
            """
            import pytest
            import warnings

            warnings.warn(UserWarning("warn-module"))

            def test_a():
                warnings.warn(UserWarning("warn-test"))
                pass
            """
        ),
        encoding="utf-8",
    )
    result: RunResult = pytester.runpytest(
        str(package),
        "--collect-only",
        "-q",
        "--strip-paths",
    )
    assert result.ret == ExitCode.OK
    assert obs.session is not None

    # no tests have been executed and therefore no tests are reported, test_a is discovered
    assert len(obs.tests) == 0
    assert len(obs.session.tests) == 1

    # there is a single report containing the module's warning
    # the warning of the test case is not picked up since it hasn't been executed yet.
    assert len(obs.session.records) == 1

    rep = obs.session.records[0]
    assert rep.phase == model.RecordPhase.COLLECT
    assert rep.severity == model.RecordSeverity.WARN
    assert "UserWarning: warn-module" in rep.msg
    assert rep.source is None

    assert obs.session.result == model.Result.YELLOW
    assert obs.session.state == model.State.DONE
