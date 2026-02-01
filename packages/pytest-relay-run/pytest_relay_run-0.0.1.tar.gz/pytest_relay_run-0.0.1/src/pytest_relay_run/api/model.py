"""
API model.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class JobState(str, Enum):
    """Execution state of a job."""

    CREATED = "created"
    COLLECTED = "collected"
    IN_PROGRESS = "in-progress"
    DONE = "done"
    TERMINATING = "terminating"


class JobRequest(BaseModel):
    """Parameters accepted for job creation."""

    # TODO: consider accepting an executable such that the test can be run as a module
    # TODO: or using tools like poetry, uv, poe ... it could even support `tox` to some extent.

    id: Optional[str]
    args: List[str]
    collect_only: bool = False


class JobResponse(BaseModel):
    """Job information exposed via the API."""

    id: str
    state: JobState
    returncode: Optional[int] = None
    text: Optional[str] = None


class JobAction(str, Enum):
    """Action identifiers supported for jobs."""

    START = "start"
    STOP = "stop"


class JobActionRequest(BaseModel):
    """Model for action requests."""

    action: JobAction
