"""The front page's list of the method library's methods, written from a snapshot of the library's manifests at a pinned tag.

`cookbook.toml`'s `[library]` table pins the library's address, its GitHub repository and a release tag. `make refresh-library` downloads that
tag's tarball from GitHub, which needs no key and no git, reads every `methods/<name>/METHODS.toml` in it in memory with the MTHDS standard's own
manifest parser, and writes `library.json` at the root, keeping only what the front page prints. `make render` reads only that snapshot, so the
front page renders with no network, and loading the cookbook refuses a snapshot taken from another repository, address or tag than the one pinned.
`make check-library` takes the snapshot again and fails when the committed one differs, as a hand edit makes it.
"""

import io
import json
import tarfile
from collections.abc import Callable
from pathlib import Path, PurePosixPath

import httpx
from mthds.package.exceptions import ManifestError
from mthds.package.manifest.parser import parse_methods_toml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from scripts.exceptions import CookbookError, CookbookLayoutError

LIBRARY_FILE = "library.json"
TARBALL_URL = "https://codeload.github.com/{repository}/tar.gz/refs/tags/{tag}"
# Where the library keeps its packages, `methods/<name>/`, which the front page links each method's directory under.
LIBRARY_METHODS_DIR = "methods"
_MANIFEST_FILE = "METHODS.toml"
_REFRESH_HINT = "run `make refresh-library` to take the snapshot again"


class LibraryFetchError(CookbookError):
    """The library's tarball could not be downloaded."""


class LibrarySettings(BaseModel):
    """The `[library]` table of `cookbook.toml`: the method library the front page lists, and the tag its snapshot is taken at."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    address: str = Field(description="The address every library manifest carries, such as `github.com/Pipelex/methods`")
    repository: str = Field(description="The library's GitHub repository, `<owner>/<name>`, whose tagged tarball the snapshot is taken from")
    tag: str = Field(description="The library release the front page lists, such as `v0.1.2`")

    @property
    def version(self) -> str:
        """The version every manifest at the tag carries: the tag without its `v`."""
        return self.tag.removeprefix("v")


class LibraryMethod(BaseModel):
    """One library method, as the front page prints it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    display_name: str
    description: str
    main_pipe: str


class LibrarySnapshot(BaseModel):
    """The contents of `library.json`: the library's methods at one tag of one repository, sorted by name."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    address: str
    repository: str
    tag: str
    methods: list[LibraryMethod]

    def to_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"


def load_library(root: Path, settings: LibrarySettings) -> LibrarySnapshot:
    """Read `library.json`, and hold it to the repository, the address and the tag `cookbook.toml` pins.

    Raises:
        CookbookLayoutError: The snapshot is missing or does not load, or it was taken from another repository, address or tag than the one
            pinned.
    """
    path = root / LIBRARY_FILE
    if not path.is_file():
        msg = f"{path} is missing: {_REFRESH_HINT}"
        raise CookbookLayoutError(msg)
    try:
        snapshot = LibrarySnapshot.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        msg = f"{path} does not load, so {_REFRESH_HINT}:\n{exc}"
        raise CookbookLayoutError(msg) from exc
    taken = (snapshot.repository, snapshot.address, snapshot.tag)
    pinned = (settings.repository, settings.address, settings.tag)
    if taken != pinned:
        msg = f"{path} was taken from {_coordinates(*taken)}, but cookbook.toml pins {_coordinates(*pinned)}: {_REFRESH_HINT}"
        raise CookbookLayoutError(msg)
    return snapshot


def snapshot_from_tarball(data: bytes, settings: LibrarySettings) -> LibrarySnapshot:
    """Build the snapshot from the library's tarball at the pinned tag, reading each `methods/<name>/METHODS.toml` in memory.

    Raises:
        CookbookLayoutError: The tarball does not open, holds no method, or holds a manifest that does not parse, that names another package
            than its directory, or that carries another address than the pinned one or another version than the tag's.
    """
    methods: list[LibraryMethod] = []
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            for member in archive.getmembers():
                name = _package_name(member)
                if name is None:
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                methods.append(_library_method(name=name, text=extracted.read().decode("utf-8"), settings=settings))
    except (tarfile.TarError, OSError, EOFError, UnicodeDecodeError) as exc:
        msg = f"the tarball of {settings.repository} at {settings.tag} does not open: {exc}"
        raise CookbookLayoutError(msg) from exc
    if not methods:
        msg = f"the tarball of {settings.repository} at {settings.tag} holds no {LIBRARY_METHODS_DIR}/<name>/{_MANIFEST_FILE}"
        raise CookbookLayoutError(msg)
    return LibrarySnapshot(
        address=settings.address, repository=settings.repository, tag=settings.tag, methods=sorted(methods, key=lambda method: method.name)
    )


def fetch_library(settings: LibrarySettings, *, fetch: Callable[[str], bytes]) -> LibrarySnapshot:
    """Download the library's tarball at the pinned tag with `fetch`, and build its snapshot."""
    return snapshot_from_tarball(fetch(TARBALL_URL.format(repository=settings.repository, tag=settings.tag)), settings)


def snapshot_is_current(snapshot: LibrarySnapshot, settings: LibrarySettings, *, fetch: Callable[[str], bytes]) -> bool:
    """Whether the committed snapshot equals one taken again now from the tarball at the pinned tag, which a hand edit breaks."""
    return fetch_library(settings, fetch=fetch) == snapshot


def download(url: str) -> bytes:
    """Download a URL's body, following redirects.

    Raises:
        LibraryFetchError: The request got no answer, or an answer that is not a success.
    """
    try:
        response = httpx.get(url, follow_redirects=True, timeout=60.0)
    except httpx.HTTPError as exc:
        msg = f"{url} could not be downloaded: {exc}"
        raise LibraryFetchError(msg) from exc
    if not response.is_success:
        msg = f"{url} answered HTTP {response.status_code}"
        raise LibraryFetchError(msg)
    return response.content


def _package_name(member: tarfile.TarInfo) -> str | None:
    """The package's name when the member is `<top>/methods/<name>/METHODS.toml`, the layout of a GitHub tarball of the library."""
    parts = PurePosixPath(member.name).parts
    if member.isfile() and len(parts) == 4 and parts[1] == LIBRARY_METHODS_DIR and parts[3] == _MANIFEST_FILE:
        return parts[2]
    return None


def _library_method(*, name: str, text: str, settings: LibrarySettings) -> LibraryMethod:
    where = f"{LIBRARY_METHODS_DIR}/{name}/{_MANIFEST_FILE} at {settings.tag}"
    try:
        manifest = parse_methods_toml(text)
    except ManifestError as exc:
        msg = f"{where} does not parse: {exc}"
        raise CookbookLayoutError(msg) from exc
    if manifest.name != name:
        msg = f"{where} names the package `{manifest.name}`, but its directory is `{name}`"
        raise CookbookLayoutError(msg)
    if manifest.address != settings.address:
        msg = f"{where} carries the address `{manifest.address}`, but cookbook.toml pins the library at `{settings.address}`"
        raise CookbookLayoutError(msg)
    if manifest.version != settings.version:
        msg = f"{where} declares version {manifest.version}, but the tag is {settings.tag}"
        raise CookbookLayoutError(msg)
    if not manifest.main_pipe:
        msg = f"{where} names no main_pipe, so its address runs nothing"
        raise CookbookLayoutError(msg)
    return LibraryMethod(name=name, display_name=manifest.display_name or name, description=manifest.description, main_pipe=manifest.main_pipe)


def _coordinates(repository: str, address: str, tag: str) -> str:
    return f"{repository} ({address}) at {tag}"
