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

The page snippets `make render` writes under `tests/snippets/` are code of the same kinds, a Python script per page and one TypeScript
package for them all, so the finders of trees, scripts and packages read them too, and `make check-recipe-types` type-checks them with
the recipes. The rules only a recipe needs stay with the recipes: its tree's address, the literal its code calls, the SDK its script
declares and the gate its package runs, since `make check-render` holds each snippet to its page instead.
"""

import os
import re
import subprocess
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from scripts.cookbook import SNIPPETS_DIR

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
    """One generated tree of a code recipe or a page snippet, and what its sidecar says it was generated from."""

    model_config = ConfigDict(frozen=True)

    recipe_dir: Path = Field(description="The directory holding the tree's `generated/`, where a Python script reading the tree is")
    directory: Path
    package_dir: Path | None = Field(
        default=None, description="The nearest directory at or above the tree holding a `package.json`, which type-checks a TypeScript tree"
    )
    method_ref: str | None
    target: str | None
    sidecar_problem: str | None = None


def find_trees(root: Path) -> list[RecipeTree]:
    """Every directory directly under a recipe's or a page snippet's `generated/`, with its sidecar read.

    A tree is found by where it is, not by the files it should hold, so a tree that lost its sidecar and its lock is still found and
    reported rather than skipped.
    """
    trees: list[RecipeTree] = []
    for code_root in _code_roots(root):
        tree_dirs: set[Path] = set()
        for generated_dir in code_root.rglob(GENERATED_DIR):
            if not generated_dir.is_dir() or _is_skipped(generated_dir, root=code_root):
                continue
            tree_dirs.update(child for child in generated_dir.iterdir() if child.is_dir() and child.name not in _SKIPPED_DIRS)
        trees.extend(_read_tree(directory, code_root=code_root) for directory in tree_dirs)
    return sorted(trees, key=lambda tree: tree.directory)


def python_scripts(root: Path) -> list[Path]:
    """Every Python script of a recipe or a page snippet: a `.py` file outside `generated/` declaring its dependencies inline for `uv run`."""
    return sorted(
        path
        for code_root in _code_roots(root)
        for path in code_root.rglob("*.py")
        if not _is_skipped(path, root=code_root) and GENERATED_DIR not in path.relative_to(code_root).parts and _script_block(path) is not None
    )


def typescript_packages(root: Path) -> list[Path]:
    """Every TypeScript recipe, and the page snippets' package: a directory holding a `package.json`, their installed packages left out."""
    return sorted(path.parent for code_root in _code_roots(root) for path in code_root.rglob(PACKAGE_FILE) if not _is_skipped(path, root=code_root))


def in_recipes(path: Path, *, root: Path) -> bool:
    """Whether a path is a recipe's, rather than a page snippet's, and so held to the rules only a recipe needs."""
    return path.is_relative_to(root / RECIPES_DIR)


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
    A page snippet's address is its page's, which `make check-addresses` validates at the page's tag, so its trees are left out.
    """
    named_in: dict[str, set[str]] = {}
    for tree in find_trees(root):
        if tree.method_ref is not None and in_recipes(tree.directory, root=root):
            named_in.setdefault(tree.method_ref, set()).add(tree.recipe_dir.relative_to(root).as_posix())
    for found in find_addresses(root):
        named_in.setdefault(found.address, set()).add(found.file.parent.relative_to(root).as_posix())
    return {address: sorted(recipes) for address, recipes in sorted(named_in.items())}


def recipe_problems(root: Path) -> list[str]:
    """What an offline reading finds wrong with the recipes, and with the page snippets' generated trees, one sentence each.

    It reads their generated trees, their Python scripts and TypeScript packages, the addresses they name, and their shell scripts. A page
    snippet's tree must have a sidecar and a target its code can read, but the rules only a recipe needs are not applied to it.
    """
    problems: list[str] = []
    trees = find_trees(root)
    for tree in trees:
        where = tree.directory.relative_to(root)
        if tree.method_ref is None or tree.target is None:
            problems.append(f"{where}/{SIDECAR_FILE}: {tree.sidecar_problem}")
            continue
        is_recipe = in_recipes(tree.directory, root=root)
        if is_recipe and not _PINNED_ADDRESS.match(tree.method_ref):
            problems.append(f"{where}/{SIDECAR_FILE}: {tree.method_ref!r} {_NOT_PINNED}")
        if tree.target not in TARGET_MARKERS:
            problems.append(f"{where}/{SIDECAR_FILE}: target {tree.target!r} is none of {', '.join(sorted(TARGET_MARKERS))}")
        elif not _tree_is_read(tree):
            # A TypeScript tree is read by the nearest package at or above it, a Python tree by a script beside its `generated/`.
            place = f"{tree.recipe_dir.relative_to(root)}{' or above it' if tree.target == TYPESCRIPT_TARGET else ''}"
            problems.append(f"{where}: target {tree.target} needs {TARGET_MARKERS[tree.target]} in {place}")
        if is_recipe and not any(_names_address(code, address=tree.method_ref) for code in _recipe_code(_code_dir(tree))):
            problems.append(
                f"{where}: the recipe's code never names {tree.method_ref} as a string, so its types may describe another method than it calls"
            )
    for script in python_scripts(root):
        block = _script_block(script) or ""
        if in_recipes(script, root=root) and SDK_DEPENDENCY not in block:
            problems.append(f"{script.relative_to(root)}: its inline dependencies do not name {SDK_DEPENDENCY}")
    for package_dir in typescript_packages(root):
        if not in_recipes(package_dir, root=root):
            continue
        package_trees = [tree for tree in trees if tree.package_dir == package_dir and tree.target == TYPESCRIPT_TARGET]
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
    # A recipe package is a code recipe, which carries generated types, so it needs the gate over them even when no tree is found: `make
    # check-recipe-types` runs the script only if it is present, since the snippets' package has none.
    if CODEGEN_CHECK_SCRIPT not in manifest.scripts:
        problems.append(f"{where}: it has no `{CODEGEN_CHECK_SCRIPT}` script, the gate over its generated types")
    # Each word of the script read as a path, so `./generated/<method>/` names the same tree as `generated/<method>`, as it does to the gate.
    checked = {PurePosixPath(word).as_posix() for word in manifest.scripts.get(CODEGEN_CHECK_SCRIPT, "").split()}
    for tree in trees:
        tree_path = tree.directory.relative_to(package_dir).as_posix()
        if tree_path not in checked:
            problems.append(f"{where}: its `{CODEGEN_CHECK_SCRIPT}` script does not check {tree_path}, so nothing holds those types to their lock")
    return problems


def _read_tree(directory: Path, *, code_root: Path) -> RecipeTree:
    recipe_dir = directory.parent.parent
    package_dir = _nearest_package(directory, code_root=code_root)
    sidecar_path = directory / SIDECAR_FILE
    if not sidecar_path.is_file():
        problem = "missing, so nothing says what these types were generated from"
        return _unread_tree(recipe_dir=recipe_dir, directory=directory, package_dir=package_dir, problem=problem)
    try:
        sidecar = Sidecar.model_validate_json(sidecar_path.read_text(encoding="utf-8"))
    except ValidationError:
        problem = "must be JSON naming `method.method_ref` and `target`"
        return _unread_tree(recipe_dir=recipe_dir, directory=directory, package_dir=package_dir, problem=problem)
    return RecipeTree(
        recipe_dir=recipe_dir, directory=directory, package_dir=package_dir, method_ref=sidecar.method.method_ref, target=sidecar.target
    )


def _unread_tree(*, recipe_dir: Path, directory: Path, package_dir: Path | None, problem: str) -> RecipeTree:
    return RecipeTree(recipe_dir=recipe_dir, directory=directory, package_dir=package_dir, method_ref=None, target=None, sidecar_problem=problem)


def _nearest_package(directory: Path, *, code_root: Path) -> Path | None:
    """The nearest directory at or above `directory`, and within `code_root`, holding a `package.json`: the package `tsc` reads it in.

    A recipe's package holds its trees in its own `generated/`, and the page snippets' one package holds the trees of every snippet below it.
    """
    for candidate in [directory, *directory.parents]:
        if not candidate.is_relative_to(code_root):
            return None
        if (candidate / PACKAGE_FILE).is_file():
            return candidate
    return None


def _code_roots(root: Path) -> list[Path]:
    """The directories holding code the tooling reads: the recipes, and the page snippets `make render` writes as files."""
    return [code_root for code_root in (root / RECIPES_DIR, root / SNIPPETS_DIR) if code_root.is_dir()]


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


def _code_dir(tree: RecipeTree) -> Path:
    """Where the code reading a tree is: anywhere in a TypeScript tree's package, and beside a Python tree's `generated/`."""
    if tree.target == TYPESCRIPT_TARGET and tree.package_dir is not None:
        return tree.package_dir
    return tree.recipe_dir


def _tree_is_read(tree: RecipeTree) -> bool:
    """Whether checked code reads the tree: a package at or above a TypeScript tree, or a script beside a Python tree's `generated/`."""
    if tree.target == TYPESCRIPT_TARGET:
        return tree.package_dir is not None
    return any(_script_block(path) is not None for path in tree.recipe_dir.glob("*.py"))
