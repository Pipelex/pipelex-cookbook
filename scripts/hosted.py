"""Every call the cookbook's tooling makes to production, with `PIPELEX_API_KEY`: the checks and the refresh run by hand (`make check-hosted`,
`make refresh`), and the runs of the smoke check (`make check-smoke`).

A package is validated from its files (`make check-methods`), and so is each of the tutorial's bundles, alone; a page's address is validated at
the page's tag (`make check-addresses`). Validation is `POST /v1/validate`, and it spends no inference.

A run spends inference credit, so only a deliberate command starts one. `run_package` starts a run from a package's `.mthds` files and its
`inputs.json` (`POST /v1/start` with `mthds_contents`, the bundle's `main_pipe` naming the pipe), and `run_address` from an address (`method_ref`,
which the API fetches at its tag). Both first replace every raw URL into this repository that the inputs name, at `main` or a release tag, with
an upload of the file this checkout holds (`POST /v1/upload`), so that a sample not yet on `main` runs. Then they wait on
`GET /v1/runs/{id}/results`, which answers 202 or 503 with a `Retry-After` while the run goes on, 409 when it ended without a result and 200
with its output, reading again after a read that got no answer or a passing failure (429, 500, 502 or 504), since the run is paid for and goes
on on the server, and read when the run started and finished from `GET /v1/runs/{id}/status`. `HostedClient.resolve_storage_urls` turns the
`pipelex-storage://` references an output holds into fresh links (`POST /v1/resolve-storage-url/bulk`), and `download` fetches such a link
without the key.

The calls are made with `httpx`. The key is read from the environment and sent only as the `Authorization` header of a call to the API; nothing
here prints it.
"""

import base64
import mimetypes
import os
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from time import monotonic, sleep
from typing import Any, cast
from urllib.parse import quote, urlsplit, urlunsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError

from scripts.contract import Contract, project_contract
from scripts.cookbook import Cookbook, MethodPackage
from scripts.exceptions import CookbookLayoutError, HostedApiError, HostedApiUnreachableError, HostedRunError, HostedRunTimeoutError

API_KEY_ENV = "PIPELEX_API_KEY"
BASE_URL_ENV = "PIPELEX_BASE_URL"
DEFAULT_BASE_URL = "https://api.pipelex.com"
USER_AGENT = "pipelex-cookbook-tooling"
VALIDATE_TIMEOUT_SECONDS = 300.0
# A first start at a tag waits while the API fetches the repository, so the start's request may take as long as a run.
START_TIMEOUT_SECONDS = 1200.0
UPLOAD_TIMEOUT_SECONDS = 300.0
# One read of a run's results or status, or one request resolving storage references: the hosted gateway answers within thirty seconds.
READ_TIMEOUT_SECONDS = 60.0
DOWNLOAD_TIMEOUT_SECONDS = 120.0
# How long a run is waited for once started. The wait giving up does not stop the run, which goes on on the server.
RUN_TIMEOUT_SECONDS = 1200.0
# The shortest wait between two reads of a run's results, whatever its `Retry-After` says.
POLL_INTERVAL_SECONDS = 5.0
# The most references `POST /v1/resolve-storage-url/bulk` takes in one request; a longer list is refused, so it is sent in batches.
RESOLVE_BATCH_SIZE = 100
STORAGE_SCHEME = "pipelex-storage://"
_DEFAULT_CONTENT_TYPE = "application/octet-stream"
_BODY_EXCERPT_LENGTH = 2000
# A 409 from the results route says how the run ended in its detail, such as "Run finished with status FAILED; …".
_ENDED_STATUS_PATTERN = re.compile(r"status\s+([A-Z_]+)")
_FAILED_STATUS = "FAILED"
_COMPLETED_STATUS = "COMPLETED"
_RUNNING_STATUS = "RUNNING"
# The answers to a start that do not say whether a run was created: the gateway gave up waiting on the server, or the server failed on its way,
# and either may come after the server created the run.
_UNSETTLED_START_STATUS_CODES = frozenset({502, 503, 504})
# The answers to a read of a run's results that say nothing of the run, only that the server or the gateway failed for a moment or asked the
# caller to slow down. The run goes on on the server whatever one read says, so the read is made again while the wait has time left.
_TRANSIENT_READ_STATUS_CODES = frozenset({429, 500, 502, 504})


class MethodVerdict(BaseModel):
    """What production said of one package's files."""

    model_config = ConfigDict(frozen=True)

    name: str
    is_valid: bool
    report: str
    contract: Contract | None


class BundleVerdict(BaseModel):
    """What production said of one bundle validated alone from its file, such as a tutorial lesson."""

    model_config = ConfigDict(frozen=True)

    source: str
    is_valid: bool
    report: str


class RunRoute(StrEnum):
    """How a run named its method: by the package's files, or by its address."""

    FILES = "files"
    ADDRESS = "address"


class HostedRun(BaseModel):
    """A run on production that completed, with its output and what it cost."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    base_url: str = Field(description="The API the run was started on, such as `https://api.pipelex.com`")
    route: RunRoute
    method_ref: str | None = Field(description="The address the run was started from, or None for a run from the package's files")
    commit_sha: str | None = Field(description="The commit the address resolved to, or None for a run from the package's files")
    started_at: datetime = Field(description="When the run was created, in UTC")
    finished_at: datetime = Field(description="When the run finished, in UTC")
    main_stuff: JsonValue = Field(description="The run's main output, as the results route relays it")
    tokens_usages: list[dict[str, JsonValue]] | None = Field(
        description="One record per inference call, each with its `cost` in US dollars, or None when the run relayed no records"
    )

    @property
    def cost_usd(self) -> float | None:
        """What the run cost, in US dollars: the sum of its priced usage records, or None when it relayed no records.

        A record whose model has no rate table carries no cost and adds nothing, so the sum is what the priced calls cost.
        """
        if self.tokens_usages is None:
            return None
        total = 0.0
        for record in self.tokens_usages:
            cost = record.get("cost")
            if isinstance(cost, int | float) and not isinstance(cost, bool):
                total += cost
        return total

    @property
    def duration_seconds(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()

    def summary(self) -> str:
        """The run's id, cost and duration, in the words every command prints them in."""
        cost = self.cost_usd
        cost_text = "cost unknown, since the run relayed no usage records" if cost is None else f"${cost:.4f}"
        return f"run {self.run_id}, {cost_text}, {self.duration_seconds:.0f} s"


class StorageUrlError(BaseModel):
    """Why the API resolved no link for a storage reference: `code` is `invalid_storage_uri` or `forbidden`, and `detail` says it in a sentence."""

    model_config = ConfigDict(frozen=True)

    code: str
    detail: str


class ResolvedStorageUrl(BaseModel):
    """The API's verdict on one `pipelex-storage://` reference: a fresh link, or why there is none.

    Either `url`, `expires_at` and `content_type` are set and `error` is None, or `error` is set and the link's fields are None. A link is
    presigned and expires about fifteen minutes after it is resolved.
    """

    model_config = ConfigDict(frozen=True)

    uri: str = Field(description="The reference, exactly as it was sent")
    url: str | None = None
    expires_at: str | None = None
    content_type: str | None = None
    error: StorageUrlError | None = None


class RunStart(BaseModel):
    """What the API acknowledged when it started a run."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    commit_sha: str | None = Field(description="The commit an address resolved to, for a run started from an address")


class ResultsPending(BaseModel):
    """The run is going on, or its results cannot be read yet: ask again after `retry_after_seconds`, when the API named a wait."""

    model_config = ConfigDict(frozen=True)

    retry_after_seconds: int | None


class ResultsReady(BaseModel):
    """The run completed, and its results carry its output."""

    model_config = ConfigDict(frozen=True)

    main_stuff: JsonValue
    tokens_usages: list[dict[str, JsonValue]] | None


class ResultsFailed(BaseModel):
    """The run ended without a result: `status` is how it ended, such as `FAILED`, and `message` what the API said of it."""

    model_config = ConfigDict(frozen=True)

    status: str
    message: str


class HostedClient:
    """A client for the routes of production the cookbook's tooling calls.

    Each call opens its own connection. Pass `transport` to answer the calls without a network, as the tests do.
    """

    def __init__(self, *, api_key: str, base_url: str, transport: httpx.BaseTransport | None = None) -> None:
        self._headers = {"Authorization": f"Bearer {api_key}", "User-Agent": USER_AGENT}
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    @property
    def base_url(self) -> str:
        return self._base_url

    def validate_files(self, *, contents: list[str], sources: list[str]) -> dict[str, Any]:
        """Validate bundles from their contents, asking for the input form so the contract can name each input's kind."""
        body = {"mthds_contents": contents, "mthds_sources": sources, "views": ["input_form"], "render": ["markdown"]}
        return self._post_validate(body)

    def validate_address(self, *, method_ref: str) -> dict[str, Any]:
        """Validate a published method by its address, which the server fetches at its tag."""
        return self._post_validate({"method_ref": method_ref, "render": ["markdown"]})

    def start_files(self, *, mthds_contents: list[str], inputs: Mapping[str, JsonValue]) -> RunStart:
        """Start a run from bundles' contents, whose `main_pipe` names the pipe. The run spends inference credit.

        Raises:
            HostedApiError: The API refused the start, could not be reached, or acknowledged no run id.
        """
        return self._start({"mthds_contents": mthds_contents, "inputs": dict(inputs)})

    def start_address(self, *, method_ref: str, inputs: Mapping[str, JsonValue]) -> RunStart:
        """Start a run of a published method by its address, whose manifest's `main_pipe` names the pipe. The run spends inference credit.

        Raises:
            HostedApiError: The API refused the start, could not be reached, or acknowledged no run id.
        """
        return self._start({"method_ref": method_ref, "inputs": dict(inputs)})

    def upload(self, *, path: Path) -> str:
        """Upload a local file into the caller's storage and return its `pipelex-storage://` reference, which an input names as its `url`.

        Raises:
            HostedApiError: The API refused the file, or could not be reached.
        """
        content_type = mimetypes.guess_type(path.name)[0] or _DEFAULT_CONTENT_TYPE
        body = {"filename": path.name, "data": base64.b64encode(path.read_bytes()).decode("ascii"), "content_type": content_type}
        url, response = self._send("POST", "/v1/upload", body=body, timeout=UPLOAD_TIMEOUT_SECONDS)
        if not response.is_success:
            raise _refusal(url=url, response=response)
        uri = _json_object(url=url, response=response).get("uri")
        if not isinstance(uri, str) or not uri.startswith(STORAGE_SCHEME):
            msg = f"{url} answered HTTP {response.status_code} without a {STORAGE_SCHEME} reference for {path.name}: {_excerpt(response)}"
            raise HostedApiError(msg)
        return uri

    def read_results(self, *, run_id: str) -> ResultsPending | ResultsReady | ResultsFailed:
        """Read a run's results once: pending while it goes on, ready with its output once it completed, failed when it ended without one.

        Raises:
            HostedApiError: The API refused the read, such as for a run it does not know, or could not be reached.
        """
        url, response = self._send("GET", f"/v1/runs/{quote(run_id, safe='')}/results", timeout=READ_TIMEOUT_SECONDS)
        match response.status_code:
            case 202 | 503:
                # 202 while the run goes on; 503 while the run store is degraded, which is a reason to ask again, never to give up.
                return ResultsPending(retry_after_seconds=_retry_after(response))
            case 409:
                message = str(_problem_details(response).get("detail") or _excerpt(response) or "the run ended without a result")
                ended = _ENDED_STATUS_PATTERN.search(message)
                return ResultsFailed(status=ended.group(1) if ended else _FAILED_STATUS, message=message)
            case 200:
                body = _json_object(url=url, response=response)
                main_stuff = body.get("main_stuff")
                if main_stuff is None:
                    return ResultsFailed(status=_COMPLETED_STATUS, message=f"{url} answered 200, but the results carry no output")
                usages = body.get("tokens_usages")
                records = (
                    [cast("dict[str, JsonValue]", record) for record in cast("list[Any]", usages) if isinstance(record, dict)]
                    if isinstance(usages, list)
                    else None
                )
                return ResultsReady(main_stuff=main_stuff, tokens_usages=records)
            case _:
                raise _refusal(url=url, response=response)

    def read_status(self, *, run_id: str) -> dict[str, Any]:
        """Read a run's status record, which carries its `status`, `created_at` and `finished_at`.

        Raises:
            HostedApiError: The API refused the read, or could not be reached.
        """
        url, response = self._send("GET", f"/v1/runs/{quote(run_id, safe='')}/status", timeout=READ_TIMEOUT_SECONDS)
        if response.status_code != 200:
            raise _refusal(url=url, response=response)
        return _json_object(url=url, response=response)

    def resolve_storage_urls(self, *, uris: list[str]) -> list[ResolvedStorageUrl]:
        """Resolve `pipelex-storage://` references into fresh links, one verdict per reference, in the order given.

        A reference the API refuses, being malformed or another organization's, is a verdict carrying `error` rather than an exception, and the
        caller decides what it means. A link expires about fifteen minutes after it is resolved, so references are resolved right before their
        files are fetched. An answer holding links is never repeated in an error, since each link carries its signature: an error names the
        references instead.

        Raises:
            HostedApiError: A request failed as a whole, or its answer does not hold one verdict per reference, in order.
        """
        resolved: list[ResolvedStorageUrl] = []
        for offset in range(0, len(uris), RESOLVE_BATCH_SIZE):
            batch = uris[offset : offset + RESOLVE_BATCH_SIZE]
            url, response = self._send("POST", "/v1/resolve-storage-url/bulk", body={"uris": batch}, timeout=READ_TIMEOUT_SECONDS)
            if response.status_code != 200:
                raise _refusal(url=url, response=response)
            items = _json_object(url=url, response=response).get("items")
            try:
                verdicts = [ResolvedStorageUrl.model_validate(item) for item in cast("list[Any]", items)] if isinstance(items, list) else []
            except ValidationError as exc:
                # The validation's own message quotes the item, link included, so only where and why it failed are named.
                problems = "; ".join(f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors(include_input=False))
                msg = f"{url} answered with an item that is not a verdict on a reference: {problems}"
                raise HostedApiError(msg) from None
            answered = [verdict.uri for verdict in verdicts]
            if answered != batch:
                msg = (
                    f"{url} did not answer one verdict per reference, in the order they were sent: "
                    f"it was sent {', '.join(batch)} and answered on {', '.join(answered) or 'none'}"
                )
                raise HostedApiError(msg)
            resolved.extend(verdicts)
        return resolved

    def _start(self, body: Mapping[str, Any]) -> RunStart:
        """Send a start and read the run id it acknowledges.

        Once the request is sent, only a refusal from the API itself proves that no run began. An error for a request that got no answer, for a
        gateway's failure (502, 503 or 504), or for a success whose body carries no run id says that the run may exist all the same.

        Raises:
            HostedApiError: The API refused the start, could not be reached, or acknowledged no run id.
        """
        try:
            url, response = self._send("POST", "/v1/start", body=body, timeout=START_TIMEOUT_SECONDS)
        except HostedApiError as exc:
            raise _may_have_started(exc) from exc
        if response.status_code in _UNSETTLED_START_STATUS_CODES:
            raise _may_have_started(_refusal(url=url, response=response))
        if not response.is_success:
            raise _refusal(url=url, response=response)
        try:
            ack = _json_object(url=url, response=response)
        except HostedApiError as exc:
            raise _may_have_started(exc) from exc
        run_id = ack.get("pipeline_run_id")
        if not isinstance(run_id, str) or not run_id:
            msg = f"{url} answered HTTP {response.status_code} without a run id: {_excerpt(response)}"
            raise _may_have_started(HostedApiError(msg))
        provenance = ack.get("method_provenance")
        commit_sha = cast("dict[str, Any]", provenance).get("commit_sha") if isinstance(provenance, dict) else None
        return RunStart(run_id=run_id, commit_sha=commit_sha if isinstance(commit_sha, str) else None)

    def _post_validate(self, body: Mapping[str, Any]) -> dict[str, Any]:
        url, response = self._send("POST", "/v1/validate", body=body, timeout=VALIDATE_TIMEOUT_SECONDS)
        if response.status_code != 200:
            # A non-2xx carries no verdict: the request, the key or the server failed. The body names why; the key is never part of it.
            msg = f"{url} answered HTTP {response.status_code} without a verdict: {_excerpt(response)}"
            raise HostedApiError(msg, status_code=response.status_code, problem=_problem_details(response))
        verdict = _json_object(url=url, response=response)
        if "is_valid" not in verdict:
            msg = f"{url} answered 200 without a verdict"
            raise HostedApiError(msg)
        return verdict

    def _send(self, method: str, path: str, *, body: Mapping[str, Any] | None = None, timeout: float) -> tuple[str, httpx.Response]:
        """Make one call to the API and return its URL, for the errors to name, with its answer, whatever its status.

        Raises:
            HostedApiUnreachableError: No answer came.
        """
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(transport=self._transport, timeout=timeout) as http:
                return url, http.request(method, url, json=dict(body) if body is not None else None, headers=self._headers)
        except httpx.TransportError as exc:
            msg = f"{url} could not be reached: {exc}"
            raise HostedApiUnreachableError(msg) from exc


def client_from_env() -> HostedClient:
    """Build the client from `PIPELEX_API_KEY` and, when set, `PIPELEX_BASE_URL`.

    Raises:
        HostedApiError: No key is set.
    """
    api_key = os.environ.get(API_KEY_ENV, "")
    if not api_key:
        msg = f"{API_KEY_ENV} is not set: the hosted checks call production, so they need a key (create one at https://app.pipelex.com)"
        raise HostedApiError(msg)
    return HostedClient(api_key=api_key, base_url=os.environ.get(BASE_URL_ENV) or DEFAULT_BASE_URL)


def validate_package(*, client: HostedClient, package: MethodPackage) -> MethodVerdict:
    """Validate a package's bundles on production from its files, and project its main pipe's contract when they are valid."""
    bundle_paths = package.bundle_paths()
    contents = [bundle_path.read_text(encoding="utf-8") for bundle_path in bundle_paths]
    sources = [f"{package.name}/{bundle_path.name}" for bundle_path in bundle_paths]
    verdict = client.validate_files(contents=contents, sources=sources)
    report = str(verdict.get("rendered_markdown") or verdict.get("message") or "")
    if verdict.get("is_valid") is not True:
        return MethodVerdict(name=package.name, is_valid=False, report=report, contract=None)
    main_pipe = package.manifest.main_pipe or ""
    return MethodVerdict(name=package.name, is_valid=True, report=report, contract=project_contract(verdict=verdict, main_pipe=main_pipe))


def validate_bundle_file(*, client: HostedClient, path: Path, root: Path) -> BundleVerdict:
    """Validate one self-contained bundle on production from its file, naming it by its path from the repository root."""
    source = path.relative_to(root).as_posix()
    verdict = client.validate_files(contents=[path.read_text(encoding="utf-8")], sources=[source])
    report = str(verdict.get("rendered_markdown") or verdict.get("message") or "")
    return BundleVerdict(source=source, is_valid=verdict.get("is_valid") is True, report=report)


def validate_packages(*, cookbook: Cookbook, client: HostedClient) -> list[MethodVerdict]:
    return [validate_package(client=client, package=package) for package in cookbook.packages]


class AddressState(StrEnum):
    VALID = "valid"
    UNRELEASED = "unreleased"
    FAILED = "failed"


class AddressVerdict(BaseModel):
    """What production said of the address a page names."""

    model_config = ConfigDict(frozen=True)

    name: str
    address: str
    state: AddressState
    report: str


# What production answers for an address that is not published yet: a tag that carries no package at the address (404, the package is not
# found), or a tag that does not exist yet (422, a fetch error whose detail says the tag names no git tag). Anything else is a failure.
_PACKAGE_NOT_FOUND_TYPE = "method-package-not-found-error"
_FETCH_ERROR_TYPE = "MethodFetchError"
_NO_SUCH_TAG_DETAIL = "does not name a git tag"


def check_address(*, client: HostedClient, cookbook: Cookbook, package: MethodPackage) -> AddressVerdict:
    """Validate the address a package's page names, at the page's tag.

    A method the tag does not carry yet, or a tag not pushed yet, is reported as unreleased rather than as a failure: a method added since the
    last release has a page naming a tag it is not in, and the release that carries it is what the check after the release proves.
    """
    return check_method_ref(client=client, name=package.name, address=cookbook.address_of(package))


def check_method_ref(*, client: HostedClient, name: str, address: str) -> AddressVerdict:
    """Validate one address on production, naming the page or the recipe it comes from as `name`, and read an unpublished one as unreleased."""
    try:
        verdict = client.validate_address(method_ref=address)
    except HostedApiError as exc:
        if _is_unreleased(exc):
            detail = str(exc.problem.get("detail") or exc)
            return AddressVerdict(name=name, address=address, state=AddressState.UNRELEASED, report=detail)
        return AddressVerdict(name=name, address=address, state=AddressState.FAILED, report=str(exc))
    report = str(verdict.get("rendered_markdown") or verdict.get("message") or "")
    state = AddressState.VALID if verdict.get("is_valid") is True else AddressState.FAILED
    return AddressVerdict(name=name, address=address, state=state, report=report)


def check_pinned_method_ref(*, client: HostedClient, name: str, address: str) -> AddressVerdict:
    """Validate an address a recipe calls, which must resolve today: its types were generated from it, so unreleased is a failure."""
    verdict = check_method_ref(client=client, name=name, address=address)
    match verdict.state:
        case AddressState.UNRELEASED:
            return verdict.model_copy(update={"state": AddressState.FAILED})
        case AddressState.VALID | AddressState.FAILED:
            return verdict


def _is_unreleased(error: HostedApiError) -> bool:
    problem_type = str(error.problem.get("type") or "")
    if error.status_code == 404 and _PACKAGE_NOT_FOUND_TYPE in problem_type:
        return True
    detail = str(error.problem.get("detail") or "")
    return error.status_code == 422 and error.problem.get("error_type") == _FETCH_ERROR_TYPE and _NO_SUCH_TAG_DETAIL in detail


def run_package(*, client: HostedClient, cookbook: Cookbook, package: MethodPackage, timeout_seconds: float = RUN_TIMEOUT_SECONDS) -> HostedRun:
    """Run a package once on production from its files, on its sample, and wait for its output. The run spends inference credit.

    The package's `.mthds` files are sent as this checkout holds them, and the bundle's `main_pipe` names the pipe, so the run proves the
    method on the branch, which the address its page names, at the last release's tag, may not hold yet.

    Raises:
        CookbookLayoutError: The sample names a file of this repository that this checkout does not hold.
        HostedApiError: A call was refused or got no answer.
        HostedRunError: The run ended without a result, or, as `HostedRunTimeoutError`, was still going, or could not be read, when
            `timeout_seconds` ran out.
    """
    inputs = upload_local_samples(client=client, cookbook=cookbook, inputs=package.inputs)
    contents = [bundle_path.read_text(encoding="utf-8") for bundle_path in package.bundle_paths()]
    started_at = datetime.now(UTC)
    start = client.start_files(mthds_contents=contents, inputs=inputs)
    return _wait_for_run(client=client, start=start, route=RunRoute.FILES, method_ref=None, started_at=started_at, timeout_seconds=timeout_seconds)


def run_address(
    *,
    client: HostedClient,
    cookbook: Cookbook,
    address: str,
    inputs: Mapping[str, JsonValue],
    timeout_seconds: float = RUN_TIMEOUT_SECONDS,
) -> HostedRun:
    """Run a published method once on production by its address, which the API fetches at its tag, and wait for its output.

    The run spends inference credit. The inputs' raw URLs into this repository are uploaded from this checkout, as for `run_package`.

    Raises:
        CookbookLayoutError: The inputs name a file of this repository that this checkout does not hold.
        HostedApiError: A call was refused or got no answer, such as a start at an address that does not resolve.
        HostedRunError: The run ended without a result, or, as `HostedRunTimeoutError`, was still going, or could not be read, when
            `timeout_seconds` ran out.
    """
    prepared = upload_local_samples(client=client, cookbook=cookbook, inputs=inputs)
    started_at = datetime.now(UTC)
    start = client.start_address(method_ref=address, inputs=prepared)
    return _wait_for_run(
        client=client, start=start, route=RunRoute.ADDRESS, method_ref=address, started_at=started_at, timeout_seconds=timeout_seconds
    )


def upload_local_samples(*, client: HostedClient, cookbook: Cookbook, inputs: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    """A copy of `inputs` in which every `url` naming a raw URL into this repository names an upload of this checkout's file instead.

    The URL may name `main` or a release tag: either way the file is taken from this checkout, so that a sample not yet on `main` runs.

    Each file is uploaded once, however many inputs name it. Every other value is kept as it is, a URL hosted elsewhere included.

    Raises:
        CookbookLayoutError: A URL into this repository names a file this checkout does not hold.
        HostedApiError: An upload failed.
    """
    uploaded: dict[Path, str] = {}
    return {name: _with_uploads(value, client=client, cookbook=cookbook, uploaded=uploaded) for name, value in inputs.items()}


def _with_uploads(value: JsonValue, *, client: HostedClient, cookbook: Cookbook, uploaded: dict[Path, str]) -> JsonValue:
    if isinstance(value, list):
        return [_with_uploads(item, client=client, cookbook=cookbook, uploaded=uploaded) for item in value]
    if not isinstance(value, dict):
        return value
    replaced: dict[str, JsonValue] = {}
    for key, item in value.items():
        local_path = _local_sample(cookbook=cookbook, url=item) if key == "url" and isinstance(item, str) else None
        if local_path is None:
            replaced[key] = _with_uploads(item, client=client, cookbook=cookbook, uploaded=uploaded)
            continue
        if local_path not in uploaded:
            uploaded[local_path] = client.upload(path=local_path)
        replaced[key] = uploaded[local_path]
    return replaced


def _local_sample(*, cookbook: Cookbook, url: str) -> Path | None:
    """The file of this checkout a raw URL into this repository names, at `main` or a release tag, or None for a URL hosted elsewhere.

    Raises:
        CookbookLayoutError: The URL points into this repository, but names no file this checkout holds.
    """
    try:
        local_file = cookbook.local_file_of(url)
    except CookbookLayoutError as exc:
        msg = f"the sample {url} points into this repository, but {exc}"
        raise CookbookLayoutError(msg) from exc
    return local_file.path if local_file is not None else None


def _wait_for_run(
    *,
    client: HostedClient,
    start: RunStart,
    route: RunRoute,
    method_ref: str | None,
    started_at: datetime,
    timeout_seconds: float,
) -> HostedRun:
    results = _await_results(client=client, run_id=start.run_id, timeout_seconds=timeout_seconds)
    finished_at = datetime.now(UTC)
    # The status records when the run was created and when it finished. When it cannot be read, the times this process saw stand in, since the
    # output has been paid for and is in hand.
    try:
        status = client.read_status(run_id=start.run_id)
    except HostedApiError:
        status = {}
    return HostedRun(
        run_id=start.run_id,
        base_url=client.base_url,
        route=route,
        method_ref=method_ref,
        commit_sha=start.commit_sha,
        started_at=_timestamp(status.get("created_at")) or started_at,
        finished_at=_timestamp(status.get("finished_at")) or finished_at,
        main_stuff=results.main_stuff,
        tokens_usages=results.tokens_usages,
    )


def _await_results(*, client: HostedClient, run_id: str, timeout_seconds: float) -> ResultsReady:
    """Read a run's results until it ends, waiting between two reads what the API's `Retry-After` asks, and never less than the poll interval.

    A read that got no answer, or whose answer says only that the server or the gateway failed for a moment (429, 500, 502 or 504), is made
    again after the same wait while time remains, since the run is paid for and goes on on the server whatever one read says. Every error but
    the run's own end names the run and says how to read its output later.

    Raises:
        HostedRunError: The run ended without a result.
        HostedRunTimeoutError: The run was still going, or its results could not be read, when `timeout_seconds` ran out.
        HostedApiError: A read was refused otherwise, such as for a run the API does not know.
    """
    deadline = monotonic() + timeout_seconds
    while True:
        unread: HostedApiError | None = None
        try:
            state = client.read_results(run_id=run_id)
        except HostedApiError as exc:
            if not _is_transient(exc):
                msg = f"run {run_id} started, but a read of its results failed: {exc}. {_goes_on(run_id)}"
                raise HostedApiError(msg, status_code=exc.status_code, problem=exc.problem) from exc
            unread = exc
            retry_after = exc.retry_after_seconds
        else:
            match state:
                case ResultsReady():
                    return state
                case ResultsFailed():
                    msg = f"run {run_id} ended {state.status} without a result: {state.message}"
                    raise HostedRunError(msg, run_id=run_id, status=state.status)
                case ResultsPending():
                    retry_after = state.retry_after_seconds
        remaining = deadline - monotonic()
        if remaining <= 0:
            if unread is None:
                msg = f"run {run_id} was still going after {timeout_seconds:.0f} s. {_goes_on(run_id)}"
            else:
                msg = f"run {run_id} had no readable result after {timeout_seconds:.0f} s, its last read failing: {unread}. {_goes_on(run_id)}"
            raise HostedRunTimeoutError(msg, run_id=run_id, status=_RUNNING_STATUS)
        sleep(min(max(POLL_INTERVAL_SECONDS, retry_after or 0), remaining))


def _is_transient(error: HostedApiError) -> bool:
    """Whether a failed read of a run's results says nothing of the run: no answer came, or the server or the gateway failed for a moment."""
    return isinstance(error, HostedApiUnreachableError) or error.status_code in _TRANSIENT_READ_STATUS_CODES


def _goes_on(run_id: str) -> str:
    """What an error raised once a run started says of it: that it goes on on the server, and how to read its output later by its id."""
    return f"It goes on on the server, and GET /v1/runs/{run_id}/results reads its output once it ends"


def download(url: str, *, max_bytes: int, transport: httpx.BaseTransport | None = None) -> bytes:
    """Fetch a resolved storage link, which carries its own signature, and return its body.

    No key is sent and no redirect is followed, and a body over `max_bytes` is refused. An error names the link without its query, which holds
    the signature.

    Raises:
        HostedApiError: The link is not HTTPS, could not be fetched, answered anything but 200, or holds more than `max_bytes`.
    """
    shown = _without_query(url)
    try:
        scheme = urlsplit(url).scheme
    except ValueError:
        # A link too malformed to split, such as one with an unclosed bracket in its host, is no HTTPS link either.
        scheme = ""
    if scheme != "https":
        msg = f"{shown} is not an HTTPS link, and a resolved storage link always is"
        raise HostedApiError(msg)
    try:
        with (
            httpx.Client(transport=transport, timeout=DOWNLOAD_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}) as http,
            http.stream("GET", url) as response,
        ):
            if response.status_code != 200:
                msg = f"{shown} answered HTTP {response.status_code}"
                raise HostedApiError(msg, status_code=response.status_code)
            declared = response.headers.get("content-length")
            if declared is not None and declared.isdigit() and int(declared) > max_bytes:
                msg = f"{shown} holds {declared} bytes, more than the {max_bytes} allowed"
                raise HostedApiError(msg)
            body = bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body) > max_bytes:
                    msg = f"{shown} holds more than the {max_bytes} bytes allowed"
                    raise HostedApiError(msg)
            return bytes(body)
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        msg = f"{shown} could not be fetched: {exc}"
        raise HostedApiError(msg) from exc


def _refusal(*, url: str, response: httpx.Response) -> HostedApiError:
    msg = f"{url} answered HTTP {response.status_code}: {_excerpt(response)}"
    return HostedApiError(msg, status_code=response.status_code, problem=_problem_details(response), retry_after_seconds=_retry_after(response))


def _may_have_started(error: HostedApiError) -> HostedApiError:
    """The error of a start whose request was sent but whose answer names no run, warning that the run may exist and spend credit all the same."""
    msg = f"{error}. The API may have started the run all the same: look for it in the console before starting another"
    return HostedApiError(msg, status_code=error.status_code, problem=error.problem, retry_after_seconds=error.retry_after_seconds)


def _json_object(*, url: str, response: httpx.Response) -> dict[str, Any]:
    """The answer's body, which must be a JSON object.

    Raises:
        HostedApiError: The body is not a JSON object.
    """
    try:
        body: object = response.json()
    except ValueError as exc:
        msg = f"{url} answered HTTP {response.status_code} with a body that is not JSON: {_excerpt(response)}"
        raise HostedApiError(msg) from exc
    if not isinstance(body, dict):
        msg = f"{url} answered HTTP {response.status_code} with a body that is not a JSON object: {_excerpt(response)}"
        raise HostedApiError(msg)
    return cast("dict[str, Any]", body)


def _problem_details(response: httpx.Response) -> dict[str, Any]:
    """The problem details (RFC 9457) a refusal carries, or nothing when its body is not a JSON object."""
    try:
        body: object = response.json()
    except ValueError:
        return {}
    return cast("dict[str, Any]", body) if isinstance(body, dict) else {}


def _excerpt(response: httpx.Response) -> str:
    return response.text[:_BODY_EXCERPT_LENGTH]


def _retry_after(response: httpx.Response) -> int | None:
    """The seconds a `Retry-After` header asks to wait, in the integer form the API uses, or None."""
    raw = response.headers.get("retry-after", "").strip()
    return int(raw) if raw.isdigit() else None


def _timestamp(value: object) -> datetime | None:
    """An ISO 8601 timestamp as a UTC datetime, reading one without an offset as UTC, or None when the value is not a timestamp."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC)


def _without_query(url: str) -> str:
    try:
        parts = urlsplit(url)
    except ValueError:
        return "a storage link"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
