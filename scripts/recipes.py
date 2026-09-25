"""Find the recipes' generated types and check, offline, what a recipe promises about the method it calls.

A recipe is a small project under `recipes/<door>/` showing one way to use a method on a real case. A code recipe calls its method by a
pinned address and carries the method's types in `generated/<method>/`: the stamped artifacts, the `codegen.lock` vouching for them, and
a `sources.json` naming the address and the codegen target they come from. `make refresh` regenerates each tree from its sidecar
(`scripts/sdk/recipe_codegen.py`, which runs beside `pipelex-sdk`), and this module is what the rest of the tooling reads a tree from.

The offline checks here hold each tree to its recipe: the sidecar names an address pinned to a tag and a target the recipe's language
reads, the recipe's own code calls that same address as a whole string literal, a Python recipe script declares `pipelex-sdk` among
its inline dependencies, and a TypeScript recipe's `package.json` depends on `@pipelex/sdk` and has its `codegen:check` script check
every tree it carries. Whether the types still match their lock is the SDK's check, whether the lock comes from what the address
resolves to is `make check-codegen-live`, and whether the address resolves is `make check-addresses`.

A recipe with no code of its own, such as a request to a coding agent, is a README, and the HTTP recipe carries a shell script. So the
addresses every recipe names in its READMEs, shell scripts and JSON files are read too, and each must be pinned to a release tag, as a
sidecar's is; `make check-addresses` validates them with the sidecars' addresses. Each shell script must parse under `sh -n`, and
`make check-recipe-types` runs shellcheck over them.
"""

import os
import re
import subprocess
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, ValidationError

RECIPES_DIR = "recipes"
GENERATED_DIR = "generated"
SIDECAR_FILE = "sources.json"
PYTHON_TARGET = "python-pydantic"
TYPESCRIPT_TARGET = "ts-zod"
TARGET_MARKERS = {PYTHON_TARGET: "a Python script declaring its dependencies inline", TYPESCRIPT_TARGET: "a package.json"}
CODE_SUFFIXES = frozenset({".py", ".ts", ".tsx", ".mts", ".mjs"})
SDK_DEPENDENCY = "pipelex-sdk"
PACKAGE_FILE = "package.json"
SDK_PACKAGE = "@pipelex/sdk"
CODEGEN_CHECK_SCRIPT = "codegen:check"
README_FILE = "README.md"
SHELL_SUFFIX = ".sh"
# The files a recipe names an address in, beside its code: its README, its shell scripts and its JSON files. A lock file npm writes names
# packages, never a method, so it is left out.
ADDRESS_SUFFIXES = frozenset({SHELL_SUFFIX, ".json"})
NPM_LOCK_FILE = "package-lock.json"

# Directories no recipe's own code or generated tree lives in: installed packages, environments and build output.
_SKIPPED_DIRS = frozenset({"node_modules", ".venv", "__pycache__", ".next", "dist", "build"})
_PINNED_ADDRESS = re.compile(r"^github\.com/[\w.-]+/[\w.-]+(/[\w.-]+)*@v\d+\.\d+\.\d+$")
_NOT_PINNED = "is not an address pinned to a release tag (github.com/<owner>/<repo>/<name>@vX.Y.Z)"
_SCRIPT_BLOCK = re.compile(r"^# /// script\s*$(?P<body>.*?)^# ///\s*$", re.MULTILINE | re.DOTALL)
# An address carrying a tag, wherever it stands in prose, a string or a URL: `github.com/<owner>/<repo>[/<selector>…]@<tag>`. A repository
# link without an `@` names no tag and is not read as an address, nor is a catalog id (`mt_…`); `api.github.com` is not `github.com`.
_TAGGED_ADDRESS = re.compile(r"(?<![\w.-])github\.com/[\w.-]+/[\w.-]+(?:/[\w.-]+)*@[\w.+-]+")
# An address closing a sentence keeps the sentence's full stop in the match, and no release tag ends in one.
_TAG_TRAILING_PUNCTUATION = "."


class SidecarMethod(BaseModel):
    method_ref: str


class Sidecar(BaseModel):
    """The part of a tree's `sources.json` the tooling reads: the address the types come from and the codegen target."""

    method: SidecarMethod
    target: str


class PackageManifest(BaseModel):
    """The part of a TypeScript recipe's `package.json` the tooling reads: what it depends on and the scripts it defines."""

    dependencies: dict[str, str] = Field(default_factory=dict)
    scripts: dict[str, str] = Field(default_factory=dict)


class RecipeAddress(BaseModel):
    """An address carrying a tag that a recipe names in its README, a shell script or a JSON file, with the file it is in."""

    model_config = ConfigDict(frozen=True)

    address: str
    file: Path


class RecipeTree(BaseModel):
    """One generated tree of a code recipe, and what its sidecar says it was generated from."""

    model_config = ConfigDict(frozen=True)

    recipe_dir: Path
    directory: Path
    method_ref: str | None
    target: str | None
    sidecar_problem: str | None = None


def find_trees(root: Path) -> list[RecipeTree]:
    """Every directory directly under a recipe's `generated/`, with its sidecar read.

    A tree is found by where it is, not by the files it should hold, so a tree that lost its sidecar and its lock is still found and
    reported rather than skipped.
    """
    recipes_root = root / RECIPES_DIR
    if not recipes_root.is_dir():
        return []
    tree_dirs: set[Path] = set()
    for generated_dir in recipes_root.rglob(GENERATED_DIR):
        if not generated_dir.is_dir() or _is_skipped(generated_dir, root=recipes_root):
            continue
        tree_dirs.update(child for child in generated_dir.iterdir() if child.is_dir() and child.name not in _SKIPPED_DIRS)
    return [_read_tree(directory) for directory in sorted(tree_dirs)]


def python_scripts(root: Path) -> list[Path]:
    """Every Python recipe script: a `.py` file outside `generated/` that declares its dependencies inline, as `uv run` reads them."""
    recipes_root = root / RECIPES_DIR
    if not recipes_root.is_dir():
        return []
    return sorted(
        path
        for path in recipes_root.rglob("*.py")
        if not _is_skipped(path, root=recipes_root) and GENERATED_DIR not in path.relative_to(recipes_root).parts and _script_block(path) is not None
    )


def typescript_packages(root: Path) -> list[Path]:
    """Every TypeScript recipe: a directory under `recipes/` holding a `package.json`, its installed packages left out."""
    recipes_root = root / RECIPES_DIR
    if not recipes_root.is_dir():
        return []
    return sorted(path.parent for path in recipes_root.rglob(PACKAGE_FILE) if not _is_skipped(path, root=recipes_root))


def recipe_files(root: Path) -> list[Path]:
    """Every file a recipe wrote itself, whatever its kind: its generated trees, installed packages and build output left out.

    The walk never enters a directory it leaves out, since a TypeScript recipe's installed packages alone hold thousands of files.
    """
    recipes_root = root / RECIPES_DIR
    if not recipes_root.is_dir():
        return []
    files: list[Path] = []
    for directory, subdirectories, file_names in os.walk(recipes_root):
        subdirectories[:] = [name for name in subdirectories if name not in _SKIPPED_DIRS and name != GENERATED_DIR]
        files.extend(Path(directory) / file_name for file_name in file_names)
    return sorted(files)


def shell_scripts(root: Path) -> list[Path]:
    """Every shell script of a recipe, which `sh -n` parses in `make check-recipes` and shellcheck reads in `make check-recipe-types`."""
    return [path for path in recipe_files(root) if path.suffix == SHELL_SUFFIX]


def find_addresses(root: Path) -> list[RecipeAddress]:
    """Every address carrying a tag that a recipe names in a README, a shell script or a JSON file, once per file it is in."""
    found: set[RecipeAddress] = set()
    for path in recipe_files(root):
        if path.name != README_FILE and (path.suffix not in ADDRESS_SUFFIXES or path.name == NPM_LOCK_FILE):
            continue
        for match in _TAGGED_ADDRESS.findall(path.read_text(encoding="utf-8")):
            found.add(RecipeAddress(address=match.rstrip(_TAG_TRAILING_PUNCTUATION), file=path))
    return sorted(found, key=lambda found_address: (str(found_address.file), found_address.address))


def recipe_addresses(root: Path) -> dict[str, list[str]]:
    """Every address the recipes pin, in a sidecar or in a README, a shell script or a JSON file, with the recipes naming it.

    A recipe is named by its directory: a sidecar's recipe is the directory holding `generated/`, and a file's recipe the directory it is in.
    """
    named_in: dict[str, set[str]] = {}
    for tree in find_trees(root):
        if tree.method_ref is not None:
            named_in.setdefault(tree.method_ref, set()).add(tree.recipe_dir.relative_to(root).as_posix())
    for found in find_addresses(root):
        named_in.setdefault(found.address, set()).add(found.file.parent.relative_to(root).as_posix())
    return {address: sorted(recipes) for address, recipes in sorted(named_in.items())}


def recipe_problems(root: Path) -> list[str]:
    """What an offline reading finds wrong with the recipes, one sentence each.

    It reads their generated trees, their Python scripts and TypeScript packages, the addresses they name, and their shell scripts.
    """
    problems: list[str] = []
    trees = find_trees(root)
    for tree in trees:
        where = tree.directory.relative_to(root)
        if tree.method_ref is None or tree.target is None:
            problems.append(f"{where}/{SIDECAR_FILE}: {tree.sidecar_problem}")
            continue
        if not _PINNED_ADDRESS.match(tree.method_ref):
            problems.append(f"{where}/{SIDECAR_FILE}: {tree.method_ref!r} {_NOT_PINNED}")
        if tree.target not in TARGET_MARKERS:
            problems.append(f"{where}/{SIDECAR_FILE}: target {tree.target!r} is none of {', '.join(sorted(TARGET_MARKERS))}")
        elif not _recipe_reads(tree.recipe_dir, target=tree.target):
            problems.append(f"{where}: target {tree.target} needs {TARGET_MARKERS[tree.target]} in {tree.recipe_dir.relative_to(root)}")
        if not any(_names_address(code, address=tree.method_ref) for code in _recipe_code(tree.recipe_dir)):
            problems.append(
                f"{where}: the recipe's code never names {tree.method_ref} as a string, so its types may describe another method than it calls"
            )
    for script in python_scripts(root):
        block = _script_block(script) or ""
        if SDK_DEPENDENCY not in block:
            problems.append(f"{script.relative_to(root)}: its inline dependencies do not name {SDK_DEPENDENCY}")
    for package_dir in typescript_packages(root):
        package_trees = [tree for tree in trees if tree.recipe_dir == package_dir and tree.target == TYPESCRIPT_TARGET]
        problems.extend(_package_problems(package_dir, root=root, trees=package_trees))
    for found in find_addresses(root):
        if not _PINNED_ADDRESS.match(found.address):
            problems.append(f"{found.file.relative_to(root)}: {found.address!r} {_NOT_PINNED}")
    for script in shell_scripts(root):
        parse_error = _shell_parse_error(script)
        if parse_error is not None:
            problems.append(f"{script.relative_to(root)}: `sh -n` cannot parse it: {parse_error}")
    return problems


def _shell_parse_error(script: Path) -> str | None:
    """What `sh -n` says of a script it cannot parse, or nothing when it parses. `sh -n` reads the script without running any of it."""
    completed = subprocess.run(["sh", "-n", str(script)], capture_output=True, text=True, check=False)
    if completed.returncode == 0:
        return None
    return completed.stderr.strip() or f"sh exited with status {completed.returncode}"


def _package_problems(package_dir: Path, *, root: Path, trees: list[RecipeTree]) -> list[str]:
    """What is wrong with a TypeScript recipe's `package.json`: the SDK it calls through, and the gate over each of its trees."""
    where = (package_dir / PACKAGE_FILE).relative_to(root)
    try:
        manifest = PackageManifest.model_validate_json((package_dir / PACKAGE_FILE).read_text(encoding="utf-8"))
    except ValidationError:
        return [f"{where}: must be JSON whose `dependencies` and `scripts` map names to strings"]
    problems: list[str] = []
    if SDK_PACKAGE not in manifest.dependencies:
        problems.append(f"{where}: its dependencies do not name {SDK_PACKAGE}")
    # Each word of the script read as a path, so `./generated/<method>/` names the same tree as `generated/<method>`, as it does to the gate.
    checked = {PurePosixPath(word).as_posix() for word in manifest.scripts.get(CODEGEN_CHECK_SCRIPT, "").split()}
    for tree in trees:
        tree_path = tree.directory.relative_to(package_dir).as_posix()
        if tree_path not in checked:
            problems.append(f"{where}: its `{CODEGEN_CHECK_SCRIPT}` script does not check {tree_path}, so nothing holds those types to their lock")
    return problems


def _read_tree(directory: Path) -> RecipeTree:
    recipe_dir = directory.parent.parent
    sidecar_path = directory / SIDECAR_FILE
    if not sidecar_path.is_file():
        return _unread_tree(recipe_dir=recipe_dir, directory=directory, problem="missing, so nothing says what these types were generated from")
    try:
        sidecar = Sidecar.model_validate_json(sidecar_path.read_text(encoding="utf-8"))
    except ValidationError:
        return _unread_tree(recipe_dir=recipe_dir, directory=directory, problem="must be JSON naming `method.method_ref` and `target`")
    return RecipeTree(recipe_dir=recipe_dir, directory=directory, method_ref=sidecar.method.method_ref, target=sidecar.target)


def _unread_tree(*, recipe_dir: Path, directory: Path, problem: str) -> RecipeTree:
    return RecipeTree(recipe_dir=recipe_dir, directory=directory, method_ref=None, target=None, sidecar_problem=problem)


def _is_skipped(path: Path, *, root: Path) -> bool:
    return any(part in _SKIPPED_DIRS for part in path.relative_to(root).parts)


def _script_block(path: Path) -> str | None:
    match = _SCRIPT_BLOCK.search(path.read_text(encoding="utf-8"))
    return match.group("body") if match else None


def _recipe_code(recipe_dir: Path) -> list[str]:
    """The text of every code file the recipe wrote itself: its generated types and installed packages left out."""
    return [
        path.read_text(encoding="utf-8")
        for path in sorted(recipe_dir.rglob("*"))
        if path.suffix in CODE_SUFFIXES and path.is_file() and not _is_own_generated_or_skipped(path, recipe_dir=recipe_dir)
    ]


def _is_own_generated_or_skipped(path: Path, *, recipe_dir: Path) -> bool:
    return _is_skipped(path, root=recipe_dir) or GENERATED_DIR in path.relative_to(recipe_dir).parts


def _names_address(code: str, *, address: str) -> bool:
    """Whether the code holds the address as a whole string literal: `@v0.1.1` does not name `@v0.1.10`, nor does a mention in prose."""
    return re.search(rf"""(["'`]){re.escape(address)}\1""", code) is not None


def _recipe_reads(recipe_dir: Path, *, target: str) -> bool:
    if target == TYPESCRIPT_TARGET:
        return (recipe_dir / "package.json").is_file()
    return any(_script_block(path) is not None for path in recipe_dir.glob("*.py"))
