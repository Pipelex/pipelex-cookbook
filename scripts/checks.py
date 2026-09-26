"""The checks that need no API key, run on every pull request: the pages are fresh, the manifests are in lockstep, and every sample link answers.

Freshness covers every file `make render` writes, the pages' snippet files included, and a snippet directory left behind by a method that is gone.
It also covers what a page shows that no render can write: every sample input has its source-and-licence record, every document sample kept in
this repository its preview, and every method its output snapshot, taken from the sample as it is and holding every file it names and no other.
A snapshot whose bundles changed since is only reported as stale, so a prompt tweak does not force a paid run.
The links are read from the packages' inputs, from the pages and from the recipes' own files.
"""

import re
from collections.abc import Callable
from pathlib import Path

import httpx
from pydantic import BaseModel, ConfigDict, JsonValue

from scripts.cookbook import COOKBOOK_FILE, INPUTS_FILE, SNIPPETS_DIR, Cookbook, MethodPackage
from scripts.exceptions import CookbookLayoutError
from scripts.recipes import recipe_files
from scripts.snapshot import (
    OUTPUT_DIR,
    SNAPSHOT_FILE,
    OutputSnapshot,
    bundle_digest,
    document_samples,
    inputs_digest,
    preview_path,
    read_snapshot,
    sha256_of,
)

_RAW_URL_PATTERN = re.compile(r"https://raw\.githubusercontent\.com/[^\s)\"'`<>]+")
_SENTENCE_PUNCTUATION = ".,;:!?"
_NOT_FOUND = 404
# The snippets' TypeScript package installs its dependencies beside the methods' snippet directories, and they belong to no method.
_INSTALLED_PACKAGES_DIR = "node_modules"


class LinkVerdict(BaseModel):
    """What the link check found for one raw URL."""

    model_config = ConfigDict(frozen=True)

    url: str
    found_in: list[str]
    ok: bool
    note: str


def stale_pages(*, cookbook: Cookbook, rendered: dict[Path, str]) -> list[Path]:
    """The rendered files, pages and snippet files alike, whose committed contents differ from a fresh render, including one never written."""
    stale: list[Path] = []
    for page_path, contents in rendered.items():
        committed = page_path.read_text(encoding="utf-8") if page_path.is_file() else None
        if committed != contents:
            stale.append(page_path.relative_to(cookbook.root))
    return stale


def orphan_snippet_dirs(cookbook: Cookbook) -> list[Path]:
    """The directories under `tests/snippets/` that belong to no package under `methods/`, such as a removed or renamed method's.

    `make render` writes each method's snippet files into a directory of its own there and never deletes one, so a directory a method left
    behind would go on being type-checked while no page shows it.
    """
    snippets_root = cookbook.root / SNIPPETS_DIR
    if not snippets_root.is_dir():
        return []
    names = {package.name for package in cookbook.packages}
    return sorted(
        child.relative_to(cookbook.root)
        for child in snippets_root.iterdir()
        if child.is_dir() and child.name not in names and child.name != _INSTALLED_PACKAGES_DIR
    )


def sample_problems(cookbook: Cookbook) -> list[str]:
    """Every sample input without its source-and-licence record, and every document sample kept in this repository without its preview."""
    problems: list[str] = []
    for package in cookbook.packages:
        package_dir = package.directory.relative_to(cookbook.root)
        for input_name in package.inputs:
            if input_name not in package.editorial.samples:
                problems.append(
                    f"{package_dir}: the sample input `{input_name}` has no source-and-licence record "
                    f"under [methods.{package.name}.samples.{input_name}] in {COOKBOOK_FILE}"
                )
        try:
            documents = document_samples(cookbook=cookbook, package=package)
        except CookbookLayoutError as exc:
            problems.append(str(exc))
            continue
        for document in documents:
            if not preview_path(document).is_file():
                problems.append(
                    f"{package_dir}: the document sample {document.relative_to(cookbook.root)} has no preview, "
                    f"{preview_path(document).relative_to(cookbook.root)}; `make snapshot METHOD={package.name}` renders it"
                )
    return problems


def snapshot_problems(cookbook: Cookbook) -> list[str]:
    """What is wrong with each method's output snapshot: missing, from another pipe or concept, from another sample, or its files out of step."""
    problems: list[str] = []
    for package in cookbook.packages:
        package_dir = package.directory.relative_to(cookbook.root)
        try:
            snapshot = read_snapshot(package)
        except CookbookLayoutError as exc:
            problems.append(str(exc))
            continue
        if snapshot is None:
            problems.append(f"{package_dir} has no {SNAPSHOT_FILE}: `make snapshot METHOD={package.name}` takes it, with one paid run on production")
            continue
        problems.extend(
            f"{package_dir}/{SNAPSHOT_FILE} {problem}" for problem in _snapshot_problems(cookbook=cookbook, package=package, snapshot=snapshot)
        )
    return problems


def stale_snapshots(cookbook: Cookbook) -> list[str]:
    """The snapshots taken from other bundles than the package's, which still show the method's output but no longer its current version's."""
    stale: list[str] = []
    for package in cookbook.packages:
        try:
            snapshot = read_snapshot(package)
        except CookbookLayoutError:
            continue
        if snapshot is not None and snapshot.run.bundle_sha256 != bundle_digest(cookbook=cookbook, package=package):
            stale.append(
                f"{package.directory.relative_to(cookbook.root)}/{SNAPSHOT_FILE} was taken from other bundles than the package's: "
                f"whoever changes what the method returns takes a new one with `make snapshot METHOD={package.name}`"
            )
    return stale


def _snapshot_problems(*, cookbook: Cookbook, package: MethodPackage, snapshot: OutputSnapshot) -> list[str]:
    problems: list[str] = []
    contract = package.contract
    if contract is not None:
        if snapshot.pipe != contract.pipe:
            problems.append(f"was taken from the pipe `{snapshot.pipe}`, and contract.json names `{contract.pipe}`")
        if snapshot.concept != contract.output.concept:
            problems.append(f"holds a `{snapshot.concept}`, and contract.json says the method returns a `{contract.output.concept}`")
    try:
        current_inputs = inputs_digest(cookbook=cookbook, package=package)
    except CookbookLayoutError as exc:
        problems.append(f"cannot be held to its sample: {exc}")
    else:
        if snapshot.run.inputs_sha256 != current_inputs:
            problems.append(
                "was taken from another sample than inputs.json and the assets it names: the page would show one input beside another's output"
            )
    output_dir = package.directory / OUTPUT_DIR
    for relative, entry in snapshot.files.items():
        path = package.directory / relative
        if not relative.startswith(f"{OUTPUT_DIR}/") or path.resolve().parent != output_dir.resolve():
            problems.append(f"names the file {relative}, which is not directly under {OUTPUT_DIR}/")
        elif not path.is_file():
            problems.append(f"names the file {relative}, which does not exist")
        elif sha256_of(path.read_bytes()) != entry.sha256:
            problems.append(f"names the file {relative}, whose contents changed since the snapshot")
    for referenced in sorted(_output_paths(snapshot.output) - set(snapshot.files)):
        problems.append(f"holds the path {referenced}, which its `files` does not list")
    if output_dir.is_dir():
        for path in sorted(output_dir.rglob("*")):
            relative = path.relative_to(package.directory).as_posix()
            if path.is_file() and relative not in snapshot.files:
                problems.append(f"does not name {relative}, which {OUTPUT_DIR}/ holds: `make snapshot` replaces {OUTPUT_DIR}/ as a whole")
    return problems


def _output_paths(value: JsonValue) -> set[str]:
    """Every string of the output that is a path under `output/`, where the writer put a copied file's path."""
    found: set[str] = set()
    if isinstance(value, str):
        if value.startswith(f"{OUTPUT_DIR}/"):
            found.add(value)
    elif isinstance(value, list):
        for item in value:
            found |= _output_paths(item)
    elif isinstance(value, dict):
        for item in value.values():
            found |= _output_paths(item)
    return found


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
    """Every URL in the packages' inputs, wherever it is hosted, and every raw URL on the pages and in the recipes, with the files it is in.

    A recipe's own files are read whatever their kind, since a sample is linked from a README, a script or a CSV alike; a file that is not text,
    such as an image, holds no link to read.
    """
    found: dict[str, list[str]] = {}
    for package in cookbook.packages:
        inputs_file = f"{package.directory.relative_to(cookbook.root)}/{INPUTS_FILE}"
        for url in _urls_in_json(package.inputs):
            found.setdefault(url, []).append(inputs_file)
    texts = dict(rendered)
    for recipe_file in recipe_files(cookbook.root):
        try:
            texts[recipe_file] = recipe_file.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
    for text_path, contents in texts.items():
        text_file = str(text_path.relative_to(cookbook.root))
        for match in _RAW_URL_PATTERN.findall(contents):
            # A URL closing a sentence keeps the sentence's punctuation in the match, and no sample's name ends in one.
            found.setdefault(match.rstrip(_SENTENCE_PUNCTUATION), []).append(text_file)
    return {url: sorted(set(files)) for url, files in sorted(found.items())}


def check_links(*, cookbook: Cookbook, rendered: dict[Path, str], fetch_status: Callable[[str], int]) -> list[LinkVerdict]:
    """Check every sample URL, and every raw URL on the pages and in the recipes.

    A URL into the cookbook itself must name a file this checkout holds, whichever ref it names, `main` or a release tag, as one path segment.
    When it answers 404, it is reported as not published rather than as broken: a file added since the last release is on neither `main` nor
    that release's tag, and the next release both publishes it and re-renders every page at its own tag. Any other URL must answer.

    Args:
        cookbook: The cookbook.
        rendered: The pages, freshly rendered.
        fetch_status: Fetches a URL and returns its HTTP status, following redirects.
    """
    verdicts: list[LinkVerdict] = []
    for url, found_in in collect_urls(cookbook=cookbook, rendered=rendered).items():
        status = fetch_status(url)
        answered = 200 <= status < 300
        try:
            local_file = cookbook.local_file_of(url)
        except CookbookLayoutError as exc:
            verdicts.append(LinkVerdict(url=url, found_in=found_in, ok=False, note=str(exc)))
            continue
        if local_file is not None:
            if answered:
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
                        note=f"not published at {local_file.ref} (HTTP {status}); the file is in this checkout, and the next release publishes it",
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
