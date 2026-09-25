"""The command line behind the Makefile's cookbook targets: `python -m scripts <command>`.

Offline, needing no key: `render`, `check-render`, `check-lockstep`, `check-links` (which only fetches public sample URLs), `check-recipes`, and
`recipe-trees`, `recipe-scripts`, `recipe-packages` and `recipe-shell-scripts`, which list what the Makefile hands the SDK script, the type
checkers and shellcheck: the recipes' code, and the page snippets `render` writes under `tests/snippets/`.
Keyed, calling production with `PIPELEX_API_KEY`: `refresh`, `check-methods`, `check-addresses`.
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from scripts.checks import check_links, http_status, lockstep_problems, orphan_snippet_dirs, stale_pages
from scripts.cookbook import Cookbook, load_cookbook
from scripts.exceptions import CookbookError
from scripts.hosted import AddressState, AddressVerdict, check_address, check_pinned_method_ref, client_from_env, validate_packages
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
from scripts.render import render_all, render_pages

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR_NAME = "templates"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts", description="Render the cookbook's method pages and check them.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="The cookbook's root directory (default: this repository)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    commands: dict[str, Callable[[Cookbook], int]] = {
        "render": _render,
        "check-render": _check_render,
        "check-lockstep": _check_lockstep,
        "check-links": _check_links,
        "refresh": _refresh,
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
            "and the front page's list of methods"
        ),
        "check-render": (
            "Fail when a committed page, snippet file or the front page's list of methods differs from a fresh render, "
            "or when a snippet directory belongs to no method"
        ),
        "check-lockstep": "Fail when a manifest's version is not the cookbook's",
        "check-links": "Fetch every sample URL in the packages, and every raw URL on the pages and in the recipes",
        "refresh": "Validate every package on production and write its contract.json (needs PIPELEX_API_KEY)",
        "check-methods": "Validate every package on production from its files, and check its contract snapshot (needs PIPELEX_API_KEY)",
        "check-addresses": "Validate every address on production: each page's at its tag, each recipe's as it pins it (needs PIPELEX_API_KEY)",
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
    arguments = parser.parse_args(argv)
    root = Path(arguments.root).resolve()
    try:
        cookbook = load_cookbook(root, read_contracts=arguments.command != "refresh")
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
    return 1 if orphans else 0


def _check_render(cookbook: Cookbook) -> int:
    rendered = render_all(cookbook=cookbook, templates_dir=_templates_dir(cookbook))
    stale = stale_pages(cookbook=cookbook, rendered=rendered)
    orphans = orphan_snippet_dirs(cookbook)
    for relative in stale:
        print(f"✗ {relative} differs from a fresh render")
    if stale:
        print("Pages and their snippet files are generated: run `make render` and commit what it writes, never edit one by hand.")
    _print_orphans(orphans)
    if stale or orphans:
        return 1
    print(
        f"✓ {len(cookbook.packages)} method page(s), their snippet files and the front page's list of methods match a fresh render at {cookbook.tag}"
    )
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
    print("Run `make render` next, so the pages carry the refreshed contracts.")
    return 0


def _check_methods(cookbook: Cookbook) -> int:
    client = client_from_env()
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
    return 1 if problems else 0


def _check_addresses(cookbook: Cookbook) -> int:
    client = client_from_env()
    verdicts = [check_address(client=client, cookbook=cookbook, package=package) for package in cookbook.packages]
    recipe_verdicts = [
        check_pinned_method_ref(client=client, name=", ".join(recipes), address=address)
        for address, recipes in recipe_addresses(cookbook.root).items()
    ]
    for verdict in verdicts:
        _print_address_verdict(verdict, where="")
    for verdict in recipe_verdicts:
        _print_address_verdict(verdict, where=f" (in {verdict.name})")
    unreleased = sum(1 for verdict in verdicts if verdict.state is AddressState.UNRELEASED)
    if unreleased:
        print(f"{unreleased} method(s) not released at {cookbook.tag}: run this check again once the release that carries them is tagged.")
    return 1 if any(verdict.state is AddressState.FAILED for verdict in [*verdicts, *recipe_verdicts]) else 0


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
