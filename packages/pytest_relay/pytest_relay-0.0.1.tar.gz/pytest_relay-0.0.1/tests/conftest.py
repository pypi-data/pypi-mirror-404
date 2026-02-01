# pylint: skip-file
# https://docs.pytest.org/en/stable/how-to/writing_plugins.html#testing-plugins
pytest_plugins = "pytester"

from typing import Generator
from uuid import uuid4

import pytest
from observer import SimpleObserver


@pytest.fixture(scope="function")
def obs() -> Generator[SimpleObserver, None, None]:
    obs = SimpleObserver()
    obs.reset()
    yield obs
    obs.reset()


@pytest.fixture(scope="function")
def sid() -> str:
    return str(uuid4())
