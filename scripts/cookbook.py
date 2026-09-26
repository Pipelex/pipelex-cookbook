"""Load the cookbook: its version, its editorial fields in `cookbook.toml`, every method package under `methods/`, and the library's snapshot.

A package is a directory holding a `METHODS.toml` manifest, its `.mthds` bundles, a sample `inputs.json`, and the contract snapshot
`contract.json` that `make refresh` writes; the output snapshot `output.json` that `make snapshot` writes beside them is read by
`scripts/snapshot.py`, not here. Loading checks the package's identity: its manifest's `name` is its directory's name and its `address` is the
cookbook's, since the runtime locates a package by that pair and never by its path. It also holds the contract snapshot to the package's files:
the main pipe, its output concept and its multiplicity must be what the `.mthds` files declare. The method library's snapshot, `library.json`,
must have been taken at the tag and the address `cookbook.toml` pins (`scripts/library.py`).

Each sample input's source and licence is a record in `cookbook.toml`, which loading validates: a record names an input the sample gives, says
whether the input was made up, and a real input that is a file lives under `assets/<name>/` in this repository. An input with no record at all
is not refused here but by `make check-render`, so that every other command still runs while a sample's provenance is being settled.
"""

import json
import tomllib
from datetime import date
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import unquote, urlsplit

from mthds.package.exceptions import ManifestError
from mthds.package.manifest.parser import parse_methods_toml
from mthds.package.manifest.schema import MethodsManifest
from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError, model_validator

from scripts.bundles import DeclaredOutput, declared_main_output
from scripts.contract import CONTRACT_FILE, Contract, load_contract
from scripts.exceptions import CookbookLayoutError
from scripts.library import LibrarySettings, LibrarySnapshot, load_library

COOKBOOK_FILE = "cookbook.toml"
PYPROJECT_FILE = "pyproject.toml"
METHODS_DIR = "methods"
MANIFEST_FILE = "METHODS.toml"
INPUTS_FILE = "inputs.json"
PAGE_FILE = "README.md"
# Where `make render` writes each method's page snippets as files, in `tests/snippets/<name>/`, for the type checkers to read.
SNIPPETS_DIR = "tests/snippets"
# Where a sample's files live: a real input's under `assets/<name>/`, named by `inputs.json` by their raw URL on `main`.
ASSETS_DIR = "assets"
# Where a raw URL into a GitHub repository points: `<RAW_BASE_URL>/<owner>/<repository>/<ref>/<path>`.
RAW_BASE_URL = "https://raw.githubusercontent.com"
# How a text field of an output reads on the page, as the `formats` hint of `[methods.<name>.output]` names it.
TextFormat = Literal["markdown", "html", "text"]


class SampleRecord(BaseModel):
    """Where one sample input comes from and under which licence it is shown, from `[methods.<name>.samples.<input>]` in `cookbook.toml`.

    A made-up input has no source: it was written or rendered for the example, and the page says it is fictional. A real input names the URL it
    was copied from and the date it was copied, and a real input that is a file lives under `assets/<name>/` (DB3 of the making-examples design).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(description="The link text of the sample, and its name on the page")
    synthetic: bool = Field(description="Whether the input was made up for the example, which the page says")
    source: str | None = Field(default=None, description="The URL the input was copied from; absent for a made-up input")
    retrieved: date | None = Field(default=None, description="The date the input was copied from its source; only with a source")
    license: str = Field(description="The licence's SPDX identifier, or a `LicenseRef-…` for one SPDX does not list")
    license_url: str = Field(description="Where the licence's text is")
    attribution: str = Field(description="The credit line the licence asks for")
    changes: str | None = Field(default=None, description="What was changed from the source, which CC BY asks to say")

    @model_validator(mode="after")
    def _check_provenance(self) -> "SampleRecord":
        if self.synthetic and self.source is not None:
            msg = "a made-up sample (`synthetic = true`) has no `source`: it was written or rendered for the example"
            raise ValueError(msg)
        if not self.synthetic and self.source is None:
            msg = "a real sample (`synthetic = false`) names the URL it was copied from in `source`"
            raise ValueError(msg)
        if self.source is not None and self.retrieved is None:
            msg = "a sample copied from a `source` gives the date it was copied in `retrieved`"
            raise ValueError(msg)
        if self.source is None and self.retrieved is not None:
            msg = "`retrieved` is the date a sample was copied from its `source`, and this record names none"
            raise ValueError(msg)
        return self


class OutputHints(BaseModel):
    """How the page renders a method's output where the contract alone does not say, from `[methods.<name>.output]` in `cookbook.toml`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    formats: dict[str, TextFormat] = Field(
        default_factory=dict, description="How a text field of the output reads: `markdown`, `html` or `text`, by field name"
    )
    item_label: str | None = Field(default=None, description="The noun naming each item of a list output, such as `Page`")


class EditorialEntry(BaseModel):
    """A method's editorial fields in `cookbook.toml`. Every field is optional: a method with no entry still gets a page from its manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str | None = Field(default=None, description="The page's title; the manifest's display name otherwise")
    pitch: str | None = Field(default=None, description="The one-line pitch under the title; the manifest's description otherwise")
    samples: dict[str, SampleRecord] = Field(default_factory=dict, description="Each sample input's source and licence, by input name")
    output: OutputHints = Field(default_factory=OutputHints, description="How the page renders the output where the contract does not say")
    chatbot: str | None = Field(default=None, description="What to ask the chatbot, with `{address}` and `{samples}` placeholders")
    app_dir: str | None = Field(default=None, description="The directory the method-app initializer creates")
    yours_dir: str | None = Field(default=None, description="The directory the agent copies the method into")
    yours_change: str | None = Field(default=None, description="The change 'Make it yours' asks the agent for")


class CookbookSettings(BaseModel):
    """The contents of `cookbook.toml`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    address: str = Field(description="The address every cookbook manifest carries, such as `github.com/Pipelex/pipelex-cookbook`")
    repository: str = Field(description="The GitHub repository, `<owner>/<name>`, that raw sample URLs point into")
    library: LibrarySettings = Field(description="The method library the front page lists, and the tag its snapshot is taken at")
    methods: dict[str, EditorialEntry] = Field(default_factory=dict)


class MethodPackage(BaseModel):
    """One cookbook method, as loaded from its directory."""

    model_config = ConfigDict(frozen=True)

    directory: Path
    manifest: MethodsManifest
    bundle_files: list[str] = Field(description="The package's `.mthds` files, relative to its directory, sorted")
    inputs: dict[str, JsonValue] = Field(description="The sample inputs of `inputs.json`")
    contract: Contract | None = Field(description="The committed contract snapshot, or None before the first `make refresh`")
    editorial: EditorialEntry

    @property
    def name(self) -> str:
        """The package's name, which loading has checked is both its directory's name and its manifest's."""
        return self.directory.name

    @property
    def page_path(self) -> Path:
        return self.directory / PAGE_FILE

    @property
    def contract_path(self) -> Path:
        return self.directory / CONTRACT_FILE

    def bundle_paths(self) -> list[Path]:
        return [self.directory / bundle_file for bundle_file in self.bundle_files]


class LocalFile(BaseModel):
    """A file of this checkout that a raw URL into the cookbook's repository names."""

    model_config = ConfigDict(frozen=True)

    ref: str = Field(description="The ref the URL names the file at: `main` or a release tag")
    path: Path = Field(description="The file in this checkout, resolved")


class Cookbook(BaseModel):
    """The whole cookbook as the renderer and the checks see it."""

    model_config = ConfigDict(frozen=True)

    root: Path
    version: str = Field(description="The cookbook's version, from `pyproject.toml`, without the `v`")
    settings: CookbookSettings
    packages: list[MethodPackage]
    library: LibrarySnapshot | None = Field(description="The library's snapshot, or None for `make refresh-library`, which rewrites it")

    @property
    def tag(self) -> str:
        """The release tag every page names: `v` and the version, which on `dev` is the latest release and on a release branch the one being cut."""
        return f"v{self.version}"

    def address_of(self, package: MethodPackage) -> str:
        return f"{self.settings.address}/{package.name}@{self.tag}"

    def local_file_of(self, url: str) -> LocalFile | None:
        """The file of this checkout a raw URL into the cookbook's repository names, or None for a URL hosted elsewhere.

        The URL's path is `/<owner>/<repository>/<ref>/<file>`, where the ref is one path segment, `main` or a release tag, as the guides ask
        of every link into this repository; its query and fragment are no part of the file's path. The file's path is percent-decoded and
        resolved under the checkout, so a path climbing out of it, with `..` or from the filesystem's root, names no file of this checkout.

        Raises:
            CookbookLayoutError: The URL points into the cookbook's repository, but names no file this checkout holds. The message names the
                path the URL names rather than the URL, which the caller holds.
        """
        named = _raw_url_file(url, repository=self.settings.repository)
        if named is None:
            return None
        ref, relative = named
        root = self.root.resolve()
        local_path = (root / relative).resolve()
        if not local_path.is_relative_to(root):
            msg = f"its path {relative} leads outside this checkout"
            raise CookbookLayoutError(msg)
        if not local_path.is_file():
            msg = f"this checkout holds no file at {relative}"
            raise CookbookLayoutError(msg)
        return LocalFile(ref=ref, path=local_path)


def load_cookbook(root: Path, *, read_contracts: bool = True, read_library: bool = True) -> Cookbook:
    """Load the cookbook rooted at `root`.

    Args:
        root: The repository root.
        read_contracts: Whether to read each package's `contract.json`. `make refresh` rewrites the snapshots, so it loads without them and
            recovers from a snapshot that no longer loads.
        read_library: Whether to read `library.json`. `make refresh-library` rewrites it, so it loads without it and recovers from a snapshot
            taken at another tag.

    Raises:
        CookbookLayoutError: A file is missing or malformed, a package's identity is wrong, `cookbook.toml` names a method that does not exist,
            or the library's snapshot was taken at another tag or address than the one `cookbook.toml` pins.
    """
    version = read_version(root / PYPROJECT_FILE)
    settings = _load_settings(root / COOKBOOK_FILE)
    methods_dir = root / METHODS_DIR
    package_dirs = sorted(child for child in methods_dir.iterdir() if child.is_dir()) if methods_dir.is_dir() else []
    packages = [_load_package(directory=package_dir, settings=settings, read_contract=read_contracts) for package_dir in package_dirs]
    known_names = {package.name for package in packages}
    unknown_entries = sorted(set(settings.methods) - known_names)
    if unknown_entries:
        msg = f"{root / COOKBOOK_FILE} has editorial entries for methods that do not exist under {METHODS_DIR}/: {', '.join(unknown_entries)}"
        raise CookbookLayoutError(msg)
    library = load_library(root, settings.library) if read_library else None
    return Cookbook(root=root, version=version, settings=settings, packages=packages, library=library)


def read_version(pyproject_path: Path) -> str:
    """Read `[project].version` from a `pyproject.toml`.

    Raises:
        CookbookLayoutError: The file has no project version.
    """
    data = _read_toml(pyproject_path)
    project = data.get("project")
    version = cast("dict[str, Any]", project).get("version") if isinstance(project, dict) else None
    if not isinstance(version, str):
        msg = f"{pyproject_path} has no [project].version"
        raise CookbookLayoutError(msg)
    return version


def _load_settings(path: Path) -> CookbookSettings:
    try:
        return CookbookSettings.model_validate(_read_toml(path))
    except ValidationError as exc:
        msg = f"{path} does not load:\n{exc}"
        raise CookbookLayoutError(msg) from exc


def _load_package(*, directory: Path, settings: CookbookSettings, read_contract: bool) -> MethodPackage:
    manifest_path = directory / MANIFEST_FILE
    if not manifest_path.is_file():
        msg = f"{directory} holds no {MANIFEST_FILE}: every directory under {METHODS_DIR}/ is a method package"
        raise CookbookLayoutError(msg)
    try:
        manifest = parse_methods_toml(manifest_path.read_text(encoding="utf-8"))
    except ManifestError as exc:
        msg = f"{manifest_path} does not parse: {exc}"
        raise CookbookLayoutError(msg) from exc
    if manifest.name is None or manifest.name != directory.name:
        msg = f"{manifest_path} names the package `{manifest.name}`, but its directory is `{directory.name}`"
        raise CookbookLayoutError(msg)
    if manifest.address != settings.address:
        msg = f"{manifest_path} carries the address `{manifest.address}`, but every cookbook manifest carries `{settings.address}`"
        raise CookbookLayoutError(msg)
    if not manifest.main_pipe:
        msg = f"{manifest_path} names no main_pipe: a cookbook method's page runs its main pipe"
        raise CookbookLayoutError(msg)

    bundle_files = sorted(bundle_path.name for bundle_path in directory.glob("*.mthds"))
    if not bundle_files:
        msg = f"{directory} holds no .mthds bundle"
        raise CookbookLayoutError(msg)

    inputs = _load_inputs(directory / INPUTS_FILE)
    editorial = settings.methods.get(directory.name) or EditorialEntry()
    _check_sample_records(directory=directory, settings=settings, editorial=editorial, inputs=inputs)
    contract_path = directory / CONTRACT_FILE
    contract = load_contract(contract_path) if read_contract and contract_path.is_file() else None
    if contract is not None:
        _check_contract_against_bundles(
            contract=contract,
            contract_path=contract_path,
            declared=declared_main_output(bundle_paths=[directory / bundle_file for bundle_file in bundle_files], main_pipe=manifest.main_pipe),
        )

    return MethodPackage(
        directory=directory,
        manifest=manifest,
        bundle_files=bundle_files,
        inputs=inputs,
        contract=contract,
        editorial=editorial,
    )


def input_content(value: JsonValue) -> JsonValue:
    """An input's content as code passes it: `inputs.json` may wrap a value as `{"concept": …, "content": …}`, and the content is inside.

    Only a dict whose keys are exactly `concept` and `content` is that wrapper, as the runtime reads it: a structured input whose concept has a
    field named `content` is passed whole.
    """
    if isinstance(value, dict) and set(value) == {"concept", "content"}:
        return value["content"]
    return value


def file_urls(content: JsonValue) -> list[str]:
    """The URLs of a file input, given as one `{"url": …}` object or as a list of them."""
    if isinstance(content, dict):
        url = content.get("url")
        return [url] if isinstance(url, str) else []
    if isinstance(content, list):
        return [url for item in content if isinstance(item, dict) and isinstance(url := item.get("url"), str)]
    return []


def _raw_url_file(url: str, *, repository: str) -> tuple[str, str] | None:
    """The ref and the percent-decoded path from the repository root that a raw URL into `repository` names, or None for a URL hosted elsewhere.

    This is the one reading of a raw URL into the cookbook's repository: `Cookbook.local_file_of` resolves the path it gives under the checkout,
    and the sample records' check reads where a real sample lives from it before any cookbook is loaded. The URL's path is
    `/<owner>/<repository>/<ref>/<file>`, where the ref is one path segment, and its query and fragment are no part of the file's path.
    """
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if f"{parts.scheme}://{parts.netloc}".lower() != RAW_BASE_URL.lower():
        return None
    # GitHub reads an owner's and a repository's names whatever their case.
    owner_and_name = repository.lower().split("/")
    segments = parts.path.removeprefix("/").split("/")
    if len(segments) <= len(owner_and_name) or [segment.lower() for segment in segments[: len(owner_and_name)]] != owner_and_name:
        return None
    return segments[len(owner_and_name)], unquote("/".join(segments[len(owner_and_name) + 1 :]))


def _check_sample_records(*, directory: Path, settings: CookbookSettings, editorial: EditorialEntry, inputs: dict[str, JsonValue]) -> None:
    """Refuse a sample record naming an input the sample does not give, and a real file sample kept anywhere but under `assets/<name>/`.

    Raises:
        CookbookLayoutError: A record is out of place.
    """
    unknown = sorted(set(editorial.samples) - set(inputs))
    if unknown:
        msg = (
            f"{COOKBOOK_FILE} has sample records for `{directory.name}` inputs its {INPUTS_FILE} does not give: {', '.join(unknown)}; "
            "a record describes one input of the sample"
        )
        raise CookbookLayoutError(msg)
    own_assets = f"{ASSETS_DIR}/{directory.name}/"
    for input_name, record in editorial.samples.items():
        if record.synthetic:
            continue
        for url in file_urls(input_content(inputs[input_name])):
            named = _raw_url_file(url, repository=settings.repository)
            if named is None or not named[1].startswith(own_assets):
                msg = (
                    f"the sample `{input_name}` of `{directory.name}` is a real file, so it is copied under {own_assets} in this repository "
                    f"and linked by its raw URL, never linked where it is published: {url}"
                )
                raise CookbookLayoutError(msg)


def _check_contract_against_bundles(*, contract: Contract, contract_path: Path, declared: DeclaredOutput) -> None:
    """Refuse a snapshot whose main pipe, output concept or multiplicity is not what the package's `.mthds` files declare.

    Raises:
        CookbookLayoutError: The snapshot and the files disagree, which means a bundle changed without `make refresh`.
    """
    recorded = DeclaredOutput(
        pipe=contract.pipe,
        concept=contract.output.concept,
        multiplicity=contract.output.multiplicity,
        item_count=contract.output.item_count,
    )
    if recorded != declared:
        msg = (
            f"{contract_path} says the main pipe `{recorded.pipe}` returns {_phrase_output(recorded)}, "
            f"but the package's .mthds files declare `{declared.pipe}` returning {_phrase_output(declared)}: "
            "run `make refresh` to take the contract again"
        )
        raise CookbookLayoutError(msg)


def _phrase_output(output: DeclaredOutput) -> str:
    if output.multiplicity == "single":
        return f"one `{output.concept}`"
    if output.item_count is not None:
        return f"a list of {output.item_count} `{output.concept}`"
    return f"a list of `{output.concept}`"


def _load_inputs(path: Path) -> dict[str, JsonValue]:
    if not path.is_file():
        msg = f"{path.parent} holds no {INPUTS_FILE}: every cookbook method carries sample inputs"
        raise CookbookLayoutError(msg)
    try:
        data: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"{path} is not JSON: {exc}"
        raise CookbookLayoutError(msg) from exc
    if not isinstance(data, dict):
        msg = f"{path} must hold one object, keyed by input name"
        raise CookbookLayoutError(msg)
    return cast("dict[str, JsonValue]", data)


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        msg = f"{path} is missing"
        raise CookbookLayoutError(msg)
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        msg = f"{path} is not valid TOML: {exc}"
        raise CookbookLayoutError(msg) from exc
