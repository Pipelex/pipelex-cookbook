"""Load the cookbook: its version, its editorial fields in `cookbook.toml`, and every method package under `methods/`.

A package is a directory holding a `METHODS.toml` manifest, its `.mthds` bundles, a sample `inputs.json`, an answer key `key.md`, and the contract
snapshot `contract.json` that `make refresh` writes. Loading checks the package's identity: its manifest's `name` is its directory's name and its
`address` is the cookbook's, since the runtime locates a package by that pair and never by its path. It also holds the contract snapshot to the
package's files: the main pipe, its output concept and its multiplicity must be what the `.mthds` files declare.
"""

import json
import tomllib
from pathlib import Path
from typing import Any, cast

from mthds.package.exceptions import ManifestError
from mthds.package.manifest.parser import parse_methods_toml
from mthds.package.manifest.schema import MethodsManifest
from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError

from scripts.bundles import DeclaredOutput, declared_main_output
from scripts.contract import CONTRACT_FILE, Contract, load_contract
from scripts.exceptions import CookbookLayoutError
from scripts.key import AnswerKey, parse_key

COOKBOOK_FILE = "cookbook.toml"
PYPROJECT_FILE = "pyproject.toml"
METHODS_DIR = "methods"
MANIFEST_FILE = "METHODS.toml"
INPUTS_FILE = "inputs.json"
KEY_FILE = "key.md"
PAGE_FILE = "README.md"
# Where `make render` writes each method's page snippets as files, in `tests/snippets/<name>/`, for the type checkers to read.
SNIPPETS_DIR = "tests/snippets"


class EditorialEntry(BaseModel):
    """A method's editorial fields in `cookbook.toml`. Every field is optional: a method with no entry still gets a page from its manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str | None = Field(default=None, description="The page's title; the manifest's display name otherwise")
    pitch: str | None = Field(default=None, description="The one-line pitch under the title; the manifest's description otherwise")
    sample_labels: dict[str, str] = Field(default_factory=dict, description="The link text of each input's sample, by input name")
    chatbot: str | None = Field(default=None, description="What to ask the chatbot, with `{address}` and `{samples}` placeholders")
    app_dir: str | None = Field(default=None, description="The directory the method-app initializer creates")
    yours_dir: str | None = Field(default=None, description="The directory the agent copies the method into")
    yours_change: str | None = Field(default=None, description="The change 'Make it yours' asks the agent for")


class CookbookSettings(BaseModel):
    """The contents of `cookbook.toml`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    address: str = Field(description="The address every cookbook manifest carries, such as `github.com/Pipelex/pipelex-cookbook`")
    repository: str = Field(description="The GitHub repository, `<owner>/<name>`, that raw sample URLs point into")
    methods: dict[str, EditorialEntry] = Field(default_factory=dict)


class MethodPackage(BaseModel):
    """One cookbook method, as loaded from its directory."""

    model_config = ConfigDict(frozen=True)

    directory: Path
    manifest: MethodsManifest
    bundle_files: list[str] = Field(description="The package's `.mthds` files, relative to its directory, sorted")
    inputs: dict[str, JsonValue] = Field(description="The sample inputs of `inputs.json`")
    key: AnswerKey
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


class Cookbook(BaseModel):
    """The whole cookbook as the renderer and the checks see it."""

    model_config = ConfigDict(frozen=True)

    root: Path
    version: str = Field(description="The cookbook's version, from `pyproject.toml`, without the `v`")
    settings: CookbookSettings
    packages: list[MethodPackage]

    @property
    def tag(self) -> str:
        """The release tag every page names: `v` and the version, which on `dev` is the latest release and on a release branch the one being cut."""
        return f"v{self.version}"

    def address_of(self, package: MethodPackage) -> str:
        return f"{self.settings.address}/{package.name}@{self.tag}"


def load_cookbook(root: Path, *, read_contracts: bool = True) -> Cookbook:
    """Load the cookbook rooted at `root`.

    Args:
        root: The repository root.
        read_contracts: Whether to read each package's `contract.json`. `make refresh` rewrites the snapshots, so it loads without them and
            recovers from a snapshot that no longer loads.

    Raises:
        CookbookLayoutError: A file is missing or malformed, a package's identity is wrong, or `cookbook.toml` names a method that does not exist.
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
    return Cookbook(root=root, version=version, settings=settings, packages=packages)


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
    key_path = directory / KEY_FILE
    if not key_path.is_file():
        msg = f"{directory} holds no {KEY_FILE}: every cookbook method carries an answer key for its sample"
        raise CookbookLayoutError(msg)
    key = parse_key(key_path.read_text(encoding="utf-8"), source=str(key_path))
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
        key=key,
        contract=contract,
        editorial=settings.methods.get(directory.name) or EditorialEntry(),
    )


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
