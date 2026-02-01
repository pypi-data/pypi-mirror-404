"""
pytest-relay plugin, hooks and extraction logic.
"""

import os
import pathlib
import sys
import warnings
from datetime import datetime
from typing import Generator, List, Literal, Optional
from uuid import uuid4

import pytest
from _pytest._code.code import ExceptionInfo
from _pytest.config import Config, ExitCode
from _pytest.main import Session
from _pytest.nodes import Item
from _pytest.outcomes import Exit
from _pytest.reports import CollectReport, TestReport
from _pytest.terminal import TestShortLogReport

from pytest_relay import model


class RelayPlugin:
    """
    pytest relay plugin instance.
    """

    config: Config
    session: model.TestSession
    tests: model.TestList
    #: users of this plugin can register their own observers
    #: the life-cycle of registered observers must be managed by the user.
    _observers: List[model.Observer]

    def __init__(self, config: Config):
        self.config = config

        session_id: Optional[str] = config.option.session_id
        if session_id is None:
            session_id = str(uuid4())

        self.session = model.TestSession(id=session_id, state=model.State.OPEN)
        self.tests = model.TestList()

        self._observers: List[model.Observer] = []

    def _strip_root(self, msg: str) -> str:
        msg = msg.strip()

        if not self.config.option.strip_paths:
            return msg

        strip_paths = {
            # replace the root path in all messages.
            # this ensures that no local paths (e.g., in Exceptions) are in the records
            "pytest.rootpath": self.config.rootpath.resolve(),
            # replace the python's base installation's prefix
            "sys.base_prefix": pathlib.Path(sys.base_prefix).resolve(),
            # replace the executing python environment's prefix
            "sys.prefix": pathlib.Path(sys.prefix).resolve(),
        }

        for id_, path in strip_paths.items():
            msg = msg.replace(f"{path}{os.sep}", f"<{id_}>{os.sep}")
            msg = msg.replace(f"{path}", f"[{id_}]")
        return msg

    def register_observer(self, observer: model.Observer) -> None:
        """
        Registers the provided observer. On test updates, the observer's ``publish`` method
        is called with the corresponding message.

        Observers should be initialized in pytest's configuration phase with the corresponding
        connection parameters, and are torn down in ``unconfigure``.
        """
        self._observers.append(observer)

    def _notify_observers(self, msg: model.Message) -> None:
        for observer in self._observers:
            observer.publish(msg)

    def pytest_unconfigure(self, config: Config) -> None:
        """
        Hook: Called before test process is exited.
        """
        _ = config
        for observer in self._observers:
            observer.unregister()

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_collectreport(self, report: CollectReport) -> Generator[None, None, None]:
        """
        Hook: Collector finished collecting.

        This function is called for each directory, module, and file individually, whereas
        ``pytest_collection_finish`` is called after the full completion of the collection.
        This function is also called before the collection was modified, e.g., using the
        ``pytest_collection_modifyitems`` hook.

        This function is also called if the collection fails, e.g., due to syntax errors in some
        python files, and can therefore can be used to publish additional information.
        """
        if report.failed:
            rep = model.Record(
                phase=model.RecordPhase.COLLECT,
                severity=model.RecordSeverity.ERR,
                msg=self._strip_root(report.longreprtext),
                source=report.nodeid,
            )
            # TODO: collect sections
            self.session.record(rep)

        yield

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_collection_finish(self, session: Session) -> Generator[None, None, None]:
        """
        Hook: Called after the (full) collection has been performed and modified.

        This function is also called if the collection fails, but but ``session.items`` will not
        contain the items for which the collection failed or which have been removedby the
        ``pytest_collection_modifyitems`` hook. The session contains actual test cases and
        variants instead of files and directories.
        """
        yield

        # update the list of discovered test cases.
        self.session.tests = [item.nodeid for item in session.items]

        def truncate_args(config: Config) -> List[pathlib.Path]:
            resolved = []
            for arg in config.args:
                # ignore nodeid part of paths, e.g., `file.py::TestClass::test_func`
                pathpart = arg.split("::", 1)[0]
                p = pathlib.Path(pathpart)

                # resolve all paths that are not absolute relative to the invocation directory
                if not p.is_absolute():
                    p = config.invocation_params.dir / p
                p = p.resolve()

                # for all paths that are relative to the session's root path, shorten the path
                # by only providing the path that is relative to the root path.
                try:
                    p = p.relative_to(config.rootpath)
                except ValueError:
                    # path is outside rootpath
                    pass
                finally:
                    resolved.append(p)
            return resolved

        self.session.config = model.TestRuntimeCfg(
            rootpath=str(self.config.rootpath),
            invocation_dir=str(self.config.invocation_params.dir),
            args=[str(p) for p in truncate_args(self.config)],
        )

        if self.config.option.collectonly:
            self.session.state = model.State.DONE
        self._notify_observers(self.session.to_message())

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtestloop(self, session: Session) -> Generator[None, object, object]:
        """
        Hook: Perform the main runtest loop (after collection finished).
        """
        if not session.config.option.collectonly:
            self.session.time_start = datetime.now()
            self.session.state = model.State.IN_PROGRESS
            self._notify_observers(self.session.to_message())
        return (yield)

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_protocol(self, item: Item, nextitem: Item) -> Generator[None, None, None]:
        """
        Hook: Called to perform the runtest protocol for a single test item.

        This function is thus called once for every test item.
        For more information about the runtest protocol, see
        https://docs.pytest.org/en/stable/reference/reference.html#std-hook-pytest_runtest_protocol
        """
        _ = nextitem  # unused
        tc = self.tests.get_or_create(self.session.id, item.nodeid)
        tc.time_start = datetime.now()
        tc.state = model.State.IN_PROGRESS

        self._notify_observers(self.tests[item.nodeid].to_message())
        yield

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """
        Hook: Process the report produced for each phase of an item.
        """
        content_out = report.capstdout
        content_log = report.caplog
        content_err = report.capstderr

        _ = content_out
        _ = content_log
        _ = content_err

        # TODO: NYI

        # parser.addini(
        #     "junit_logging",
        #     "Write captured log messages to JUnit report: "
        #     "one of no|log|system-out|system-err|out-err|all",
        #     default="no",
        # )

        # if self.xml.logging == "no":
        #     return
        # content_all = ""
        # if self.xml.logging in ["log", "all"]:
        #     content_all = self._prepare_content(content_log, " Captured Log ")
        # if self.xml.logging in ["system-out", "out-err", "all"]:
        #     content_all += self._prepare_content(content_out, " Captured Out ")
        #     self._write_content(report, content_all, "system-out")
        #     content_all = ""
        # if self.xml.logging in ["system-err", "out-err", "all"]:
        #     content_all += self._prepare_content(content_err, " Captured Err ")
        #     self._write_content(report, content_all, "system-err")
        #     content_all = ""
        # if content_all:
        #     self._write_content(report, content_all, "system-out")

    @pytest.hookimpl(trylast=True)
    def pytest_warning_recorded(
        self,
        warning_message: warnings.WarningMessage,
        when: Literal["config", "collect", "runtest"],
        nodeid: str,
        location: tuple[str, int, str] | None,
    ) -> None:
        """
        Hook: Process a warning captured by the internal pytest warnings plugin.
        """
        _ = location  # unused

        if nodeid:
            # prefer the relative path instead of the absolute filename
            warning_message.filename = nodeid.split("::", 1)[0]

        rep = model.Record(
            phase=model.RecordPhase.from_when(when),
            severity=model.RecordSeverity.WARN,
            msg=self._strip_root(
                warnings.formatwarning(
                    message=str(warning_message.message),
                    category=warning_message.category,
                    filename=warning_message.filename,
                    lineno=warning_message.lineno,
                    line=warning_message.line,
                ),
            ),
        )

        if nodeid:
            # warning within a test case or one of its associated fixtures
            tc = self.tests[nodeid]
            tc.records.append(rep)
            self._notify_observers(tc.to_message())
        else:
            # warnings can also be raised during the collection or configuration phase
            # and may therefor not be associated to a certain test.
            self.session.record(rep)
            self._notify_observers(self.session.to_message())

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_report_teststatus(
        self, report: CollectReport | TestReport, config: Config
    ) -> Generator[None, None, None]:
        """
        Hook: Returns the result's category, shortletter and verbose word for status reporting.

        ``pytest`` implements this hook in its ``terminal.py`` module, where it also evaluates
        the overall test result (category) taking into account all failures, e.g., setup failures
        and teardown failures as well as the evaluation of the ``xfail`` marker.

        In contrast to ``pytest_runtest_makereport`` - which reports "success" for the "call" phase
        even if, e.g., the "setup" phase fails, the result category reflects the overall success
        of a test case.

        Depending on the test method, ``pytest`` may perform an **additional** execution of this
        hook, e.g., for the additional pass performed for the ``strict=True`` output:

        ```
        terminal.py::pytest_terminal_summary
            short_test_summary
                actions(_)=show_simple
                    for rep: BaseReport in self.stats.get(_, _)
                        _get_line_with_reprcrash_message
                            reports.py::BaseReport._get_verbose_word_with_markup
                                config.hook.pytest_report_teststatus
        ```

        The reported outcome is, however, always equivalent and it is therefore not necessary
        to perform an additional result update after all tests have been executed and reported.

        Note: This function is also called by ``pytest`` in case of errors during the collection
              phase. The report is then marked as ``report.when=collect``.
        """
        _ = config  # unused
        outcome: TestShortLogReport = TestShortLogReport(*(yield).get_result())  # type: ignore

        if self.session.state != model.State.IN_PROGRESS:
            return

        # we're only interested in the "call", "setup", and "teardown" phases, i.e., during
        # the runtest protocol. other phases, e.g., "collect", are not processed
        if report.when not in ["call", "setup", "teardown"]:
            return

        # the function is called for every phase, if it exists. if an outcome is provided, we
        # update the test's outcome. all these outcomes, however, are temporary until
        # the test's teardown phase, which might again overwrite the outcome.
        # empty outcomes are ignored.
        if not outcome.category:
            return

        tc = self.tests[report.nodeid]
        did_update = tc.update_category(outcome.category)

        # in addition to the outcome of the testcase, this hook is used to collect information
        # regarding failures, markers, or annotations that are provided by pytest in the
        # report's `longrepr`; this information is attached to the corresponding test case.
        if not report.longrepr:
            self._notify_observers(tc.to_message())
            return

        tc_records: List[model.Record] = []

        match tc.category:
            case model.TestCategory.PASS:
                # passed testcases should not report any long representation
                raise NotImplementedError(f"Unexpected report.longrepr for category {tc.category}")
            case model.TestCategory.XFAIL:
                # tests that should fail and failed list the exact location where the test failed
                # in the report's long representation. this can be useful for debugging.
                # however, the marker also allows specifying "run=False", which re-raises an
                # exception via pytest's own "xfail" and this we don't want to capture. this
                # raise happens in the test's setup phase.
                if not (report.outcome == "skipped" and report.when == "setup"):
                    tc_records.append(
                        model.Record(
                            phase=model.RecordPhase.from_when(report.when),
                            msg=self._strip_root(report.longreprtext),
                            severity=model.RecordSeverity.DBG,
                        )
                    )
                # in addition, the 'reason' of the xfail marker is stored as an attribute.
                # if no reason was given, the attribute still exists, but is empty
                if hasattr(report, "wasxfail") and report.wasxfail:
                    tc_records.append(
                        model.Record(
                            phase=model.RecordPhase.from_when(report.when),
                            msg=f"XFAIL({report.wasxfail})",
                            severity=model.RecordSeverity.INFO,
                        )
                    )

            case model.TestCategory.FAIL | model.TestCategory.ERR:
                # errors occur outside of the test method; failures are exceptions or assertions
                # within the test function. for both pytest tracks the exact error in the report's
                # long representation.
                tc_records.append(
                    model.Record(
                        phase=model.RecordPhase.from_when(report.when),
                        msg=self._strip_root(report.longreprtext),
                        severity=model.RecordSeverity.ERR,
                    )
                )
            case model.TestCategory.XPASS:
                # passed testcases, even if they fail, should not report any long representation.
                # there is no additional content that could be reported since the execution passed.
                raise NotImplementedError(f"Unexpected report.longrepr for category {tc.category}")
            case model.TestCategory.SKIPPED:
                # skipped tests report the absolute path, line number, and message of the marker.
                # we're only interested in the marker's message, if present.
                r: tuple[str, int, str] = report.longrepr  # type: ignore
                if r[2]:
                    tc_records.append(
                        model.Record(
                            phase=model.RecordPhase.from_when(report.when),
                            msg=self._strip_root(r[2]),
                            severity=model.RecordSeverity.INFO,
                        )
                    )
            case _:
                raise NotImplementedError(f"Missing case for category {tc.category}")

        for rep in tc_records:
            tc.record(rep)

        if did_update or len(tc_records) > 0:
            self._notify_observers(tc.to_message())

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_runtest_logstart(
        self, nodeid: str, location: tuple[str, int | None, str]
    ) -> Generator[None, None, None]:
        """
        Hook: Called at the start of running the runtest protocol for a single item.

        ``location`` is a tuple of ``(filename, lineno, testname)`` where
        - ``filename`` is a file path relative to ``config.rootpath``
        - and ``lineno`` is 0-based.
        """
        _ = nodeid
        _ = location
        yield

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_runtest_logfinish(
        self, nodeid: str, location: tuple[str, int | None, str]
    ) -> Generator[None, None, None]:
        """
        Hook: Called at the end of the runtest protocol for a single item.

        :param nodeid: Full node ID of the item.
        :param location: A tuple of ``(filename, lineno, testname)``
            where ``filename`` is a file path relative to ``config.rootpath``
            and ``lineno`` is 0-based.
        """
        _ = location  # unused
        yield

        self.tests[nodeid].time_stop = datetime.now()
        self.tests[nodeid].state = model.State.DONE
        self._notify_observers(self.tests[nodeid].to_message())

    def pytest_keyboard_interrupt(
        self,
        excinfo: ExceptionInfo[KeyboardInterrupt | Exit],
    ) -> None:
        """
        Hook: Called for keyboard interrupt and other interruptions.

        This function is also called, e.g., if the test collection fails with the``excinfo``
        ``<ExceptionInfo Interrupted('<n> error(s) during collection') tblen=<n>>
        """
        rep = model.Record(
            phase=model.RecordPhase.TEARDOWN,
            severity=model.RecordSeverity.ERR,
            msg=self._strip_root(str(excinfo.getrepr(style="auto"))),
        )

        self.tests.cancel_all(rep)
        for _tc in self.tests.values():
            tc: model.TestCase = _tc
            # cheap state update, doesn't require to track if changes were applied.
            # FEATURE: only notify unpublished modifications
            # FEATURE: add a report to each cancelled test
            self._notify_observers(tc.to_message())

        self.session.record(rep)
        # FEATURE: add "skipped" results for missing tests
        self._notify_observers(self.session.to_message())

    @pytest.hookimpl(wrapper=True, trylast=True)
    def pytest_sessionfinish(
        self, session: Session, exitstatus: int | ExitCode
    ) -> Generator[None, None, None]:
        """
        Hook: Called after whole test run finished, right before returning the exit
        status to the system.
        """

        if not session.config.option.collectonly:
            self.session.time_stop = datetime.now()
        self.session.state = model.State.DONE

        # update the session's exit status if anything fails internally
        session.exitstatus = self.session.finalize(exitstatus, list(self.tests.values()))
        self._notify_observers(self.session.to_message())
        yield
