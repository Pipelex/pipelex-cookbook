from pathlib import Path

import pytest

from scripts.__main__ import check_tutorial
from scripts.cookbook import load_cookbook
from scripts.hosted import BundleVerdict, HostedClient
from scripts.tutorial import tutorial_bundles
from tests.tooling.test_data import MakeCookbook


def _write(root: Path, relative: str, text: str = 'domain = "lesson"\n') -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _client() -> HostedClient:
    return HostedClient(api_key="not-a-real-key", base_url="https://api.example.invalid")


class TestTutorial:
    def test_every_bundle_under_the_tutorial_is_found_at_any_depth_and_sorted(self, tmp_path: Path):
        _write(tmp_path, "tutorial/medium/2_batch.mthds")
        _write(tmp_path, "tutorial/easy/basics/1_hello.mthds")
        _write(tmp_path, "tutorial/easy/basics/inputs.json", "{}")
        _write(tmp_path, "tutorial/README.md", "# Tutorials\n")
        _write(tmp_path, "methods/count_words/bundle.mthds")

        assert [path.relative_to(tmp_path).as_posix() for path in tutorial_bundles(tmp_path)] == [
            "tutorial/easy/basics/1_hello.mthds",
            "tutorial/medium/2_batch.mthds",
        ]

    def test_a_cookbook_without_a_tutorial_has_no_bundle_to_check(self, tmp_path: Path):
        assert tutorial_bundles(tmp_path) == []

    def test_each_bundle_prints_its_verdict_and_an_invalid_one_counts_as_a_problem(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], make_cookbook: MakeCookbook
    ):
        root = make_cookbook()
        _write(root, "tutorial/easy/1_hello.mthds")
        _write(root, "tutorial/medium/2_broken.mthds")

        def validate_bundle_file(*, client: HostedClient, path: Path, root: Path) -> BundleVerdict:
            source = path.relative_to(root).as_posix()
            if "broken" in source:
                return BundleVerdict(source=source, is_valid=False, report="Pipe `broken` names no output")
            return BundleVerdict(source=source, is_valid=True, report="")

        monkeypatch.setattr("scripts.__main__.validate_bundle_file", validate_bundle_file)

        assert check_tutorial(load_cookbook(root), _client()) == 1
        assert capsys.readouterr().out.splitlines() == [
            "✓ tutorial/easy/1_hello.mthds is valid on production",
            "✗ tutorial/medium/2_broken.mthds is not valid on production:",
            "Pipe `broken` names no output",
        ]
