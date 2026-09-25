"""What a package's `.mthds` files declare about its main pipe, read offline.

`contract.json` records what production says the main pipe takes and returns, and the page's "Returns" line and its snippets' typed read are
rendered from it, while the snippets' generated types come from the package's `.mthds` files. Loading the cookbook holds the two together: the
snapshot's pipe, output concept and multiplicity must be what the files declare, so a bundle changed without `make refresh` fails every check that
loads the cookbook, CI's included, rather than only the keyed ones. A bare concept reference resolves as the MTHDS standard resolves one: a native
concept first, then a concept of the bundle's own domain, declared in any of the package's files.
"""

import re
import tomllib
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict

from scripts.exceptions import CookbookLayoutError

# The native concepts of the MTHDS standard, pinned at MTHDS 2.0.0 (mthds.ai, "Native Concepts"): a bare reference to one of these codes names it.
NATIVE_CONCEPTS = frozenset(
    {
        "Anything",
        "Composite",
        "Date",
        "Document",
        "Dynamic",
        "Html",
        "Image",
        "JSON",
        "Number",
        "Page",
        "SearchResult",
        "Text",
        "TextAndImages",
        "Time",
        "YesNo",
    }
)
NATIVE_DOMAIN = "native"
# A pipe's output: a concept reference, then an optional multiplicity (`[]`, or `[N]`) or an optional presence marker (`?`).
_OUTPUT_PATTERN = re.compile(r"^(?P<ref>[^\[\]?!]+?)(?:\[(?P<count>\d*)\]|(?P<optional>\?))?$")


class DeclaredOutput(BaseModel):
    """The main pipe and its output as the package's files declare them, in the shape `contract.json` records them."""

    model_config = ConfigDict(frozen=True)

    pipe: str
    concept: str
    multiplicity: str
    item_count: int | None = None


class _Bundle(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    domain: str
    concepts: frozenset[str]
    pipes: dict[str, dict[str, Any]]


def declared_main_output(*, bundle_paths: list[Path], main_pipe: str) -> DeclaredOutput:
    """Read the main pipe's domain-qualified reference and its output from the package's `.mthds` files.

    Raises:
        CookbookLayoutError: A file does not parse, no file or several declare the main pipe, or its output is not a concept this package or the
            standard declares.
    """
    bundles = [_read_bundle(path) for path in bundle_paths]
    declaring = [bundle for bundle in bundles if main_pipe in bundle.pipes]
    if len(declaring) != 1:
        msg = f"the manifest's main_pipe `{main_pipe}` is declared in {len(declaring)} of the package's .mthds files, where it must be in exactly one"
        raise CookbookLayoutError(msg)
    bundle = declaring[0]
    output = bundle.pipes[main_pipe].get("output")
    if not isinstance(output, str):
        msg = f"{bundle.path}: the main pipe `{main_pipe}` declares no output"
        raise CookbookLayoutError(msg)
    match = _OUTPUT_PATTERN.match(output.strip())
    if match is None:
        msg = f"{bundle.path}: the main pipe `{main_pipe}` declares the output `{output}`, which is not a concept reference"
        raise CookbookLayoutError(msg)
    concept = _resolve_concept(reference=match["ref"].strip(), bundle=bundle, bundles=bundles, main_pipe=main_pipe)
    count = match["count"]
    if count is None or count == "1":
        multiplicity, item_count = "single", None
    elif count == "":
        multiplicity, item_count = "variable", None
    else:
        multiplicity, item_count = "fixed", int(count)
    return DeclaredOutput(pipe=f"{bundle.domain}.{main_pipe}", concept=concept, multiplicity=multiplicity, item_count=item_count)


def _resolve_concept(*, reference: str, bundle: _Bundle, bundles: list[_Bundle], main_pipe: str) -> str:
    if "->" in reference:
        msg = (
            f"{bundle.path}: the main pipe `{main_pipe}` returns `{reference}`, a concept of another package, "
            "while a cookbook method returns a concept of its own package or a native one"
        )
        raise CookbookLayoutError(msg)
    if "." in reference:
        return reference
    if reference in NATIVE_CONCEPTS:
        return f"{NATIVE_DOMAIN}.{reference}"
    if any(other.domain == bundle.domain and reference in other.concepts for other in bundles):
        return f"{bundle.domain}.{reference}"
    msg = (
        f"{bundle.path}: the main pipe `{main_pipe}` returns `{reference}`, which is neither a native concept nor one of the domain `{bundle.domain}`"
    )
    raise CookbookLayoutError(msg)


def _read_bundle(path: Path) -> _Bundle:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        msg = f"{path} does not parse: {exc}"
        raise CookbookLayoutError(msg) from exc
    domain = data.get("domain")
    if not isinstance(domain, str):
        msg = f"{path} declares no domain"
        raise CookbookLayoutError(msg)
    concepts = data.get("concept")
    pipes = data.get("pipe")
    return _Bundle(
        path=path,
        domain=domain,
        concepts=frozenset(cast("dict[str, Any]", concepts)) if isinstance(concepts, dict) else frozenset(),
        pipes=cast("dict[str, dict[str, Any]]", pipes) if isinstance(pipes, dict) else {},
    )
