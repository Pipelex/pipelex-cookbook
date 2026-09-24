"""The checks that need no API key, run on every pull request: the pages are fresh, the manifests are in lockstep, and every sample link answers."""

import re
from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote

import httpx
from pydantic import BaseModel, ConfigDict, JsonValue

from scripts.cookbook import INPUTS_FILE, Cookbook
from scripts.render import RAW_BASE_URL

_RAW_URL_PATTERN = re.compile(r"https://raw\.githubusercontent\.com/[^\s)\"'`<>]+")


class LinkVerdict(BaseModel):
    """What the link check found for one raw URL."""

    model_config = ConfigDict(frozen=True)

    url: str
    found_in: list[str]
    ok: bool
    note: str


def stale_pages(*, cookbook: Cookbook, rendered: dict[Path, str]) -> list[Path]:
    """The pages whose committed contents differ from a fresh render, including a page that was never written."""
    stale: list[Path] = []
    for page_path, contents in rendered.items():
        committed = page_path.read_text(encoding="utf-8") if page_path.is_file() else None
        if committed != contents:
            stale.append(page_path.relative_to(cookbook.root))
    return stale


def lockstep_problems(cookbook: Cookbook) -> list[str]:
    """Every manifest's `version` must be the cookbook's own, as the library's lockstep convention asks: a manifest states the release it ships in."""
    problems: list[str] = []
    for package in cookbook.packages:
        if package.manifest.version != cookbook.version:
            problems.append(
                f"{package.directory.relative_to(cookbook.root)}/METHODS.toml declares version {package.manifest.version}, "
                f"but the cookbook is at {cookbook.version}"
            )
    return problems


def collect_raw_urls(*, cookbook: Cookbook, rendered: dict[Path, str]) -> dict[str, list[str]]:
    """Every raw URL in the packages' inputs and on the pages, each with the files it appears in."""
    found: dict[str, list[str]] = {}
    for package in cookbook.packages:
        inputs_file = f"{package.directory.relative_to(cookbook.root)}/{INPUTS_FILE}"
        for url in _urls_in_json(package.inputs):
            if url.startswith(f"{RAW_BASE_URL}/"):
                found.setdefault(url, []).append(inputs_file)
    for page_path, contents in rendered.items():
        page_file = str(page_path.relative_to(cookbook.root))
        for url in _RAW_URL_PATTERN.findall(contents):
            found.setdefault(url, []).append(page_file)
    return {url: sorted(set(files)) for url, files in sorted(found.items())}


def check_links(*, cookbook: Cookbook, rendered: dict[Path, str], fetch_status: Callable[[str], int]) -> list[LinkVerdict]:
    """Check every raw URL.

    A URL into the cookbook itself must name a file this checkout holds, whichever ref it names. When it does not answer, it is reported as not
    published rather than as broken: a file added since the last release is on neither `main` nor that release's tag, and the next release both
    publishes it and re-renders every page at its own tag. Any other URL must answer.

    Args:
        cookbook: The cookbook.
        rendered: The pages, freshly rendered.
        fetch_status: Fetches a URL and returns its HTTP status, following redirects.
    """
    verdicts: list[LinkVerdict] = []
    own_prefix = f"{RAW_BASE_URL}/{cookbook.settings.repository}/".lower()
    for url, found_in in collect_raw_urls(cookbook=cookbook, rendered=rendered).items():
        status = fetch_status(url)
        answered = 200 <= status < 300
        if url.lower().startswith(own_prefix):
            ref, _, url_path = url[len(own_prefix) :].partition("/")
            local_path = unquote(url_path)
            if not (cookbook.root / local_path).is_file():
                verdicts.append(LinkVerdict(url=url, found_in=found_in, ok=False, note=f"no file at {local_path} in this checkout"))
            elif answered:
                verdicts.append(LinkVerdict(url=url, found_in=found_in, ok=True, note="answers"))
            else:
                verdicts.append(
                    LinkVerdict(
                        url=url,
                        found_in=found_in,
                        ok=True,
                        note=f"not published at {ref} (HTTP {status}); the file is in this checkout, and the next release publishes it",
                    )
                )
        elif answered:
            verdicts.append(LinkVerdict(url=url, found_in=found_in, ok=True, note="answers"))
        else:
            verdicts.append(LinkVerdict(url=url, found_in=found_in, ok=False, note=f"HTTP {status}"))
    return verdicts


def http_status(url: str) -> int:
    """Fetch a URL's status with a HEAD request, falling back to GET when the server refuses HEAD. A transport failure reads as status 0."""
    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            response = client.head(url)
            if response.status_code == 405:
                response = client.get(url)
            return response.status_code
    except httpx.TransportError:
        return 0


def _urls_in_json(value: JsonValue) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "url" and isinstance(item, str):
                urls.append(item)
            else:
                urls.extend(_urls_in_json(item))
    elif isinstance(value, list):
        for item in value:
            urls.extend(_urls_in_json(item))
    return urls
