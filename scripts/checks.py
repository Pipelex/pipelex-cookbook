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
_SENTENCE_PUNCTUATION = ".,;:!?"
_NOT_FOUND = 404


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


def collect_urls(*, cookbook: Cookbook, rendered: dict[Path, str]) -> dict[str, list[str]]:
    """Every URL in the packages' inputs, wherever it is hosted, and every raw URL on the pages, each with the files it appears in."""
    found: dict[str, list[str]] = {}
    for package in cookbook.packages:
        inputs_file = f"{package.directory.relative_to(cookbook.root)}/{INPUTS_FILE}"
        for url in _urls_in_json(package.inputs):
            found.setdefault(url, []).append(inputs_file)
    for page_path, contents in rendered.items():
        page_file = str(page_path.relative_to(cookbook.root))
        for match in _RAW_URL_PATTERN.findall(contents):
            # A URL closing a sentence keeps the sentence's punctuation in the match, and no sample's name ends in one.
            found.setdefault(match.rstrip(_SENTENCE_PUNCTUATION), []).append(page_file)
    return {url: sorted(set(files)) for url, files in sorted(found.items())}


def check_links(*, cookbook: Cookbook, rendered: dict[Path, str], fetch_status: Callable[[str], int]) -> list[LinkVerdict]:
    """Check every sample URL and every raw URL on the pages.

    A URL into the cookbook itself must name a file this checkout holds, whichever ref it names. When it answers 404, it is reported as not
    published rather than as broken: a file added since the last release is on neither `main` nor that release's tag, and the next release both
    publishes it and re-renders every page at its own tag. Any other URL must answer.

    Args:
        cookbook: The cookbook.
        rendered: The pages, freshly rendered.
        fetch_status: Fetches a URL and returns its HTTP status, following redirects.
    """
    verdicts: list[LinkVerdict] = []
    own_prefix = f"{RAW_BASE_URL}/{cookbook.settings.repository}/".lower()
    for url, found_in in collect_urls(cookbook=cookbook, rendered=rendered).items():
        status = fetch_status(url)
        answered = 200 <= status < 300
        if url.lower().startswith(own_prefix):
            ref, _, url_path = url[len(own_prefix) :].partition("/")
            local_path = unquote(url_path)
            if not (cookbook.root / local_path).is_file():
                verdicts.append(LinkVerdict(url=url, found_in=found_in, ok=False, note=f"no file at {local_path} in this checkout"))
            elif answered:
                verdicts.append(LinkVerdict(url=url, found_in=found_in, ok=True, note="answers"))
            elif status != _NOT_FOUND:
                # Only a 404 means the ref does not hold the file yet; any other failure is a failure.
                verdicts.append(LinkVerdict(url=url, found_in=found_in, ok=False, note=f"HTTP {status}" if status else "no answer"))
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
    """Fetch a URL's status with a HEAD request, asking again with GET when HEAD gets an error.

    Hosts refuse HEAD in more ways than 405: some answer 501, 403 or even 404 to a HEAD and serve the same URL to a GET, so an error answer to
    HEAD is only read once a GET confirms it. The GET's body is never downloaded. A request that gets no status, whether the transport failed,
    the redirects loop or the URL is malformed, reads as status 0.
    """
    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            status = client.head(url).status_code
            if status >= 400:
                with client.stream("GET", url) as response:
                    status = response.status_code
            return status
    except (httpx.HTTPError, httpx.InvalidURL):
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
