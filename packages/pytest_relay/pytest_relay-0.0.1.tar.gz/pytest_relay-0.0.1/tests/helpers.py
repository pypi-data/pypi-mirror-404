# pylint: disable=missing-function-docstring,missing-module-docstring

import textwrap
import traceback
from typing import Any, List, Set

from pytest import Pytester

from pytest_relay import model


def get_default_ini() -> str:
    return textwrap.dedent(
        """
               [pytest]
               asyncio_default_fixture_loop_scope = function
               """
    )


def get_conftest_observer(classname: str) -> str:
    return textwrap.dedent(
        f"""
            from typing import Any

            from _pytest.config import Config
            from observer import {classname}

            def pytest_configure(config: Config) -> None:
                p: Any = config.pluginmanager.get_plugin("pytest_relay")
                if p is not None:
                    p.register_observer({classname}())
            """
    )


def get_exception_str(e: BaseException) -> str:
    return "".join(traceback.format_exception_only(type(e), e)).strip()


def pytest_init_default(pytester: Pytester, observer: str) -> None:
    _ = pytester.makeconftest(get_conftest_observer(observer))
    _ = pytester.makefile(".ini", pytest=get_default_ini())


def compare_testcases(
    actual: List[model.TestCase],
    expected: List[model.TestCase],
    extra_exclude: None | Set[str] = None,
) -> None:
    """
    Compares the reduced models of the given ``actual`` and ``expected`` testcases.
    The reduced models do not include unique fields such as timestamps or UUIDs. The parameter
    ``extra_exclude`` may contain **additional** fields that should be ignored.
    """
    # exclude = {*model.TestCase.exclude, "records"}
    exclude = model.TestCase.exclude
    if extra_exclude:
        exclude = exclude.union(extra_exclude)

    r_act = [tc.model_dump_reduce(exclude) for tc in actual]
    r_exp = [tc.model_dump_reduce(exclude) for tc in expected]

    # import json
    # print(json.dumps([json.loads(tc.prettify()) for tc in actual], indent=2))
    # print(json.dumps([json.loads(tc.prettify()) for tc in expected], indent=2))

    assert len(actual) == len(expected)
    assert r_act == r_exp


def make_test(
    session_id: str, state: model.State = model.State.DONE, **kwargs: Any
) -> model.TestCase:
    return model.TestCase(session_id=session_id, state=state, **kwargs)
