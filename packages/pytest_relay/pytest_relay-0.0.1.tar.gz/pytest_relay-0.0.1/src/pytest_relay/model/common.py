"""
Models for common properties of sessions and testcases.
"""

from enum import Enum


class State(str, Enum):
    """
    State information for testcases and sessions.
    """

    OPEN = "open"
    IN_PROGRESS = "in-progress"
    DONE = "done"


class Result(str, Enum):
    """
    Simplified result.
    """

    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    NONE = "none"  # skipped
