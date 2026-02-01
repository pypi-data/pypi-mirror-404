# pylint: disable=missing-function-docstring,missing-module-docstring,wrong-import-order

import json  # pylint: disable=unused-import
import re
import textwrap
from pathlib import Path

from _pytest.config import ExitCode
from _pytest.pytester import Pytester, RunResult
from helpers import make_test

from pytest_relay.model import RecordPhase, RecordSeverity, Result, State
from pytest_relay.model import TestCase as Case
from pytest_relay.model import TestCategory as Cat

import helpers  # isort: skip
from observer import SimpleObserver  # isort: skip


def test_run_passes(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'passed'.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text("def test_a(): pass\n")
    (package / "test_b.py").write_text("def test_b(): pass\n")

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    # all tests are green
    assert result.ret == ExitCode.OK

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == [
        "sub/test_a.py::test_a",
        "sub/test_b.py::test_b",
    ]

    # similarity check
    helpers.compare_testcases(
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_a.py::test_a", category=Cat.PASS),
            make_test(sid, idx=0, name="sub/test_b.py::test_b", category=Cat.PASS),
        ],
    )

    # the overall result is OK
    assert obs.session.result == Result.GREEN


def test_run_continue_on_collection_errors(
    pytester: Pytester, obs: SimpleObserver, sid: str
) -> None:
    """
    Tests the execution of tests despite collection errors, which are tolerated due to the
    pytest flag ``--continue-on-collection-errors``.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text("def test_a( : typo\n")
    (package / "test_b.py").write_text("def test_b(): pass\n")

    result: RunResult = pytester.runpytest(
        str(package),
        "--continue-on-collection-errors",
        f"--session-id={sid}",
        "-q",
        "--strip-paths",
    )
    # test_b is executed due to ``--continue-on-collection-errors`` but since the collection
    # of test_a.py failed, the overall execution is still marked as failed by pytest.
    assert result.ret == ExitCode.TESTS_FAILED

    # test_a.py has a typo and therefore it's test is not collected
    assert obs.session is not None
    assert obs.session.tests == [
        "sub/test_b.py::test_b",
    ]

    # since we're specifying ``--continue-on-collection-errors`` only test_b is executed
    helpers.compare_testcases(
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_b.py::test_b", category=Cat.PASS),
        ],
    )

    # the overall result is RED
    assert obs.session.result == Result.RED

    # print(obs.session.prettify(indent=2))
    # print(json.dumps([json.loads(tc.prettify()) for tc in obs.tests], indent=2))


def test_run_xfailures(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'xfail'.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.mark.xfail(reason="bug-123")
            def test_xfail():
                assert False
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    # pytest records OK - tests failed but they expected to fail
    assert result.ret == ExitCode.OK

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == ["sub/test_a.py::test_xfail"]

    # similarity check, ignoring unique fields and the records since xfail creates a debug
    # report with the exact location of the line that caused the test to fail (as expected)
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_a.py::test_xfail", category=Cat.XFAIL),
        ],
    )

    # XFAIL generates two records within the test case
    # - one debug report with the location of the expected failure
    # - one debug report with the reason annotated in the marker (if it exists)
    assert len(obs.tests[0].records) == 2

    rep = obs.tests[0].records[0]
    assert rep.phase == RecordPhase.CALL
    assert rep.severity == RecordSeverity.DBG
    assert re.search(r"sub\/test_a\.py:\d+: AssertionError", rep.msg)

    rep = obs.tests[0].records[1]
    assert rep.phase == RecordPhase.CALL
    assert rep.severity == RecordSeverity.INFO
    assert "bug-123" in rep.msg
    assert rep.source is None

    # the overall result is YELLOW since XFAIL is reported by pytest in yellow
    # notice that JUNIT captures XFAIL as "skipped"
    assert obs.session.result == Result.YELLOW


def test_run_xfailures_raises(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'xfail' specifying the expected raised exception.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.mark.xfail(reason="bug-123", raises=(Exception, ValueError), strict=True)
            def test_xfail():
                raise ValueError("exc-bug-123")
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    # pytest records OK - tests failed but they expected to fail
    assert result.ret == ExitCode.OK
    assert obs.session is not None and obs.session.tests == ["sub/test_a.py::test_xfail"]

    # similarity check, ignoring unique fields and the records since xfail creates a debug
    # report with the exact location of the line that caused the test to fail (as expected)
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_a.py::test_xfail", category=Cat.XFAIL),
        ],
    )

    # XFAIL generates two records within the test case
    # - one debug report with the location of the expected failure
    # - one debug report with the reason annotated in the marker (if it exists)
    assert len(obs.tests[0].records) == 2

    rep = obs.tests[0].records[0]
    assert rep.phase == RecordPhase.CALL
    assert rep.severity == RecordSeverity.DBG
    assert re.search(r"sub\/test_a\.py:\d+: ValueError", rep.msg)

    rep = obs.tests[0].records[1]
    assert rep.phase == RecordPhase.CALL
    assert rep.severity == RecordSeverity.INFO
    assert "bug-123" in rep.msg
    assert rep.source is None

    # the overall result is YELLOW since XFAIL is reported by pytest in yellow
    assert obs.session.result == Result.YELLOW


def test_run_failures_xfail_raises(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'xfail' specifying the expected raised exception - but it doesn't match.
    Attention: If the exception is a subclass of the listed ``raises``, then this won't work.
    E.g., listing ``Exception`` in ``raises`` will catch pretty much anything, same as with
    try/except blocks.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.mark.xfail(reason="bug-123", raises=(ValueError), strict=True)
            def test_xfail():
                raise Exception("exc-bug-123")
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    # pytest records TESTS_FAILED - tests failed but not with the expected exceptions
    assert result.ret == ExitCode.TESTS_FAILED
    assert obs.session is not None and obs.session.tests == ["sub/test_a.py::test_xfail"]

    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_a.py::test_xfail", category=Cat.FAIL),
        ],
    )

    # XFAIL generates one records within the test case for the mismatch
    assert len(obs.tests[0].records) == 1

    rep = obs.tests[0].records[0]
    assert rep.phase == RecordPhase.CALL
    assert rep.severity == RecordSeverity.ERR
    assert re.search(r"sub\/test_a\.py:\d+: Exception", rep.msg)

    assert obs.session.result == Result.RED


def test_run_xfailures_notrun(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'NOTRUN' tests due to the marker ``@pytest.mark.xfail(run=False)``
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_mod.py").write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.mark.xfail(reason="bug-123", raises=(Exception), strict=True, run=False)
            def test_xfail_skipped():
                raise ValueError("exc-bug-123")
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    assert result.ret == ExitCode.OK

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == ["sub/test_mod.py::test_xfail_skipped"]

    # similarity check, ignoring records (checked below)
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_mod.py::test_xfail_skipped", category=Cat.XFAIL),
        ],
    )

    # both tests records an assertion error in the setup phase due to the fixture's error
    assert len(obs.tests[0].records) == 1

    rep = obs.tests[0].records[0]
    assert rep.phase == RecordPhase.SETUP
    assert rep.severity == RecordSeverity.INFO
    assert rep.msg == "XFAIL([NOTRUN] bug-123)"

    # the overall result is YELLOW since at least one test was skipped
    assert obs.session.result == Result.YELLOW


def test_run_xpasses(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'xpass' - expected failure due to ``@pytest.mark.xfail`` mark, but the test passed.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.mark.xfail(reason="bug-123")
            def test_xfail():
                assert True
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    # pytest records OK - tests expected to fail but they passed
    # without the ``strict=True`` argument, this is not considered a failure since the markers
    # are used to annotate tests that should pass in the future (e.g., a bug has been fixed).
    assert result.ret == ExitCode.OK

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == ["sub/test_a.py::test_xfail"]

    # similarity check, including records since XPASS doesn't generate any report:
    # there is no location to report since the test passed (even though it was expected to fail)
    helpers.compare_testcases(
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_a.py::test_xfail", category=Cat.XPASS),
        ],
    )

    # the overall result is YELLOW since XPASS is reported by pytest in yellow
    assert obs.session.result == Result.YELLOW


def test_run_xpasses_strict(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'xpass' - expected failure but passed, with ``@pytest.mark.xfail(strict=True)``
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.mark.xfail(reason="bug-123", strict=True)
            def test_xfail():
                assert True
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    # pytest records FAILED_TESTS - tests expected to fail but they passed and we're using
    # the ``strict=True`` argument in the marker.
    assert result.ret == ExitCode.TESTS_FAILED

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == ["sub/test_a.py::test_xfail"]

    # similarity check, excluding records since the test will receive a report ``XPASS(strict)``
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_a.py::test_xfail", category=Cat.FAIL),
        ],
    )

    # XPASS with ``strict=True`` generates an error report within the test case
    assert len(obs.tests[0].records) == 1

    rep = obs.tests[0].records[0]
    assert rep.phase == RecordPhase.CALL
    assert rep.severity == RecordSeverity.ERR
    assert rep.msg == "[XPASS(strict)] bug-123"
    assert rep.source is None

    # the overall result is RED due to the``strict=True`` mark.
    assert obs.session.result == Result.RED


def test_run_failures(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'fail'.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_a.py").write_text("def test_a(): assert False\n")
    (package / "test_b.py").write_text("def test_b(): raise Exception('something')\n")
    (package / "test_c.py").write_text("def test_c(): assert True\n")

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    assert result.ret == ExitCode.TESTS_FAILED

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == [
        "sub/test_a.py::test_a",
        "sub/test_b.py::test_b",
        "sub/test_c.py::test_c",
    ]

    # similarity check, ignoring records (checked below)
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_a.py::test_a", category=Cat.FAIL),
            make_test(sid, idx=0, name="sub/test_b.py::test_b", category=Cat.FAIL),
            make_test(sid, idx=0, name="sub/test_c.py::test_c", category=Cat.PASS),
        ],
    )

    # the first test records an assertion error
    rep = obs.tests[0].records[0]
    assert rep.phase == RecordPhase.CALL
    assert rep.severity == RecordSeverity.ERR
    assert re.search(r"sub\/test_a\.py:\d+: AssertionError", rep.msg)

    # the second test records an exception
    rep = obs.tests[1].records[0]
    assert rep.phase == RecordPhase.CALL
    assert rep.severity == RecordSeverity.ERR
    assert helpers.get_exception_str(Exception("something")) in rep.msg
    assert rep.source is None

    # the overall result is RED since at least one test failed
    assert obs.session.result == Result.RED


def test_run_skipped(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'skipped' tests.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_mod.py").write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.mark.skip(reason="run-123")
            def test_skip(fix):
                assert fix == "something"
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    assert result.ret == ExitCode.OK

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == ["sub/test_mod.py::test_skip"]

    # similarity check, ignoring records (checked below)
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_mod.py::test_skip", category=Cat.SKIPPED),
        ],
    )
    # no result for skipped tests
    assert obs.tests[0].result == Result.NONE

    # the test records the skip reason in the setup phase
    assert len(obs.tests[0].records) == 1

    rep = obs.tests[0].records[0]
    assert rep.phase == RecordPhase.SETUP
    assert rep.severity == RecordSeverity.INFO
    assert rep.msg == "Skipped: run-123"

    # the overall result is GREEN
    assert obs.session.result == Result.GREEN


def test_run_errors_setup(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'err' - errors in the setup phase which lead to failed test cases.
    Notice that the test itself may even run successfully.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_mod.py").write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.fixture(scope="module")
            def fix():
                # error in the setup phase of the fixture
                raise Exception("err-setup")
                yield "something"

            def test_a(fix):
                assert fix == "something"

            def test_b(fix):
                assert fix == "something"
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    assert result.ret == ExitCode.TESTS_FAILED

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == [
        "sub/test_mod.py::test_a",
        "sub/test_mod.py::test_b",
    ]

    # similarity check, ignoring records (checked below)
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_mod.py::test_a", category=Cat.ERR),
            make_test(sid, idx=0, name="sub/test_mod.py::test_b", category=Cat.ERR),
        ],
    )

    # both tests records an assertion error in the setup phase due to the fixture's error
    assert len(obs.tests[0].records) == 1
    assert len(obs.tests[1].records) == 1

    reps = [obs.tests[0].records[0], obs.tests[1].records[0]]
    for rep in reps:
        assert rep.phase == RecordPhase.SETUP
        assert rep.severity == RecordSeverity.ERR
        assert helpers.get_exception_str(Exception("err-setup")) in rep.msg
        assert rep.source is None

    # the overall result is RED since at least one test failed
    assert obs.session.result == Result.RED


def test_run_errors_teardown(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'err' - errors in the teardown phase which lead to a failed test case.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_mod.py").write_text(
        textwrap.dedent(
            """
            import pytest

            @pytest.fixture(scope="module")
            def fix():
                yield "something"
                # error in the teardown phase of the fixture
                raise Exception("err-teardown")

            def test_a(fix):
                assert fix == "something"

            def test_b(fix):
                assert fix == "something"
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    assert result.ret == ExitCode.TESTS_FAILED

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == [
        "sub/test_mod.py::test_a",
        "sub/test_mod.py::test_b",
    ]

    # similarity check, ignoring records (checked below)
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            make_test(sid, idx=0, name="sub/test_mod.py::test_a", category=Cat.PASS),
            make_test(sid, idx=0, name="sub/test_mod.py::test_b", category=Cat.ERR),
        ],
    )

    # only the second test records an error since it is affected by the fixture's teardown phase:
    # the fixture is module-scoped and therefore the teardown is executed after the last test
    # in the module. its error is attached to the executing test
    assert len(obs.tests[0].records) == 0
    assert len(obs.tests[1].records) == 1

    rep = obs.tests[1].records[0]
    assert rep.phase == RecordPhase.TEARDOWN
    assert rep.severity == RecordSeverity.ERR
    assert helpers.get_exception_str(Exception("err-teardown")) in rep.msg
    assert rep.source is None

    # the overall result is RED since at least one test failed
    assert obs.session.result == Result.RED


def test_run_warn(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'warnings' - test cases can contain warnings. they still pass but the result is YELLOW.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_mod.py").write_text(
        textwrap.dedent(
            """
            import pytest
            import warnings

            def test_warn():
                warnings.warn(UserWarning("warn-test"))
                assert True
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    assert result.ret == ExitCode.OK

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == ["sub/test_mod.py::test_warn"]

    # similarity check, ignoring records (checked below)
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            type(
                "CaseWithResult",
                (Case,),
                {"result": property(lambda self: Result.YELLOW)},
            )(
                state=State.DONE,
                session_id=sid,
                idx=0,
                name="sub/test_mod.py::test_warn",
                category=Cat.PASS,
            ),
        ],
    )

    # the warning is registered for the testcase
    assert len(obs.tests[0].records) == 1

    rep = obs.tests[0].records[0]
    assert rep.phase == RecordPhase.CALL
    assert rep.severity == RecordSeverity.WARN
    assert re.search(r"sub\/test_mod\.py:\d+: UserWarning: warn-test", rep.msg)
    assert rep.source is None

    # the overall result is YELLOW since at least one warning was encountered
    assert obs.session.result == Result.YELLOW


def test_run_warn_fixture(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Tests 'warnings' - test case where the used fixture contains warnings.
    They test passes but the result is YELLOW even though there is no warning within the test
    case itself.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    package: Path = pytester.mkpydir("sub")
    (package / "test_mod.py").write_text(
        textwrap.dedent(
            """
            import pytest
            import warnings

            @pytest.fixture(scope="function")
            def fix_warn():
                warnings.warn(UserWarning("warn-setup"))
                yield
                warnings.warn(UserWarning("warn-teardown"))

            def test_warn(fix_warn):
                assert True
            """
        ),
        encoding="utf-8",
    )

    result: RunResult = pytester.runpytest(str(package), "-q", f"--session-id={sid}")
    assert result.ret == ExitCode.OK

    # the tests discovered in the session match the package
    assert obs.session is not None
    assert obs.session.tests == ["sub/test_mod.py::test_warn"]

    # similarity check, ignoring records (checked below)
    helpers.compare_testcases(
        extra_exclude={"records"},
        actual=obs.tests,
        expected=[
            type(
                "CaseWithResult",
                (Case,),
                {"result": property(lambda self: Result.YELLOW)},
            )(
                state=State.DONE,
                session_id=sid,
                idx=0,
                name="sub/test_mod.py::test_warn",
                category=Cat.PASS,
            ),
        ],
    )

    # the warnings are registered for the testcase. notice that both, setup and teardown,
    # use the phase "call" since there is no distinction in the warning system.
    assert len(obs.tests[0].records) == 2

    warn_msg = [
        (0, r"warn-setup"),
        (1, r"warn-teardown"),
    ]
    for idx, msg in warn_msg:
        rep = obs.tests[0].records[idx]
        assert rep.phase == RecordPhase.CALL
        assert rep.severity == RecordSeverity.WARN
        assert re.search(r"sub\/test_mod\.py:\d+: UserWarning: " + msg, rep.msg)
        assert rep.source is None

    # the overall result is YELLOW since at least one warning was encountered
    assert obs.session.result == Result.YELLOW
