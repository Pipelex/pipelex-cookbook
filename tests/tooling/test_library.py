import io
import tarfile
from pathlib import Path

import pytest

from scripts.checks import stale_pages
from scripts.cookbook import load_cookbook
from scripts.exceptions import CookbookLayoutError
from scripts.library import LibraryMethod, LibrarySettings, fetch_library, load_library, snapshot_from_tarball
from scripts.render import render_all, render_front_page
from tests.tooling.test_data import LIBRARY_ADDRESS, LIBRARY_REPOSITORY, LIBRARY_SNAPSHOT, LIBRARY_TAG, MakeCookbook

SETTINGS = LibrarySettings(address=LIBRARY_ADDRESS, repository=LIBRARY_REPOSITORY, tag=LIBRARY_TAG)
# The directory a GitHub tarball of the library at the tag opens with.
TOP_DIR = "methods-0.4.0"


def _manifest(*, name: str, address: str = LIBRARY_ADDRESS, version: str = "0.4.0", description: str = "Does one thing.") -> str:
    return f"""[package]
name = "{name}"
display_name = "{name.replace("_", " ").title()}"
address = "{address}"
version = "{version}"
description = "{description}"
authors = ["Evotis S.A.S"]
license = "MIT"
mthds_version = ">=1.0.0"
main_pipe = "run_{name}"

[exports.{name}]
pipes = ["run_{name}"]
"""


def _tarball(files: dict[str, str]) -> bytes:
    """A gzipped tarball holding each file at its path, as GitHub serves a tag's."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for path, text in files.items():
            data = text.encode("utf-8")
            member = tarfile.TarInfo(path)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return buffer.getvalue()


class TestLibrarySnapshot:
    def test_a_tarball_s_manifests_become_the_snapshot_sorted_by_name(self):
        data = _tarball(
            {
                f"{TOP_DIR}/README.md": "# The library\n",
                f"{TOP_DIR}/methods/text_stats/METHODS.toml": _manifest(name="text_stats", description="Count the words"),
                f"{TOP_DIR}/methods/text_stats/main.mthds": 'domain = "text_stats"\n',
                f"{TOP_DIR}/methods/invoice_extraction/METHODS.toml": _manifest(name="invoice_extraction"),
                f"{TOP_DIR}/methods/invoice_extraction/tests/METHODS.toml": "not a package's manifest",
            }
        )
        snapshot = snapshot_from_tarball(data, SETTINGS)

        assert snapshot.address == LIBRARY_ADDRESS
        assert snapshot.tag == LIBRARY_TAG
        assert snapshot.methods == [
            LibraryMethod(
                name="invoice_extraction", display_name="Invoice Extraction", description="Does one thing.", main_pipe="run_invoice_extraction"
            ),
            LibraryMethod(name="text_stats", display_name="Text Stats", description="Count the words", main_pipe="run_text_stats"),
        ]

    @pytest.mark.parametrize(
        ("manifest", "refusal"),
        [
            (_manifest(name="text_stats", address="github.com/Someone/else"), "carries the address `github.com/Someone/else`"),
            (_manifest(name="text_stats", version="0.3.9"), "declares version 0.3.9, but the tag is v0.4.0"),
            (_manifest(name="word_stats"), "names the package `word_stats`, but its directory is `text_stats`"),
            ("[package\n", "does not parse"),
        ],
    )
    def test_a_manifest_that_does_not_belong_at_the_tag_is_refused(self, manifest: str, refusal: str):
        data = _tarball({f"{TOP_DIR}/methods/text_stats/METHODS.toml": manifest})
        with pytest.raises(CookbookLayoutError, match=refusal):
            snapshot_from_tarball(data, SETTINGS)

    def test_a_tarball_holding_no_method_is_refused(self):
        with pytest.raises(CookbookLayoutError, match="holds no methods/<name>/METHODS.toml"):
            snapshot_from_tarball(_tarball({f"{TOP_DIR}/README.md": "# Empty\n"}), SETTINGS)

    def test_bytes_that_are_not_a_tarball_are_refused(self):
        with pytest.raises(CookbookLayoutError, match="does not open"):
            snapshot_from_tarball(b"<html>Not found</html>", SETTINGS)

    def test_the_snapshot_is_taken_from_the_tarball_at_the_pinned_tag(self):
        fetched: list[str] = []

        def fetch(url: str) -> bytes:
            fetched.append(url)
            return _tarball({f"{TOP_DIR}/methods/text_stats/METHODS.toml": _manifest(name="text_stats")})

        snapshot = fetch_library(SETTINGS, fetch=fetch)

        assert fetched == ["https://codeload.github.com/Pipelex/methods/tar.gz/refs/tags/v0.4.0"]
        assert [method.name for method in snapshot.methods] == ["text_stats"]

    def test_the_snapshot_written_is_the_snapshot_loaded(self, tmp_path: Path):
        (tmp_path / "library.json").write_text(LIBRARY_SNAPSHOT.to_json(), encoding="utf-8")
        assert load_library(tmp_path, SETTINGS) == LIBRARY_SNAPSHOT


class TestLibraryInTheCookbook:
    def test_a_snapshot_taken_at_another_tag_fails_loading(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        cookbook_toml = root / "cookbook.toml"
        cookbook_toml.write_text(cookbook_toml.read_text(encoding="utf-8").replace(f'tag = "{LIBRARY_TAG}"', 'tag = "v0.5.0"'), encoding="utf-8")
        with pytest.raises(
            CookbookLayoutError,
            match=r"was taken from github.com/Pipelex/methods at v0.4.0, but cookbook.toml pins .* at v0.5.0: run `make refresh-library`",
        ):
            load_cookbook(root)

    def test_a_missing_snapshot_fails_loading_unless_the_command_rewrites_it(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        (root / "library.json").unlink()
        with pytest.raises(CookbookLayoutError, match="library.json is missing: run `make refresh-library`"):
            load_cookbook(root)
        assert load_cookbook(root, read_library=False).library is None

    def test_the_front_page_lists_the_library_s_methods_at_the_tag(self, make_cookbook: MakeCookbook, templates_dir: Path):
        root = make_cookbook()
        front_page = render_front_page(cookbook=load_cookbook(root), templates_dir=templates_dir)[root / "README.md"]

        assert "[Pipelex method library](https://github.com/Pipelex/methods/tree/v0.4.0)" in front_page
        assert (
            "- **[Invoice Extraction](https://github.com/Pipelex/methods/tree/v0.4.0/methods/invoice_extraction)** · "
            "`github.com/Pipelex/methods/invoice_extraction@v0.4.0`: Extract structured invoice data from a document.\n"
        ) in front_page
        assert (
            "- **[Text Stats](https://github.com/Pipelex/methods/tree/v0.4.0/methods/text_stats)** · "
            "`github.com/Pipelex/methods/text_stats@v0.4.0`: Deterministic text statistics computed in pure Python.\n"
        ) in front_page
        assert front_page.index("invoice_extraction@") < front_page.index("text_stats@")

    @pytest.mark.parametrize("copies", [0, 2])
    def test_a_front_page_without_the_library_region_or_with_it_twice_is_refused(self, make_cookbook: MakeCookbook, templates_dir: Path, copies: int):
        root = make_cookbook()
        front_page = root / "README.md"
        region = "<!-- BEGIN library, written by `make render` from library.json: never edit this region by hand -->\n<!-- END library -->\n"
        contents = front_page.read_text(encoding="utf-8")
        assert region in contents
        front_page.write_text(contents.replace(region, region * copies), encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="must hold one region for the list of the library's methods"):
            render_all(cookbook=load_cookbook(root), templates_dir=templates_dir)

    def test_a_hand_edit_inside_the_library_region_makes_the_front_page_stale(self, make_cookbook: MakeCookbook, templates_dir: Path):
        cookbook = load_cookbook(make_cookbook())
        rendered = render_all(cookbook=cookbook, templates_dir=templates_dir)
        for path, contents in rendered.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        assert stale_pages(cookbook=cookbook, rendered=rendered) == []

        front_page = cookbook.root / "README.md"
        front_page.write_text(front_page.read_text(encoding="utf-8").replace("Text Stats", "Text Statistics"), encoding="utf-8")
        assert stale_pages(cookbook=cookbook, rendered=render_all(cookbook=cookbook, templates_dir=templates_dir)) == [Path("README.md")]
