class CookbookError(Exception):
    """Base class of every error the cookbook's tooling raises."""


class CookbookLayoutError(CookbookError):
    """The repository does not hold what the tooling expects: a package, a manifest, an answer key or `cookbook.toml` that does not load."""


class HostedApiError(CookbookError):
    """The hosted Pipelex API could not be reached, or answered without a verdict."""
