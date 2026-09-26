from datetime import date

import pytest

from scripts.cookbook import Cookbook, LocalFile, OutputHints, load_cookbook
from scripts.exceptions import CookbookLayoutError
from tests.tooling.test_data import WIDGETS_SAMPLE_URL, WIDGETS_SOURCE, MakeCookbook, make_widgets_sample_synthetic

RAW_REPOSITORY_URL = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook"
SAMPLE_PATH = "assets/extract_widgets/catalogue.png"


class TestCookbookLoading:
    def test_the_fixture_cookbook_loads(self, make_cookbook: MakeCookbook):
        cookbook = load_cookbook(make_cookbook())
        assert cookbook.tag == "v0.9.0"
        assert [package.name for package in cookbook.packages] == ["count_words", "extract_widgets"]
        assert cookbook.packages[1].editorial.app_dir == "widgets-app"
        assert cookbook.packages[0].editorial.app_dir is None

    def test_a_manifest_naming_another_package_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        manifest = root / "methods" / "count_words" / "METHODS.toml"
        manifest.write_text(manifest.read_text(encoding="utf-8").replace('name = "count_words"', 'name = "count_the_words"'), encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="but its directory is `count_words`"):
            load_cookbook(root)

    def test_a_manifest_with_another_address_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        manifest = root / "methods" / "count_words" / "METHODS.toml"
        manifest.write_text(manifest.read_text(encoding="utf-8").replace("Pipelex/pipelex-cookbook", "Pipelex/methods"), encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="carries the address `github.com/Pipelex/methods`"):
            load_cookbook(root)

    def test_an_editorial_entry_for_a_missing_method_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        cookbook_toml = root / "cookbook.toml"
        cookbook_toml.write_text(cookbook_toml.read_text(encoding="utf-8") + '\n[methods.gone]\ntitle = "Gone"\n', encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="editorial entries for methods that do not exist under methods/: gone"):
            load_cookbook(root)

    def test_an_unknown_editorial_field_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        cookbook_toml = root / "cookbook.toml"
        cookbook_toml.write_text(cookbook_toml.read_text(encoding="utf-8").replace("yours_dir =", "your_dir ="), encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="your_dir"):
            load_cookbook(root)

    def test_a_broken_contract_snapshot_is_refused_unless_contracts_are_left_unread(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        (root / "methods" / "count_words" / "contract.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="make refresh"):
            load_cookbook(root)
        cookbook = load_cookbook(root, read_contracts=False)
        assert [package.contract for package in cookbook.packages] == [None, None]


class TestLocalFiles:
    @staticmethod
    def _cookbook_with_sample(make_cookbook: MakeCookbook) -> Cookbook:
        root = make_cookbook()
        sample = root / SAMPLE_PATH
        sample.parent.mkdir(parents=True)
        sample.write_bytes(b"png")
        return load_cookbook(root)

    @pytest.mark.parametrize(
        ("url", "ref"),
        [
            (WIDGETS_SAMPLE_URL, "main"),
            (f"{RAW_REPOSITORY_URL}/v0.9.0/{SAMPLE_PATH}", "v0.9.0"),
            (f"{WIDGETS_SAMPLE_URL}?raw=true#page", "main"),
            (f"https://RAW.githubusercontent.com/pipelex/Pipelex-Cookbook/main/{SAMPLE_PATH}", "main"),
            (f"{RAW_REPOSITORY_URL}/main/assets/extract_widgets/%63atalogue.png", "main"),
        ],
        ids=["main", "tag", "query-and-fragment", "any-case", "percent-encoded"],
    )
    def test_a_raw_url_into_the_repository_names_the_checkout_file_at_its_ref(self, make_cookbook: MakeCookbook, url: str, ref: str):
        cookbook = self._cookbook_with_sample(make_cookbook)
        assert cookbook.local_file_of(url) == LocalFile(ref=ref, path=(cookbook.root / SAMPLE_PATH).resolve())

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.org/assets/extract_widgets/catalogue.png",
            f"https://raw.githubusercontent.com/Pipelex/methods/main/{SAMPLE_PATH}",
            f"http://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/{SAMPLE_PATH}",
            RAW_REPOSITORY_URL,
            "https://[bad/assets",
        ],
        ids=["another-host", "another-repository", "plain-http", "no-ref", "malformed"],
    )
    def test_a_url_hosted_elsewhere_names_no_local_file(self, make_cookbook: MakeCookbook, url: str):
        assert self._cookbook_with_sample(make_cookbook).local_file_of(url) is None

    @pytest.mark.parametrize(
        ("url", "problem"),
        [
            (f"{RAW_REPOSITORY_URL}/main/assets/extract_widgets/missing.png", "this checkout holds no file at assets/extract_widgets/missing.png"),
            # The ref is one path segment, so a branch named with a slash leaves the rest of its name in the file's path.
            (f"{RAW_REPOSITORY_URL}/refs/heads/main/{SAMPLE_PATH}", f"this checkout holds no file at heads/main/{SAMPLE_PATH}"),
            (f"{RAW_REPOSITORY_URL}/main/../outside.txt", "its path ../outside.txt leads outside this checkout"),
            (f"{RAW_REPOSITORY_URL}/main/assets/%2E%2E/%2E%2E/outside.txt", "its path assets/../../outside.txt leads outside this checkout"),
            (f"{RAW_REPOSITORY_URL}/main//etc/hosts", "its path /etc/hosts leads outside this checkout"),
        ],
        ids=["missing", "slashed-ref", "dot-dot", "encoded-dot-dot", "absolute"],
    )
    def test_a_raw_url_into_the_repository_naming_no_checkout_file_is_refused(self, make_cookbook: MakeCookbook, url: str, problem: str):
        cookbook = self._cookbook_with_sample(make_cookbook)
        # A file beside the checkout, which a path climbing out of it would reach.
        (cookbook.root.parent / "outside.txt").write_text("not the cookbook's", encoding="utf-8")
        with pytest.raises(CookbookLayoutError) as raised:
            cookbook.local_file_of(url)
        assert str(raised.value) == problem


class TestSampleRecords:
    def test_a_record_loads_with_its_date_and_hints_default_to_none(self, make_cookbook: MakeCookbook):
        cookbook = load_cookbook(make_cookbook())
        widgets = cookbook.packages[1]
        record = widgets.editorial.samples["catalogue"]
        assert (record.label, record.synthetic, record.retrieved) == ("sample catalogue", False, date(2026, 9, 20))
        assert widgets.editorial.output == OutputHints()
        assert cookbook.packages[0].editorial.samples == {}

    @pytest.mark.parametrize(
        ("old", "new", "message"),
        [
            ("synthetic = false\n", "synthetic = true\n", "has no `source`"),
            (f'source = "{WIDGETS_SOURCE}"\nretrieved = 2026-09-20\n', "", "names the URL it was copied from"),
            ("retrieved = 2026-09-20\n", "", "gives the date it was copied"),
            ('attribution = "The Widget Society"\n', "", "attribution"),
            ('attribution = "The Widget Society"\n', 'attribution = "The Widget Society"\ncredit = "x"\n', "credit"),
        ],
    )
    def test_a_record_with_a_field_missing_unknown_or_out_of_place_is_refused(self, make_cookbook: MakeCookbook, old: str, new: str, message: str):
        root = make_cookbook()
        cookbook_toml = root / "cookbook.toml"
        contents = cookbook_toml.read_text(encoding="utf-8")
        assert old in contents
        cookbook_toml.write_text(contents.replace(old, new), encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match=message):
            load_cookbook(root)

    def test_a_made_up_sample_takes_no_retrieval_date(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        make_widgets_sample_synthetic(root)
        cookbook_toml = root / "cookbook.toml"
        cookbook_toml.write_text(
            cookbook_toml.read_text(encoding="utf-8").replace("synthetic = true\n", "synthetic = true\nretrieved = 2026-09-20\n")
        )
        with pytest.raises(CookbookLayoutError, match="names none"):
            load_cookbook(root)

    def test_a_record_for_an_input_the_sample_does_not_give_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        cookbook_toml = root / "cookbook.toml"
        cookbook_toml.write_text(cookbook_toml.read_text(encoding="utf-8").replace("samples.catalogue]", "samples.brochure]"), encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="inputs its inputs.json does not give: brochure"):
            load_cookbook(root)

    @pytest.mark.parametrize(
        "url",
        [
            "https://widgets.example.org/catalogue.png",
            "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/assets/count_words/catalogue.png",
        ],
    )
    def test_a_real_file_sample_kept_anywhere_but_its_own_assets_is_refused(self, make_cookbook: MakeCookbook, url: str):
        root = make_cookbook()
        (root / "methods" / "extract_widgets" / "inputs.json").write_text(f'{{"catalogue": {{"url": "{url}"}}}}', encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="copied under assets/extract_widgets/"):
            load_cookbook(root)
        make_widgets_sample_synthetic(root)
        assert load_cookbook(root).packages[1].editorial.samples["catalogue"].synthetic is True

    def test_an_output_hint_outside_its_vocabulary_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        cookbook_toml = root / "cookbook.toml"
        cookbook_toml.write_text(
            cookbook_toml.read_text(encoding="utf-8") + '\n[methods.extract_widgets.output]\nformats = { widgets = "pdf" }\n', encoding="utf-8"
        )
        with pytest.raises(CookbookLayoutError, match="widgets"):
            load_cookbook(root)
