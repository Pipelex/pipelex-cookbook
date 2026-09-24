import pytest

from scripts.cookbook import load_cookbook
from scripts.exceptions import CookbookLayoutError
from tests.tooling.test_data import MakeCookbook


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

    def test_a_package_without_an_answer_key_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        (root / "methods" / "count_words" / "key.md").unlink()
        with pytest.raises(CookbookLayoutError, match="holds no key.md"):
            load_cookbook(root)

    def test_a_broken_contract_snapshot_is_refused_unless_contracts_are_left_unread(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        (root / "methods" / "count_words" / "contract.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="make refresh"):
            load_cookbook(root)
        cookbook = load_cookbook(root, read_contracts=False)
        assert [package.contract for package in cookbook.packages] == [None, None]
