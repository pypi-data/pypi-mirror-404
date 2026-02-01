
# Job messages

All published messages follow this model:

```json
{
  "type": "job",
  "payload": {
    "id": "<job-id>",
    "state": "<job-state>",
    "returncode": "<int|null>",
    "text": "<process-output-as-str|null>"
  }
}
```

Each job transitions through a series of well-defined states, represented by the (`JobState`)[pytest_relay_run/src/pytest_relay_run/api/model.py]:

| Value           | Meaning                                                                       |
| --------------- | ----------------------------------------------------------------------------- |
| `"created"`     | The job was instantiated but has not yet started running pytest.              |
| `"collected"`   | Test collection was performed (using `--collect-only`), and no execution ran. |
| `"in-progress"` | The job’s pytest process is currently executing tests.                        |
| `"terminating"` | A termination signal (SIGINT) was sent, graceful shutdown is in progress.     |
| `"done"`        | The pytest process has completed (successfully or with errors).               |

The following transitions trigger a `JobState` message:

- **created** upon job creation (if not `collect_only`).
- **collected** as result for jobs with `--collect-only`.
- **in-progress** when a job subprocess starts executing.
- **done** after a job subprocess completes and output is captured.
- **terminating** when `stop()` is called and SIGINT is sent.

The states `collected` and `done` are final states, i.e., the job is complete.
