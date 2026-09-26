"""The command line behind the Makefile's cookbook targets: `python -m scripts <command>`.

Offline, needing no key: `render`, `check-render`, `check-lockstep`, `check-links` (which only fetches public sample URLs), `check-recipes`, and
`recipe-trees`, `recipe-scripts`, `recipe-packages` and `recipe-shell-scripts`, which list what the Makefile hands the SDK script, the type
checkers and shellcheck: the recipes' code, and the page snippets `render` writes under `tests/snippets/`. `previews` renders the first-page
preview of every PDF document sample whose source-and-licence record is written, with no key and no network. `refresh-library` and
`check-library` need no key either: each downloads the method library's tarball at the tag `cookbook.toml` pins, the first to write
`library.json` and the second to check that it is what that tarball holds.
Keyed, calling production with `PIPELEX_API_KEY`: `refresh`, `check-methods`, `check-addresses`, and `snapshot <name>`, the one command here
that spends inference credit: it runs a method once on production on its sample and writes its output snapshot.
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from scripts.checks import (
    check_links,
    http_status,
    lockstep_problems,
    orphan_snippet_dirs,
    sample_problems,
    snapshot_problems,
    stale_pages,
    stale_snapshots,
)
from scripts.cookbook import Cookbook, load_cookbook
from scripts.exceptions import CookbookError
from scripts.hosted import (
    AddressState,
    AddressVerdict,
    HostedClient,
    check_address,
    check_pinned_method_ref,
    client_from_env,
    validate_bundle_file,
    validate_packages,
)
from scripts.library import LIBRARY_FILE, download, fetch_library, snapshot_is_current
from scripts.recipes import (
    find_addresses,
    find_trees,
    in_recipes,
    python_scripts,
    recipe_addresses,
    recipe_problems,
    shell_scripts,
    typescript_packages,
)
from scripts.render import build_library_context, render_all, render_pages
from scripts.snapshot import SNAPSHOT_FILE, document_samples, preview_path, read_snapshot, take_snapshot, unrecorded_documents, write_previews
from scripts.tutorial import tutorial_bundles

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR_NAME = "templates"
SNAPSHOT_COMMAND = "snapshot"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts", description="Render the cookbook's method pages and check them.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="The cookbook's root directory (default: this repository)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    commands: dict[str, Callable[[Cookbook], int]] = {
        "render": _render,
        "previews": _previews,
        "check-render": _check_render,
        "check-lockstep": _check_lockstep,
        "check-links": _check_links,
        "check-library": _check_library,
        "refresh": _refresh,
        "refresh-library": _refresh_library,
        "check-methods": _check_methods,
        "check-addresses": _check_addresses,
        "check-recipes": _check_recipes,
        "recipe-trees": _recipe_trees,
        "recipe-scripts": _recipe_scripts,
        "recipe-packages": _recipe_packages,
        "recipe-shell-scripts": _recipe_shell_scripts,
    }
    helps = {
        "render": (
            "Write every methods/<name>/README.md from its package and cookbook.toml, its snippet files under tests/snippets/<name>/, "
            "and the front page's two lists, of the methods and of the library's methods"
        ),
        "previews": (
            "Render the first-page preview of every PDF document sample kept under assets/ whose source-and-licence record is written, "
            "beside it as <stem>.preview.png, with no key and no run"
        ),
        "check-render": (
            "Fail when a committed page, snippet file or either of the front page's lists differs from a fresh render, "
            "when a snippet directory belongs to no method, when a sample input has no source-and-licence record or a PDF document sample "
            "no preview, or when a method's output snapshot is missing or out of step with its contract, its sample or its files"
        ),
        "check-lockstep": "Fail when a manifest's version is not the cookbook's",
        "check-links": "Fetch every sample URL in the packages, and every raw URL on the pages and in the recipes",
        "check-library": "Fail when library.json differs from a fresh snapshot of the library's tarball at the tag cookbook.toml pins",
        "refresh": "Validate every package on production and write its contract.json (needs PIPELEX_API_KEY)",
        "refresh-library": "Take the method library's snapshot, library.json, from its tarball at the tag cookbook.toml pins",
        "check-methods": (
            "Validate every package on production from its files, and check its contract snapshot, "
            "then every tutorial bundle from its file (needs PIPELEX_API_KEY)"
        ),
        "check-addresses": (
            "Validate every address on production: each page's at its tag, each recipe's as it pins it, "
            "and each library method's the front page lists (needs PIPELEX_API_KEY)"
        ),
        "check-recipes": (
            "Fail when a recipe's generated tree names no pinned address, or one its code does not call as a string literal, "
            "when a recipe names an address without a release tag, or when a recipe's shell script does not parse"
        ),
        "recipe-trees": "Print every generated tree of a recipe or a page snippet, one directory per line",
        "recipe-scripts": "Print every Python script of a recipe or a page snippet, one per line",
        "recipe-packages": "Print every TypeScript recipe package, and the page snippets' package, one directory per line",
        "recipe-shell-scripts": "Print every shell script of a recipe, one per line",
    }
    for command_name in commands:
        subparsers.add_parser(command_name, help=helps[command_name])
    snapshot_parser = subparsers.add_parser(
        SNAPSHOT_COMMAND,
        help=(
            "Run one method once on production on its sample and write its output snapshot, methods/<name>/output.json, "
            "and the previews of its PDF document samples (needs PIPELEX_API_KEY, and spends inference credit)"
        ),
    )
    snapshot_parser.add_argument("method", help="The method's name, its directory under methods/")
    arguments = parser.parse_args(argv)
    root = Path(arguments.root).resolve()
    try:
        # `refresh` and `refresh-library` rewrite what they would otherwise load, so each loads without it and recovers from a stale one.
        cookbook = load_cookbook(
            root,
            read_contracts=arguments.command not in {"refresh", "refresh-library"},
            read_library=arguments.command != "refresh-library",
        )
        if arguments.command == SNAPSHOT_COMMAND:
            return _snapshot(cookbook, name=str(arguments.method))
        return commands[arguments.command](cookbook)
    except CookbookError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1


def _templates_dir(cookbook: Cookbook) -> Path:
    return cookbook.root / TEMPLATES_DIR_NAME


def _render(cookbook: Cookbook) -> int:
    rendered = render_all(cookbook=cookbook, templates_dir=_templates_dir(cookbook))
    stale = set(stale_pages(cookbook=cookbook, rendered=rendered))
    for page_path, contents in rendered.items():
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(contents, encoding="utf-8")
        relative = page_path.relative_to(cookbook.root)
        print(f"{'✎ rewrote' if relative in stale else '· unchanged'} {relative}")
    orphans = orphan_snippet_dirs(cookbook)
    _print_orphans(orphans)
    for package in cookbook.packages:
        if read_snapshot(package) is None:
            print(
                f'· {package.directory.relative_to(cookbook.root)} has no {SNAPSHOT_FILE} yet: its page has no "What you get" '
                f"until `make snapshot METHOD={package.name}`, and `make check-render` fails on it"
            )
    return 1 if orphans else 0


def _previews(cookbook: Cookbook) -> int:
    for package in cookbook.packages:
        written = set(write_previews(cookbook=cookbook, package=package))
        for document in document_samples(cookbook=cookbook, package=package):
            preview = preview_path(document).relative_to(cookbook.root)
            print(f"{'✎ rendered' if preview_path(document) in written else '· unchanged'} {preview}")
        for document in unrecorded_documents(cookbook=cookbook, package=package):
            print(
                f"· {document.relative_to(cookbook.root)} gets no preview: its sample has no source-and-licence record "
                f"under [methods.{package.name}.samples] in cookbook.toml"
            )
    return 0


def _check_render(cookbook: Cookbook) -> int:
    rendered = render_all(cookbook=cookbook, templates_dir=_templates_dir(cookbook))
    stale = stale_pages(cookbook=cookbook, rendered=rendered)
    orphans = orphan_snippet_dirs(cookbook)
    for relative in stale:
        print(f"✗ {relative} differs from a fresh render")
    if stale:
        print("Pages, their snippet files and the front page's lists are generated: run `make render` and commit what it writes, never edit them.")
    _print_orphans(orphans)
    shown = sample_problems(cookbook) + snapshot_problems(cookbook)
    for problem in shown:
        print(f"✗ {problem}")
    for warning in stale_snapshots(cookbook):
        print(f"! {warning}")
    if stale or orphans or shown:
        return 1
    print(
        f"✓ {len(cookbook.packages)} method page(s), their snippet files and the front page's lists of methods match a fresh render at "
        f"{cookbook.tag}, the library's at {cookbook.settings.library.tag}, and every page's sample and output snapshot are in place"
    )
    return 0


def _snapshot(cookbook: Cookbook, *, name: str) -> int:
    matches = [package for package in cookbook.packages if package.name == name]
    if not matches:
        print(f"✗ no method is named `{name}`: the methods are {', '.join(package.name for package in cookbook.packages)}")
        return 1
    [package] = matches
    taken = take_snapshot(client=client_from_env(), cookbook=cookbook, package=package)
    for preview in taken.previews:
        print(f"✎ rendered the preview {preview.relative_to(cookbook.root)}")
    package_dir = package.directory.relative_to(cookbook.root)
    print(f"✎ wrote {package_dir}/{SNAPSHOT_FILE} from {taken.run.summary()}")
    for relative, entry in taken.snapshot.files.items():
        print(f"✎ copied {package_dir}/{relative}{', downscaled' if entry.resized else ''}")
    print("Keep the run id, the cost and the duration in the example's working record, never in this repository, then run `make render`.")
    return 0


def _print_orphans(orphans: list[Path]) -> None:
    for relative in orphans:
        print(f"✗ {relative}/ holds the snippets of no method under methods/: delete it, since `make render` never does")


def _check_lockstep(cookbook: Cookbook) -> int:
    problems = lockstep_problems(cookbook)
    for problem in problems:
        print(f"✗ {problem}")
    if problems:
        print("Versions are lockstep: every manifest carries the cookbook's version from pyproject.toml.")
        return 1
    print(f"✓ every manifest carries the cookbook's version, {cookbook.version}")
    return 0


def _check_links(cookbook: Cookbook) -> int:
    rendered = render_pages(cookbook=cookbook, templates_dir=_templates_dir(cookbook))
    verdicts = check_links(cookbook=cookbook, rendered=rendered, fetch_status=http_status)
    for verdict in verdicts:
        print(f"{'✓' if verdict.ok else '✗'} {verdict.url} — {verdict.note} (in {', '.join(verdict.found_in)})")
    broken = [verdict for verdict in verdicts if not verdict.ok]
    if broken:
        print(f"{len(broken)} broken link(s)")
        return 1
    print(f"✓ {len(verdicts)} link(s) checked")
    return 0


def _check_library(cookbook: Cookbook) -> int:
    settings = cookbook.settings.library
    snapshot = cookbook.library
    if snapshot is not None and snapshot_is_current(snapshot, settings, fetch=download):
        print(f"✓ {LIBRARY_FILE} is the snapshot of {settings.repository} at {settings.tag}")
        return 0
    print(f"✗ {LIBRARY_FILE} differs from a fresh snapshot of {settings.repository} at {settings.tag}: run `make refresh-library`, never edit it")
    return 1


def _refresh(cookbook: Cookbook) -> int:
    client = client_from_env()
    failed = 0
    for package, verdict in zip(cookbook.packages, validate_packages(cookbook=cookbook, client=client), strict=True):
        if verdict.contract is None:
            failed += 1
            print(f"✗ {package.name} is not valid on production; its contract was left as it was:\n{verdict.report}")
            continue
        contract_path = package.contract_path
        contents = verdict.contract.to_json()
        previous = contract_path.read_text(encoding="utf-8") if contract_path.is_file() else None
        contract_path.write_text(contents, encoding="utf-8")
        print(f"{'· unchanged' if previous == contents else '✎ wrote'} {contract_path.relative_to(cookbook.root)}")
    if failed:
        return 1
    print("Render next, as `make refresh` does, so the pages carry the refreshed contracts.")
    return 0


def _refresh_library(cookbook: Cookbook) -> int:
    settings = cookbook.settings.library
    snapshot = fetch_library(settings, fetch=download)
    path = cookbook.root / LIBRARY_FILE
    contents = snapshot.to_json()
    previous = path.read_text(encoding="utf-8") if path.is_file() else None
    path.write_text(contents, encoding="utf-8")
    verb = "· unchanged" if previous == contents else "✎ wrote"
    print(f"{verb} {LIBRARY_FILE}: {len(snapshot.methods)} method(s) of {settings.address} at {settings.tag}")
    print("Render next, as `make refresh` does, so the front page lists the snapshot.")
    return 0


def _check_methods(cookbook: Cookbook) -> int:
    client = client_from_env()
    problems = _check_packages(cookbook, client) + check_tutorial(cookbook, client)
    return 1 if problems else 0


def _check_packages(cookbook: Cookbook, client: HostedClient) -> int:
    problems = 0
    for package, verdict in zip(cookbook.packages, validate_packages(cookbook=cookbook, client=client), strict=True):
        if verdict.contract is None:
            problems += 1
            print(f"✗ {package.name} is not valid on production:\n{verdict.report}")
        elif package.contract != verdict.contract:
            problems += 1
            print(f"✗ {package.name} is valid, but its contract.json no longer matches production: run `make refresh`, then `make render`")
        else:
            print(f"✓ {package.name} is valid on production, and its contract snapshot is current")
    return problems


def check_tutorial(cookbook: Cookbook, client: HostedClient) -> int:
    """Validate every tutorial bundle on production from its file, print one line for each, and return how many are not valid."""
    problems = 0
    for bundle_path in tutorial_bundles(cookbook.root):
        verdict = validate_bundle_file(client=client, path=bundle_path, root=cookbook.root)
        if verdict.is_valid:
            print(f"✓ {verdict.source} is valid on production")
        else:
            problems += 1
            print(f"✗ {verdict.source} is not valid on production:\n{verdict.report}")
    return problems


def _check_addresses(cookbook: Cookbook) -> int:
    client = client_from_env()
    verdicts = [check_address(client=client, cookbook=cookbook, package=package) for package in cookbook.packages]
    recipe_verdicts = [
        check_pinned_method_ref(client=client, name=", ".join(recipes), address=address)
        for address, recipes in recipe_addresses(cookbook.root).items()
    ]
    # The front page lists the library's methods at a released tag, so each must resolve today, as a recipe's address must.
    library_verdicts = [
        check_pinned_method_ref(client=client, name="the front page's list of the library's methods", address=line.address)
        for line in build_library_context(cookbook).methods
    ]
    for verdict in verdicts:
        _print_address_verdict(verdict, where="")
    for verdict in [*recipe_verdicts, *library_verdicts]:
        _print_address_verdict(verdict, where=f" (in {verdict.name})")
    unreleased = sum(1 for verdict in verdicts if verdict.state is AddressState.UNRELEASED)
    if unreleased:
        print(f"{unreleased} method(s) not released at {cookbook.tag}: run this check again once the release that carries them is tagged.")
    return 1 if any(verdict.state is AddressState.FAILED for verdict in [*verdicts, *recipe_verdicts, *library_verdicts]) else 0


def _print_address_verdict(verdict: AddressVerdict, *, where: str) -> None:
    if verdict.state is AddressState.VALID:
        print(f"✓ {verdict.address} is valid on production{where}")
    elif verdict.state is AddressState.UNRELEASED:
        print(f"· {verdict.address} is not released yet{where}: {verdict.report}")
    else:
        print(f"✗ {verdict.address} does not validate on production{where}:\n{verdict.report}")


def _check_recipes(cookbook: Cookbook) -> int:
    problems = recipe_problems(cookbook.root)
    for problem in problems:
        print(f"✗ {problem}")
    if problems:
        return 1
    tree_count = sum(1 for tree in find_trees(cookbook.root) if in_recipes(tree.directory, root=cookbook.root))
    address_count = len({found.address for found in find_addresses(cookbook.root)})
    shell_count = len(shell_scripts(cookbook.root))
    print(
        f"✓ {tree_count} recipe tree(s) name a pinned address their recipe calls, and every recipe declares the SDK and gates its types; "
        f"{address_count} address(es) named in the recipes are pinned to a release tag, and {shell_count} shell script(s) parse"
    )
    return 0


def _recipe_trees(cookbook: Cookbook) -> int:
    for tree in find_trees(cookbook.root):
        print(tree.directory.relative_to(cookbook.root))
    return 0


def _recipe_scripts(cookbook: Cookbook) -> int:
    for script in python_scripts(cookbook.root):
        print(script.relative_to(cookbook.root))
    return 0


def _recipe_packages(cookbook: Cookbook) -> int:
    for package_dir in typescript_packages(cookbook.root):
        print(package_dir.relative_to(cookbook.root))
    return 0


def _recipe_shell_scripts(cookbook: Cookbook) -> int:
    for script in shell_scripts(cookbook.root):
        print(script.relative_to(cookbook.root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
