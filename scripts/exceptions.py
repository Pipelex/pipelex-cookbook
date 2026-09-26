from typing import Any


class CookbookError(Exception):
    """Base class of every error the cookbook's tooling raises."""


class CookbookLayoutError(CookbookError):
    """The repository does not hold what the tooling expects: a package, a manifest or `cookbook.toml` that does not load."""


class HostedApiError(CookbookError):
    """The hosted Pipelex API could not be reached, refused a call, or answered in a way the tooling cannot read.

    When it answered, `status_code` is the HTTP status, `problem` the problem details its body carried (`type`, `title`, `detail`,
    `error_type`), empty when the body was not one, and `retry_after_seconds` the wait its `Retry-After` header asked for, None when it named
    none.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        problem: dict[str, Any] | None = None,
        retry_after_seconds: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.problem: dict[str, Any] = problem or {}
        self.retry_after_seconds = retry_after_seconds


class HostedApiUnreachableError(HostedApiError):
    """No answer came from the hosted Pipelex API: the connection failed or timed out, so the call may or may not have reached the server."""


class HostedRunError(CookbookError):
    """A run on production ended without a result: `run_id` names it and `status` is the status it ended in, such as `FAILED`."""

    def __init__(self, message: str, *, run_id: str, status: str) -> None:
        super().__init__(message)
        self.run_id = run_id
        self.status = status


class HostedRunTimeoutError(HostedRunError):
    """A run on production was still going, or its results could not be read, when the wait ran out.

    It goes on on the server, and its results can be read later by its id.
    """


class SnapshotError(CookbookError):
    """An output snapshot was not written: the run was refused before it started, or its output cannot be committed as it is."""
