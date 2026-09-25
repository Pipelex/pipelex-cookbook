# /// script
# requires-python = ">=3.11"
# dependencies = ["pipelex-sdk==0.12.0"]
# ///
"""Generate and check the typed trees the code recipes carry.

Every code recipe keeps the types of the method it calls in `generated/<method>/`: the stamped artifacts, their
`codegen.lock`, and a `sources.json` naming the pinned address and the codegen target they come from. This script is
the one place the cookbook reaches `pipelex-sdk` for them, and it runs in an environment of its own
(`uv run --script`), since the SDK and the runtime the cookbook still pins cannot be installed side by side:

- `generate <tree>...` asks the hosted API for each tree's types (`POST /v1/codegen` with the address) and writes the
  answer verbatim with `write_codegen_tree`, which is what keeps the offline check able to trust it. It needs
  `PIPELEX_API_KEY`, and `make refresh` runs it.
- `check <tree>...` is the offline drift check, `run_codegen_check`: pure hashing of each tree against its lock, with
  no key and no network. CI runs it.

Exit codes: 0 when every tree is written or current, 1 when one drifted or could not be generated, 2 when the
arguments or a sidecar cannot be read.
"""

import asyncio
import sys
from pathlib import Path

from pipelex_sdk.client import PipelexAPIClient
from pipelex_sdk.codegen_check import run_codegen_check
from pipelex_sdk.codegen_writer import write_codegen_tree
from pipelex_sdk.crate_models import CodegenRequest, CodegenTarget, CodegenValidReport
from pipelex_sdk.errors import CodegenError, CodegenLockError
from pydantic import BaseModel, ValidationError

SIDECAR_FILE = "sources.json"
PYTHON_TARGET = "python-pydantic"
KNOWN_TARGETS: dict[str, CodegenTarget] = {"python-pydantic": "python-pydantic", "ts-zod": "ts-zod"}

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_UNREADABLE = 2


class SidecarError(Exception):
    """A tree's `sources.json` is missing, malformed, or names no pinned address."""


class SidecarMethod(BaseModel):
    method_ref: str


class SidecarFile(BaseModel):
    method: SidecarMethod
    target: str


class Sidecar(BaseModel):
    """What a tree's `sources.json` says it was generated from."""

    method_ref: str
    target: CodegenTarget


def read_sidecar(tree: Path) -> Sidecar:
    """Read the address and the target a tree is generated from.

    Raises:
        SidecarError: The sidecar is missing, is not the expected JSON, names an unknown target, or names an address
            without a tag, which would float with the default branch while the committed types stay put.
    """
    sidecar_path = tree / SIDECAR_FILE
    try:
        sidecar = SidecarFile.model_validate_json(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as exc:
        msg = f"{sidecar_path}: cannot be read as JSON naming `method.method_ref` and `target` ({exc})"
        raise SidecarError(msg) from exc
    if "@" not in sidecar.method.method_ref:
        msg = f"{sidecar_path}: `method.method_ref` must be an address pinned to a tag, such as github.com/<owner>/<repo>/<name>@v1.2.3"
        raise SidecarError(msg)
    target = KNOWN_TARGETS.get(sidecar.target)
    if target is None:
        msg = f"{sidecar_path}: `target` must be one of {', '.join(sorted(KNOWN_TARGETS))}"
        raise SidecarError(msg)
    return Sidecar(method_ref=sidecar.method.method_ref, target=target)


def ensure_python_packages(tree: Path) -> None:
    """Give a Python tree the two `__init__.py` files that make it importable as `generated.<method>`.

    Codegen never emits them and they carry no stamp, so the offline check neither tracks them nor reports them as
    orphans; an existing one is left as it is.
    """
    for package_dir in (tree.parent, tree):
        init_file = package_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")


async def generate(trees: list[Path]) -> int:
    """Regenerate every tree from its sidecar's address, reporting each; one failure does not stop the others."""
    sidecars: dict[Path, Sidecar] = {}
    for tree in trees:
        try:
            sidecars[tree] = read_sidecar(tree)
        except SidecarError as exc:
            sys.stderr.write(f"✗ {exc}\n")
            return EXIT_UNREADABLE
    exit_code = EXIT_OK
    async with PipelexAPIClient() as client:
        for tree, sidecar in sidecars.items():
            request = CodegenRequest(method_ref=sidecar.method_ref, kind="types", target=sidecar.target)
            response = await client.codegen(request)
            if not isinstance(response, CodegenValidReport):
                errors = "; ".join(item.message for item in response.validation_errors)
                sys.stderr.write(f"✗ {tree}: {sidecar.method_ref} does not resolve: {errors}\n")
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
            sys.stdout.write(f"✓ {tree} — {sidecar.method_ref} ({sidecar.target}): {verb}\n")
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


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in {"generate", "check"}:
        sys.stderr.write("usage: recipe_codegen.py generate|check <tree>...\n")
        return EXIT_UNREADABLE
    command, trees = argv[0], [Path(argument) for argument in argv[1:]]
    if command == "generate":
        return asyncio.run(generate(trees))
    return check(trees)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
