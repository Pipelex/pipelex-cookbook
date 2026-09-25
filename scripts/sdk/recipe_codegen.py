# /// script
# requires-python = ">=3.11"
# dependencies = ["pipelex-sdk==0.12.0", "mthds>=0.15", "pydantic>=2.10.6"]
# ///
"""Generate and check the typed trees the code recipes and the page snippets carry.

Every code recipe keeps the types of the method it calls in `generated/<method>/`: the stamped artifacts, their
`codegen.lock`, and a `sources.json` naming the pinned address and the codegen target they come from. Each page
snippet under `tests/snippets/` keeps its method's types the same way, except that its `sources.json`, which
`make render` writes, names the `.mthds` files of the method's package instead of an address: a page names the last
release's tag, which does not hold a method added since. This script is the one place the cookbook reaches
`pipelex-sdk` for them, and it runs in an environment of its own (`uv run --script`), so that every tree is written
and checked with the exact SDK release pinned above. It runs from the repository root, as the Makefile runs it,
since a sidecar names its files by their paths from there:

- `generate <tree>...` asks the hosted API for each tree's types (`POST /v1/codegen` with the address, or with the
  files' contents) and writes the answer verbatim with `write_codegen_tree`, which is what keeps the offline check
  able to trust it. It needs `PIPELEX_API_KEY`, and `make refresh` runs it.
- `check <tree>...` is the offline drift check, `run_codegen_check`: pure hashing of each tree against its lock, with
  no key, and no network once the SDK is installed. CI runs it.
- `verify <tree>...` asks the hosted API what each tree's address or files make today and compares that crate's
  fingerprint with the one its lock records, which the offline check never asks: a sidecar pointed at another
  address, or a bundle edited, without a regeneration passes the offline check and fails this one. It needs
  `PIPELEX_API_KEY`, and `make check-hosted` runs it.

Exit codes: 0 when every tree is written, current or verified, 1 when one drifted, could not be generated or does not
come from what its sidecar names, 2 when the arguments or a sidecar cannot be read.
"""

import asyncio
import sys
from pathlib import Path, PurePosixPath

from mthds.protocol.exceptions import PipelineRequestError
from pipelex_sdk.client import PipelexAPIClient
from pipelex_sdk.codegen_check import run_codegen_check
from pipelex_sdk.codegen_writer import write_codegen_tree
from pipelex_sdk.crate_models import CodegenRequest, CodegenTarget, CodegenValidReport, CrateInvalidReport, MthdsFileItem
from pipelex_sdk.errors import CodegenError, CodegenLockError
from pydantic import BaseModel, ValidationError

SIDECAR_FILE = "sources.json"
PYTHON_TARGET = "python-pydantic"
KNOWN_TARGETS: dict[str, CodegenTarget] = {"python-pydantic": "python-pydantic", "ts-zod": "ts-zod"}
# A sidecar naming files names `.mthds` files of the cookbook's packages, by their paths from the repository root.
METHODS_DIR = "methods"
BUNDLE_SUFFIX = ".mthds"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_UNREADABLE = 2


class SidecarError(Exception):
    """A tree's `sources.json` is missing or malformed, or names neither a pinned address nor the files of a package."""


class SidecarMethod(BaseModel):
    method_ref: str | None = None
    files: list[str] | None = None


class SidecarFile(BaseModel):
    method: SidecarMethod
    target: str


class Sidecar(BaseModel):
    """What a tree's `sources.json` says it was generated from: a pinned address, or the `.mthds` files of a package."""

    method_ref: str | None = None
    files: list[str] | None = None
    target: CodegenTarget

    @property
    def origin(self) -> str:
        """The address, or the files, as a report names what the tree comes from."""
        return self.method_ref or " and ".join(self.files or [])

    def codegen_request(self) -> CodegenRequest:
        """The `POST /v1/codegen` request for the tree: its address, or the contents of its files, each labelled with its path.

        Raises:
            OSError: A file cannot be read.
            UnicodeDecodeError: A file is not UTF-8.
        """
        if self.files is not None:
            files = [MthdsFileItem(content=Path(file).read_text(encoding="utf-8"), source=file) for file in self.files]
            return CodegenRequest(files=files, kind="types", target=self.target)
        return CodegenRequest(method_ref=self.method_ref, kind="types", target=self.target)


def read_sidecar(tree: Path) -> Sidecar:
    """Read what a tree is generated from, and its target.

    A code recipe's sidecar names the address its code calls, as `method.method_ref`. A page snippet's names the `.mthds`
    files of its method's package, as `method.files`, by their paths from the repository root, where this script runs.

    Raises:
        SidecarError: The sidecar is missing, is not the expected JSON, names both an address and files or neither, names
            an unknown target, names an address without a tag, which would float with the default branch while the
            committed types stay put, or names a file that is not a `.mthds` file of a package under `methods/`.
    """
    sidecar_path = tree / SIDECAR_FILE
    try:
        sidecar = SidecarFile.model_validate_json(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as exc:
        msg = f"{sidecar_path}: cannot be read as JSON naming `target` and `method.method_ref` or `method.files` ({exc})"
        raise SidecarError(msg) from exc
    method_ref, files = sidecar.method.method_ref, sidecar.method.files
    if (method_ref is None) == (files is None):
        msg = (
            f"{sidecar_path}: `method` must name exactly one of `method_ref`, an address pinned to a tag, "
            f"and `files`, the {BUNDLE_SUFFIX} files of a package under {METHODS_DIR}/"
        )
        raise SidecarError(msg)
    if method_ref is not None and "@" not in method_ref:
        msg = f"{sidecar_path}: `method.method_ref` must be an address pinned to a tag, such as github.com/<owner>/<repo>/<name>@v1.2.3"
        raise SidecarError(msg)
    if files is not None:
        problem = files_problem(files)
        if problem is not None:
            msg = f"{sidecar_path}: {problem}"
            raise SidecarError(msg)
    target = KNOWN_TARGETS.get(sidecar.target)
    if target is None:
        msg = f"{sidecar_path}: `target` must be one of {', '.join(sorted(KNOWN_TARGETS))}"
        raise SidecarError(msg)
    return Sidecar(method_ref=method_ref, files=files, target=target)


def files_problem(files: list[str]) -> str | None:
    """What is wrong with the files a sidecar names, or None: each must be a `.mthds` file under `methods/`, named from the repository root."""
    if not files:
        return "`method.files` names no file"
    for file in files:
        path = PurePosixPath(file)
        if path.is_absolute() or ".." in path.parts or path.parts[:1] != (METHODS_DIR,) or path.suffix != BUNDLE_SUFFIX:
            return f"`method.files` names {file!r}, which is not the path of a {BUNDLE_SUFFIX} file under {METHODS_DIR}/ from the repository root"
        if not Path(file).is_file():
            return f"`method.files` names {file}, which is not a file here: run this script from the repository root"
    return None


def ensure_python_packages(tree: Path) -> None:
    """Give a Python tree the two `__init__.py` files that make it importable as `generated.<method>`.

    Codegen never emits them and they carry no stamp, so the offline check neither tracks them nor reports them as
    orphans; an existing one is left as it is.
    """
    for package_dir in (tree.parent, tree):
        init_file = package_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")


def read_sidecars(trees: list[Path]) -> dict[Path, Sidecar] | None:
    """Every tree's sidecar, or None once one cannot be read, which has been reported."""
    sidecars: dict[Path, Sidecar] = {}
    for tree in trees:
        try:
            sidecars[tree] = read_sidecar(tree)
        except SidecarError as exc:
            sys.stderr.write(f"✗ {exc}\n")
            return None
    return sidecars


async def codegen_for(client: PipelexAPIClient, *, tree: Path, sidecar: Sidecar) -> CodegenValidReport | None:
    """The hosted API's types for what a tree's sidecar names, or None once a failure has been reported.

    The API refuses an address that does not resolve, or files it cannot read as a method (`ApiResponseError`), and
    cannot always be reached (`ApiUnreachableError`), both request errors; a method that does not validate comes back
    as an invalid report instead.
    """
    try:
        request = sidecar.codegen_request()
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write(f"✗ {tree}: {sidecar.origin} could not be read ({exc})\n")
        return None
    try:
        response = await client.codegen(request)
    except PipelineRequestError as exc:
        sys.stderr.write(f"✗ {tree}: {sidecar.origin} could not be resolved: {exc}\n")
        return None
    if isinstance(response, CrateInvalidReport):
        errors = "; ".join(item.message for item in response.validation_errors)
        sys.stderr.write(f"✗ {tree}: {sidecar.origin} does not validate: {errors}\n")
        return None
    return response


async def generate(trees: list[Path]) -> int:
    """Regenerate every tree from what its sidecar names, reporting each; one failure does not stop the others."""
    sidecars = read_sidecars(trees)
    if sidecars is None:
        return EXIT_UNREADABLE
    exit_code = EXIT_OK
    async with PipelexAPIClient() as client:
        for tree, sidecar in sidecars.items():
            response = await codegen_for(client, tree=tree, sidecar=sidecar)
            if response is None:
                exit_code = EXIT_FAILED
                continue
            try:
                written = write_codegen_tree(response, output_dir=tree)
            except (CodegenError, OSError) as exc:
                sys.stderr.write(f"✗ {tree}: the types could not be written ({exc})\n")
                exit_code = EXIT_FAILED
                continue
            if sidecar.target == PYTHON_TARGET:
                ensure_python_packages(tree)
            changed = len(written.written) + len(written.removed) + int(written.lock_written)
            verb = f"{changed} file(s) written or removed" if changed else "unchanged"
            sys.stdout.write(f"✓ {tree} — {sidecar.origin} ({sidecar.target}): {verb}\n")
    return exit_code


def check(trees: list[Path]) -> int:
    """Check every tree against its lock, offline, and report each drift the SDK names."""
    exit_code = EXIT_OK
    for tree in trees:
        try:
            read_sidecar(tree)
            report = run_codegen_check(root=tree)
        except (SidecarError, CodegenLockError) as exc:
            sys.stderr.write(f"✗ {tree}: no verdict ({exc})\n")
            exit_code = max(exit_code, EXIT_UNREADABLE)
            continue
        if not report.lock_found:
            sys.stderr.write(f"✗ {tree}: no codegen.lock, so nothing vouches for these types; run `make refresh`\n")
            exit_code = max(exit_code, EXIT_FAILED)
        elif report.drifts:
            for drift in report.drifts:
                sys.stderr.write(f"✗ {tree}/{drift.path}: {drift.category} — {drift.detail}\n")
            exit_code = max(exit_code, EXIT_FAILED)
        else:
            sys.stdout.write(f"✓ {tree} is current with its lock\n")
    return exit_code


async def verify(trees: list[Path]) -> int:
    """Check that every tree's lock records the crate codegen makes today of what its sidecar names.

    Each tree is reported, and one failure does not stop the others.
    """
    sidecars = read_sidecars(trees)
    if sidecars is None:
        return EXIT_UNREADABLE
    exit_code = EXIT_OK
    async with PipelexAPIClient() as client:
        for tree, sidecar in sidecars.items():
            try:
                locked = run_codegen_check(root=tree).crate_fingerprint
            except CodegenLockError as exc:
                sys.stderr.write(f"✗ {tree}: no verdict ({exc})\n")
                exit_code = max(exit_code, EXIT_UNREADABLE)
                continue
            if locked is None:
                sys.stderr.write(f"✗ {tree}: no codegen.lock, so nothing records what these types were generated from; run `make refresh`\n")
                exit_code = max(exit_code, EXIT_FAILED)
                continue
            response = await codegen_for(client, tree=tree, sidecar=sidecar)
            if response is None:
                exit_code = max(exit_code, EXIT_FAILED)
            elif locked != response.crate_fingerprint:
                sys.stderr.write(
                    f"✗ {tree}: its codegen.lock records crate {locked}, while codegen makes crate {response.crate_fingerprint} "
                    f"of {sidecar.origin} today; run `make refresh`\n"
                )
                exit_code = max(exit_code, EXIT_FAILED)
            else:
                sys.stdout.write(f"✓ {tree} was generated from {sidecar.origin} as codegen reads it today\n")
    return exit_code


def main(argv: list[str]) -> int:
    commands = {"generate", "check", "verify"}
    if len(argv) < 2 or argv[0] not in commands:
        sys.stderr.write(f"usage: recipe_codegen.py {'|'.join(sorted(commands))} <tree>...\n")
        return EXIT_UNREADABLE
    command, trees = argv[0], [Path(argument) for argument in argv[1:]]
    if command == "generate":
        return asyncio.run(generate(trees))
    if command == "verify":
        return asyncio.run(verify(trees))
    return check(trees)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
