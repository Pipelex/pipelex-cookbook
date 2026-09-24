"""The command line behind the Makefile's cookbook targets: `python -m scripts <command>`.

Offline, needing no key: `render`, `check-render`, `check-lockstep`, `check-links` (which only fetches public sample URLs).
Keyed, calling production with `PIPELEX_API_KEY`: `refresh`, `check-methods`, `check-addresses`.
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from scripts.checks import check_links, http_status, lockstep_problems, stale_pages
from scripts.cookbook import Cookbook, load_cookbook
from scripts.exceptions import CookbookError
from scripts.hosted import AddressState, check_address, client_from_env, validate_packages
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
    }
    helps = {
        "render": "Write every methods/<name>/README.md from its package and cookbook.toml, and the front page's list of methods",
        "check-render": "Fail when a committed page, or the front page's list of methods, differs from a fresh render",
        "check-lockstep": "Fail when a manifest's version is not the cookbook's",
        "check-links": "Fetch every sample URL in the packages and every raw URL on the pages",
        "refresh": "Validate every package on production and write its contract.json (needs PIPELEX_API_KEY)",
        "check-methods": "Validate every package on production from its files, and check its contract snapshot (needs PIPELEX_API_KEY)",
        "check-addresses": "Validate every page's address on production at its tag, reporting a method not released yet (needs PIPELEX_API_KEY)",
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
        page_path.write_text(contents, encoding="utf-8")
        relative = page_path.relative_to(cookbook.root)
        print(f"{'✎ rewrote' if relative in stale else '· unchanged'} {relative}")
    return 0


def _check_render(cookbook: Cookbook) -> int:
    rendered = render_all(cookbook=cookbook, templates_dir=_templates_dir(cookbook))
    stale = stale_pages(cookbook=cookbook, rendered=rendered)
    if stale:
        for relative in stale:
            print(f"✗ {relative} differs from a fresh render")
        print("Pages are generated: run `make render` and commit what it writes, never edit a page by hand.")
        return 1
    print(f"✓ {len(cookbook.packages)} method page(s) and the front page's list of methods match a fresh render at {cookbook.tag}")
    return 0


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
    for verdict in verdicts:
        if verdict.state is AddressState.VALID:
            print(f"✓ {verdict.address} is valid on production")
        elif verdict.state is AddressState.UNRELEASED:
            print(f"· {verdict.address} is not released yet: {verdict.report}")
        else:
            print(f"✗ {verdict.address} does not validate on production:\n{verdict.report}")
    unreleased = sum(1 for verdict in verdicts if verdict.state is AddressState.UNRELEASED)
    if unreleased:
        print(f"{unreleased} method(s) not released at {cookbook.tag}: run this check again once the release that carries them is tagged.")
    return 1 if any(verdict.state is AddressState.FAILED for verdict in verdicts) else 0


if __name__ == "__main__":
    sys.exit(main())
