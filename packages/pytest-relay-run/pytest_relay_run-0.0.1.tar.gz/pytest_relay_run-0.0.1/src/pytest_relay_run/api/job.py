"""
Module for managing jobs (test executions).
"""

import asyncio
import signal
import subprocess
import threading
import uuid
from collections.abc import MutableMapping
from threading import Lock
from typing import Dict, Iterator, List, Optional

from pytest_relay_ws.observer import AnyMessage

from pytest_relay_run.api.model import JobResponse, JobState
from pytest_relay_run.ws.app import publish

# asynchronous loop to prevent "async" propagation for simple synchronous actions
_async_loop: Optional[asyncio.AbstractEventLoop] = None


def inject_async_loop(loop: asyncio.AbstractEventLoop) -> None:
    """
    Provides the running loop as reference
    """
    global _async_loop  # pylint: disable=global-statement
    _async_loop = loop


class Job:
    """
    Job (test session execution) instance.
    """

    id: str
    args: List[str]
    state: JobState
    returncode: Optional[int] = None
    text: Optional[str] = None
    _process: Optional[subprocess.Popen] = None

    def __init__(
        self, args: List[str], id_: Optional[str] = None, collect_only: bool = False
    ) -> None:
        self.id = str(uuid.uuid4()) if id_ is None else id_
        self.args = args
        self.state = JobState.CREATED

        if collect_only:
            self._collect()
        else:
            self._publish_state()

    def _publish_state(self) -> None:
        if _async_loop is None:
            raise RuntimeError("Async event loop not available")

        msg = AnyMessage(
            type="job",
            payload=self.to_model().model_dump(),
        )
        # "await" bridge: schedule the coroutine on the main loop
        asyncio.run_coroutine_threadsafe(publish(msg.model_dump_json(), to_sink=True), _async_loop)

    def _collect(self) -> None:
        proc: subprocess.Popen[str] = subprocess.Popen(  # pylint: disable=consider-using-with
            ["pytest", "--session-id", self.id, "--collect-only"] + self.args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout
            text=True,
        )

        out, _err = proc.communicate()
        self.text = out
        self.returncode = proc.returncode
        self.state = JobState.COLLECTED
        self._publish_state()

    def start(self) -> None:
        """
        Starts a the pytest execution. The job is executed within a subprocess and monitored
        by a separate thread for completion.
        """
        if self.state not in (JobState.CREATED, JobState.COLLECTED):
            return

        self.state = JobState.IN_PROGRESS
        self._publish_state()

        self._process = subprocess.Popen(  # pylint: disable=consider-using-with
            ["pytest", "--session-id", self.id] + self.args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout
            text=True,
            encoding="utf-8",
        )

        # monitor the session's state in background
        thread: threading.Thread = threading.Thread(target=self._monitor, daemon=True)
        thread.start()

    def _monitor(self) -> None:
        assert self._process

        out, _err = self._process.communicate()
        self.text = out
        self.returncode = self._process.returncode
        self.state = JobState.DONE
        self._publish_state()

    def stop(self) -> None:
        """
        Stops the execution of the job's process by sending SIGINT ("graceful" termination,
        equivalent to a keyboard interrupt). If SIGINT doesn't do the trick, the process is killed
        after a timeout.
        """
        if not self._process or self._process.poll() is not None:
            return

        self.state = JobState.TERMINATING
        self._publish_state()

        self._process.send_signal(signal.SIGINT)
        try:
            self._process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self._process.kill()

    def to_model(self) -> JobResponse:
        """
        Creates a response model that is used by the API for job information.
        """
        return JobResponse(
            id=self.id,
            state=self.state,
            returncode=self.returncode,
            text=self.text,
        )


class JobManager(MutableMapping[str, Job]):
    """
    Helper class for managing job instances.
    """

    def __init__(self, max_sessions: int = 20) -> None:
        self._jobs: Dict[str, Job] = {}
        self._max_sessions: int = max_sessions
        self._lock = Lock()

    def __getitem__(self, key: str) -> Job:
        with self._lock:
            return self._jobs[key]

    def __setitem__(self, key: str, value: Job) -> None:
        with self._lock:
            if len(self._jobs) >= self._max_sessions and key not in self._jobs:
                # Evict oldest
                oldest = next(iter(self._jobs))
                del self._jobs[oldest]
            self._jobs[key] = value

    def __delitem__(self, key: str) -> None:
        with self._lock:
            del self._jobs[key]

    def __iter__(self) -> Iterator[str]:
        with self._lock:
            return iter(self._jobs.copy())  # safe iteration

    def __len__(self) -> int:
        with self._lock:
            return len(self._jobs)

    def create_job(
        self, args: List[str], id_: Optional[str] = None, collect_only: bool = False
    ) -> Job:
        """
        Creates a job for the given arguments and immediately starts its execution if
        `collect_only` isn't defined.
        """
        job = Job(id_=id_, args=args, collect_only=collect_only)
        self[job.id] = job
        if not collect_only:
            job.start()
        return job

    def jobs(self) -> List[Job]:
        """
        Returns a snapshot of all jobs.
        """
        with self._lock:
            return list(self._jobs.values())
