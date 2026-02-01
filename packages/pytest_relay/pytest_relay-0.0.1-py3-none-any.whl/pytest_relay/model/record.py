"""
Models related to records.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class RecordPhase(str, Enum):
    """
    Record phase, based on the ``report.when`` property of ``pytest``.
    Warnings report ["config", "collect", "runtest"]. For the sake of simplicity, "runtest"
    is mapped to "call".
    """

    COLLECT = "collect"
    CONFIG = "config"

    CALL = "call"
    SETUP = "setup"
    TEARDOWN = "teardown"

    @classmethod
    def from_when(cls, when: str) -> "RecordPhase":
        """
        Translates the ``report.when`` property of ``pytest`` records to this enumeration.
        """
        match when:
            case "config":
                return cls.CONFIG
            case "collect":
                return cls.COLLECT
            case "setup":
                return cls.SETUP
            case "call" | "runtest":
                return cls.CALL
            case "teardown":
                return cls.TEARDOWN
        raise ValueError(f"Invalid value '{when}' for RecordPhase")


class RecordSeverity(str, Enum):
    """
    Severity of a record.
    """

    INFO = "info"
    ERR = "error"
    WARN = "warning"
    DBG = "debug"


class Record(BaseModel):
    """
    Records are used by both, test sessions and test cases.
    They provide additional information, e.g., in case of failure.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    time: datetime = Field(default_factory=datetime.now)
    severity: RecordSeverity
    phase: RecordPhase
    msg: str
    #: optional additional source information, e.g., for modules and directories
    source: Optional[str] = None
