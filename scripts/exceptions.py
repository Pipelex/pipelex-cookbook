from typing import Any


class CookbookError(Exception):
    """Base class of every error the cookbook's tooling raises."""


class CookbookLayoutError(CookbookError):
    """The repository does not hold what the tooling expects: a package, a manifest, an answer key or `cookbook.toml` that does not load."""


class HostedApiError(CookbookError):
    """The hosted Pipelex API could not be reached, or answered without a verdict.

    When it answered, `status_code` is the HTTP status and `problem` the problem details its body carried (`type`, `title`, `detail`,
    `error_type`), empty when the body was not one.
    """

    def __init__(self, message: str, *, status_code: int | None = None, problem: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.problem: dict[str, Any] = problem or {}
