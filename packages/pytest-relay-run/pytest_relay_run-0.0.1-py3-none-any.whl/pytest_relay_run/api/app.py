"""
Job execution API.
"""

import shlex
from http import HTTPStatus
from typing import List, Optional, Tuple

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.requests import Request
from fastapi.responses import Response

from pytest_relay_run.api.job import Job, JobManager
from pytest_relay_run.api.model import JobAction, JobActionRequest, JobRequest, JobResponse

router = APIRouter()
# router.include_router(items.router)
# router.include_router(others.router)

jobs = JobManager(max_sessions=100)


def _job_get(id_: str) -> Job:
    job: Optional[Job] = jobs.get(id_, None)
    if job is None:
        raise HTTPException(404, f"Job with ID '{id_}' found")
    return job


def _split_args(args: List[str]) -> List[str]:
    """
    Sanitize a list of arguments to be suitable for subprocess calls by splitting any arguments
    containing spaces into separate elements.
    """
    sanitized: List[str] = []

    for arg in args:
        sanitized.extend(shlex.split(arg))
    return sanitized


def _extract_session_id(args: List[str]) -> Optional[str]:
    """
    Extract the value of --session-id from a list of arguments.
    Returns the first session ID if provided, otherwise None.
    """
    it = iter(args)
    for arg in it:
        if arg.startswith("--session-id="):
            return arg.split("=", 1)[1]
        if arg == "--session-id":
            # Next element is the value, if it exists
            try:
                return next(it)
            except StopIteration:
                return None
    return None


def _parse_args(args: List[str], job_id: Optional[str]) -> Tuple[List[str], Optional[str]]:
    """
    Sanitizes the argument list and extracts the session ID, if available.
    Returns a tuple (args, job_id) where job_id is either the provided job_id or the session ID
    from the job's argument list.
    """
    args = [arg for arg in _split_args(args) if arg != "--collect-only"]
    session_id = _extract_session_id(args)

    if job_id is not None and session_id is not None and job_id != session_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"The provided job ID '{job_id}' "
            f"does not match the session ID '{session_id}' "
            "provided in the job's argument list.",
        )

    job_id = job_id if job_id is not None else session_id
    return args, job_id


@router.post("/jobs", response_model=JobResponse, status_code=HTTPStatus.CREATED)
def job_create(payload: JobRequest, response: Response, request: Request) -> JobResponse:
    """
    Creates a new job.

    Notice that the job's ID is assigned to the test session, if it exists. Therefore, the
    relay runtime argument --session-id is not allowed as argument (or must be equivalent with
    the provided job ID).
    """
    if payload.id is not None and payload.id in jobs:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail=f"Job with ID {payload.id} already exists"
        )

    args, job_id = _parse_args(payload.args, payload.id)
    job: Job = jobs.create_job(args, id_=job_id, collect_only=payload.collect_only)
    response.headers["Location"] = str(request.url_for("job_get", id_=job.id))
    return job.to_model()


@router.get("/jobs/{id_}", response_model=JobResponse)
def job_get(id_: str) -> JobResponse:
    """
    Retrieves the job with the given ID.
    """
    job = _job_get(id_)
    return job.to_model()


@router.get("/jobs", response_model=List[JobResponse])
def jobs_get() -> List[JobResponse]:
    """
    Retrieves all jobs.
    """
    return [job.to_model() for job in jobs.jobs()]


@router.post("/jobs/{id_}/actions", response_model=JobResponse)
def job_action(id_: str, req: JobActionRequest) -> JobResponse:
    """
    Triggers an action for the given job.
    """
    job = _job_get(id_)

    match req.action:
        case JobAction.START:
            job.start()
        case JobAction.STOP:
            job.stop()
        case _:
            raise HTTPException(HTTPStatus.BAD_REQUEST, f"Unsupported action '{req.action}'")

    # return the new state so the client can see the effect
    return job.to_model()


@router.delete("/jobs/{id_}", status_code=HTTPStatus.NO_CONTENT)
def job_delete(id_: str) -> None:
    """
    Deletes the job with the given ID. Notice that this does not terminate a running job, it is
    just an endpoint that can be used to explicitly clean up old results.
    """
    job = _job_get(id_)
    del jobs[job.id]


@router.delete("/jobs", status_code=HTTPStatus.NO_CONTENT)
def jobs_delete() -> None:
    """
    Deletes all jobs.
    """
    jobs.clear()


# keep the 'app' definition at the end since all included routes must exist when defining the app
app = FastAPI(title="pytest-relay-run-api")
app.include_router(router)
