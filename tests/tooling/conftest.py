"""Fixtures for the cookbook tooling's tests: a small cookbook written to a temporary directory, and the repository's real templates.

These tests exercise the renderer and the checks alone: they call no API and need no key.
"""

import json
from pathlib import Path

import pytest

from scripts.contract import Contract
from tests.tooling.test_data import (
    COOKBOOK_TOML,
    FIXTURE_ADDRESS,
    FIXTURE_VERSION,
    FRONT_PAGE,
    LIBRARY_SNAPSHOT,
    WIDGETS_BUNDLE,
    WIDGETS_CONTRACT,
    WIDGETS_KEY,
    WIDGETS_SAMPLE_URL,
    WORDS_BUNDLE,
    WORDS_CONTRACT,
    WORDS_KEY,
    MakeCookbook,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _manifest(*, name: str, version: str, display_name: str, description: str, main_pipe: str, address: str = FIXTURE_ADDRESS) -> str:
    return f"""[package]
name = "{name}"
display_name = "{display_name}"
address = "{address}"
version = "{version}"
description = "{description}"
authors = ["Evotis S.A.S"]
license = "MIT"
mthds_version = ">=1.0.0"
main_pipe = "{main_pipe}"

[exports.{name}]
pipes = ["{main_pipe}"]
"""


def write_package(
    *,
    root: Path,
    name: str,
    manifest: str,
    bundle: str,
    inputs: dict[str, object],
    key: str,
    contract: Contract | None,
) -> Path:
    package_dir = root / "methods" / name
    package_dir.mkdir(parents=True)
    (package_dir / "METHODS.toml").write_text(manifest, encoding="utf-8")
    (package_dir / "bundle.mthds").write_text(bundle, encoding="utf-8")
    (package_dir / "inputs.json").write_text(json.dumps(inputs, indent=2), encoding="utf-8")
    (package_dir / "key.md").write_text(key, encoding="utf-8")
    if contract is not None:
        (package_dir / "contract.json").write_text(contract.to_json(), encoding="utf-8")
    return package_dir


@pytest.fixture
def templates_dir() -> Path:
    return REPO_ROOT / "templates"


@pytest.fixture
def make_cookbook(tmp_path: Path) -> MakeCookbook:
    """A factory writing a two-method cookbook: `extract_widgets`, with an editorial entry and a sample URL, and `count_words`, with neither.

    Its front page holds the two regions listing the methods and the library's methods, still empty, and its `library.json` lists two methods.
    """

    def _make(*, version: str = FIXTURE_VERSION, widgets_version: str | None = None) -> Path:
        root = tmp_path / "cookbook"
        root.mkdir()
        (root / "pyproject.toml").write_text(f'[project]\nname = "fixture-cookbook"\nversion = "{version}"\n', encoding="utf-8")
        (root / "cookbook.toml").write_text(COOKBOOK_TOML, encoding="utf-8")
        (root / "README.md").write_text(FRONT_PAGE, encoding="utf-8")
        (root / "library.json").write_text(LIBRARY_SNAPSHOT.to_json(), encoding="utf-8")
        write_package(
            root=root,
            name="extract_widgets",
            manifest=_manifest(
                name="extract_widgets",
                version=widgets_version or version,
                display_name="Widget Extraction",
                description="Extract every widget from a catalogue page.",
                main_pipe="extract_widgets",
            ),
            bundle=WIDGETS_BUNDLE,
            inputs={"catalogue": {"concept": "widgets.CataloguePage", "content": {"url": WIDGETS_SAMPLE_URL}}},
            key=WIDGETS_KEY,
            contract=WIDGETS_CONTRACT,
        )
        write_package(
            root=root,
            name="count_words",
            manifest=_manifest(
                name="count_words",
                version=version,
                display_name="Word Count",
                description="Count the words of a text",
                main_pipe="count_words",
            ),
            bundle=WORDS_BUNDLE,
            inputs={"text": "The quick brown fox"},
            key=WORDS_KEY,
            contract=WORDS_CONTRACT,
        )
        return root

    return _make
