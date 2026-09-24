"""The checks and the refresh that call production, which need `PIPELEX_API_KEY` and are run by hand (`make check-hosted`, `make refresh`).

Only `POST /v1/validate` is called, and no call spends inference. The call is made with `httpx` rather than through `pipelex-sdk`: the SDK pins an
`mthds` release that the runtime this repository still pins for its older examples cannot run with, so the two cannot share an environment until
that pin goes. The key is read from the environment and sent only as the `Authorization` header; nothing here prints it.
"""

import os
from collections.abc import Mapping
from typing import Any, cast

import httpx
from pydantic import BaseModel, ConfigDict

from scripts.contract import Contract, project_contract
from scripts.cookbook import Cookbook, MethodPackage
from scripts.exceptions import HostedApiError

API_KEY_ENV = "PIPELEX_API_KEY"
BASE_URL_ENV = "PIPELEX_BASE_URL"
DEFAULT_BASE_URL = "https://api.pipelex.com"
VALIDATE_TIMEOUT_SECONDS = 300.0


class MethodVerdict(BaseModel):
    """What production said of one package's files."""

    model_config = ConfigDict(frozen=True)

    name: str
    is_valid: bool
    report: str
    contract: Contract | None


class HostedClient:
    """A client for the one hosted route the cookbook's checks call."""

    def __init__(self, *, api_key: str, base_url: str) -> None:
        self._headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "pipelex-cookbook-tooling"}
        self._base_url = base_url.rstrip("/")

    def validate_files(self, *, contents: list[str], sources: list[str]) -> dict[str, Any]:
        """Validate bundles from their contents, asking for the input form so the contract can name each input's kind."""
        body = {"mthds_contents": contents, "mthds_sources": sources, "views": ["input_form"], "render": ["markdown"]}
        return self._post_validate(body)

    def validate_address(self, *, method_ref: str) -> dict[str, Any]:
        """Validate a published method by its address, which the server fetches at its tag."""
        return self._post_validate({"method_ref": method_ref, "render": ["markdown"]})

    def _post_validate(self, body: Mapping[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}/v1/validate"
        try:
            response = httpx.post(url, json=dict(body), headers=self._headers, timeout=VALIDATE_TIMEOUT_SECONDS)
        except httpx.TransportError as exc:
            msg = f"{url} could not be reached: {exc}"
            raise HostedApiError(msg) from exc
        if response.status_code != 200:
            # A non-2xx carries no verdict: the request, the key or the server failed. The body names why; the key is never part of it.
            msg = f"{url} answered HTTP {response.status_code} without a verdict: {response.text[:2000]}"
            raise HostedApiError(msg)
        verdict: object = response.json()
        if not isinstance(verdict, dict) or "is_valid" not in verdict:
            msg = f"{url} answered 200 without a verdict"
            raise HostedApiError(msg)
        return cast("dict[str, Any]", verdict)


def client_from_env() -> HostedClient:
    """Build the client from `PIPELEX_API_KEY` and, when set, `PIPELEX_BASE_URL`.

    Raises:
        HostedApiError: No key is set.
    """
    api_key = os.environ.get(API_KEY_ENV, "")
    if not api_key:
        msg = f"{API_KEY_ENV} is not set: the hosted checks validate on production, so they need a key (create one at https://app.pipelex.com)"
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


def validate_packages(*, cookbook: Cookbook, client: HostedClient) -> list[MethodVerdict]:
    return [validate_package(client=client, package=package) for package in cookbook.packages]
