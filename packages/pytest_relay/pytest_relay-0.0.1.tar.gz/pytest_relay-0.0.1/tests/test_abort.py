# pylint: disable=missing-function-docstring,missing-module-docstring,wrong-import-order

import json  # pylint: disable=unused-import
import re
import signal
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import List, NamedTuple, Optional

from _pytest.config import ExitCode
from _pytest.pytester import Pytester, RunResult
from helpers import make_test

from pytest_relay.model import Message, RecordPhase, RecordSeverity, Result, State
from pytest_relay.model import TestCategory as Cat

import helpers  # isort: skip
from observer import SimpleObserver  # isort: skip


class RunRes(NamedTuple):
    """
    Mini RunResult for pytester-like execution.
    """

    stdout: str
    stderr: str
    returncode: Optional[int]


def _runpytest_with_timeout(cmd: list[str], cwd: Path, timeout: float) -> RunRes:
    proc = subprocess.Popen(  # pylint: disable=consider-using-with
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.send_signal(signal.SIGINT)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

    return RunRes(stdout=stdout, stderr=stderr, returncode=proc.returncode)


def _extract(lines: List[str]) -> List[str]:
    """
    Extract all occurrences of text wrapped between <!--message-begin--> and <!--message-end-->
    markers, where markers and text can span multiple lines.
    """
    full_text = "\n".join(lines)
    pattern = re.compile(r"<!--message-begin-->(.*?)<!--message-end-->", re.DOTALL)
    return pattern.findall(full_text)


def test_abort_interrupt(pytester: Pytester, obs: SimpleObserver, sid: str) -> None:
    """
    Test behavior on test run interruption

    Test interruption requires using a subprocess. Therefore, the approach is the following.

    - Implement a simple Observer that logs the messages to stdout.
    - Parse the standard output after the process has been run, extract the observer's output.
    - Feed them into the ``SimpleObserver``.
    - Evaluate as usual.
    """
    _ = pytester.makefile(".ini", pytest=helpers.get_default_ini())
    _ = pytester.makeconftest(
        textwrap.dedent(
            """
            from typing import Any

            import pytest
            from _pytest.config import Config

            from pytest_relay.model import Message, Observer


            class PrintObserver(Observer):
                def publish(self, message: Message) -> None:
                    msg_str: str = message.model_dump_json(indent=2)
                    print(f"<!--message-begin-->{msg_str}<!--message-end-->")

                def unregister(self) -> None:
                    pass


            def pytest_configure(config: Config) -> None:
                p: Any = config.pluginmanager.get_plugin("pytest_relay")
                if p is not None:
                    p.register_observer(PrintObserver())
            """
        )
    )

    package: Path = pytester.mkpydir("sub")
    (package / "test_mod.py").write_text(
        textwrap.dedent(
            """
            from time import sleep

            def test_pre():
                assert True

            def test_sleepy():
                sleep(10)
                assert True

            def test_post():
                assert True
            """
        ),
        encoding="utf-8",
    )

    # try:
    #     _: RunResult = pytester.runpytest_subprocess(str(package), "-q", timeout=1)
    # except Pytester.TimeoutExpired:
    #     # can't use this since I'm losing stdout
    #     pass
    result = _runpytest_with_timeout(
        [
            sys.executable,
            "-m",
            "pytest",
            str(package),
            "-q",
            f"--session-id={sid}",
        ],
        cwd=pytester.path,
        timeout=1,
    )

    # read the messages from stout and feed them back into our SimpleObserver
    for m in [Message(**json.loads(m)) for m in _extract(result.stdout.splitlines())]:
        obs.publish(m)

    assert obs.session is not None
    assert obs.session.tests == [
        "sub/test_mod.py::test_pre",
        "sub/test_mod.py::test_sleepy",
        "sub/test_mod.py::test_post",
    ]

    # similarity check. test_post is missing since the execution is interrupted before it executes.
    helpers.compare_testcases(
        actual=obs.tests,
        extra_exclude={"records"},
        expected=[
            make_test(sid, idx=0, name="sub/test_mod.py::test_pre", category=Cat.PASS),
            make_test(sid, idx=0, name="sub/test_mod.py::test_sleepy", category=Cat.FAIL),
        ],
    )

    # test_sleepy gets a marker for the interrupt
    assert len(obs.tests[0].records) == 0
    assert len(obs.tests[1].records) == 1

    rep = obs.tests[1].records[0]
    assert rep.phase == RecordPhase.TEARDOWN
    assert rep.severity == RecordSeverity.ERR
    assert helpers.get_exception_str(KeyboardInterrupt()) in rep.msg
    assert rep.source is None

    # there are two records in the session
    # - one error report lists the actual interruption
    # - the debug report informs that the "pytest execution [was] interrupted"
    assert len(obs.session.records) == 2

    rep = obs.session.records[0]
    assert rep.phase == RecordPhase.TEARDOWN
    assert rep.severity == RecordSeverity.ERR
    assert "KeyboardInterrupt" in rep.msg
    assert rep.source is None

    rep = obs.session.records[1]
    assert rep.phase == RecordPhase.TEARDOWN
    assert rep.severity == RecordSeverity.DBG
    assert rep.msg == "pytest execution interrupted"
    assert rep.source == "pytest"

    # the overall result is RED since it has been terminated
    assert obs.session.result == Result.RED
    assert obs.session.state == State.DONE
    # print(obs.session.prettify(indent=2))
    # print(json.dumps([json.loads(tc.prettify()) for tc in obs.tests], indent=2))


def test_abort_usage(pytester: Pytester, obs: SimpleObserver) -> None:
    """
    Behavior of pytest-relay in case of usage errors.
    """
    helpers.pytest_init_default(pytester, "SimpleObserver")

    result = pytester.runpytest("--unknown-option", "-p no:relay_ws")
    assert result.ret == ExitCode.USAGE_ERROR

    assert obs.session is None
    assert obs.tests == []


def test_abort_internal(pytester: Pytester, obs: SimpleObserver) -> None:
    """
    Behavior of pytest-relay in case of an internal error.
    """
    _ = pytester.makefile(".ini", pytest=helpers.get_default_ini())
    _ = pytester.makeconftest(
        ""
        + helpers.get_conftest_observer("SimpleObserver")
        + textwrap.dedent(
            """
            from typing import Any

            import pytest
            from _pytest.config import Config

            from pytest_relay.model import Message, Observer

            class PrintObserver(Observer):
                def publish(self, message: Message) -> None:
                    msg_str: str = message.model_dump_json(indent=2)
                    print(f"<!--message-begin-->{msg_str}<!--message-end-->")
                def unregister(self) -> None:
                    pass

            def pytest_configure(config: Config) -> None:
                p: Any = config.pluginmanager.get_plugin("pytest_relay")
                if p is not None:
                    p.register_observer(PrintObserver())

            def pytest_sessionstart(session):
                raise RuntimeError("simulated internal error")
            """
        )
    )

    result: RunResult = pytester.runpytest("-q", "-p no:relay_ws")
    assert result.ret == ExitCode.INTERNAL_ERROR

    assert obs.session is None
    assert obs.tests == []
