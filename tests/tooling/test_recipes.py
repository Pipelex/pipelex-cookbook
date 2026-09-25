import json
from pathlib import Path

from scripts.recipes import find_trees, python_scripts, recipe_problems

ADDRESS = "github.com/Pipelex/methods/invoice_extraction@v0.1.1"
SCRIPT_HEADER = '# /// script\n# dependencies = ["pipelex-sdk==0.12.0"]\n# ///\n'


def _python_recipe(root: Path, *, address: str = ADDRESS, code_address: str = ADDRESS, header: str = SCRIPT_HEADER) -> Path:
    """A Python recipe calling `code_address`, with one generated tree whose sidecar names `address`."""
    recipe = root / "recipes" / "code" / "python" / "batch"
    tree = recipe / "generated" / "invoice_extraction"
    tree.mkdir(parents=True)
    (tree / "sources.json").write_text(json.dumps({"method": {"method_ref": address}, "target": "python-pydantic"}), encoding="utf-8")
    (tree / "codegen.lock").write_text("lock_version = 1\n", encoding="utf-8")
    (tree / "models.py").write_text("class Invoice: ...\n", encoding="utf-8")
    (recipe / "batch.py").write_text(f'{header}METHOD_REF = "{code_address}"\n', encoding="utf-8")
    return recipe


class TestRecipes:
    def test_a_recipe_calling_the_address_its_types_come_from_is_clean(self, tmp_path: Path):
        recipe = _python_recipe(tmp_path)
        trees = find_trees(tmp_path)
        assert [(tree.directory, tree.method_ref, tree.target) for tree in trees] == [
            (recipe / "generated" / "invoice_extraction", ADDRESS, "python-pydantic")
        ]
        assert python_scripts(tmp_path) == [recipe / "batch.py"]
        assert recipe_problems(tmp_path) == []

    def test_an_address_without_a_release_tag_is_a_problem(self, tmp_path: Path):
        floating = "github.com/Pipelex/methods/invoice_extraction"
        _python_recipe(tmp_path, address=floating, code_address=floating)
        [problem] = recipe_problems(tmp_path)
        assert "is not an address pinned to a release tag" in problem

    def test_types_of_another_method_than_the_code_calls_are_a_problem(self, tmp_path: Path):
        _python_recipe(tmp_path, code_address="github.com/Pipelex/methods/doc_summarizer@v0.1.1")
        [problem] = recipe_problems(tmp_path)
        assert f"never names {ADDRESS}" in problem

    def test_code_naming_another_release_of_the_address_is_a_problem(self, tmp_path: Path):
        _python_recipe(tmp_path, code_address=f"{ADDRESS}0")
        [problem] = recipe_problems(tmp_path)
        assert f"never names {ADDRESS}" in problem

    def test_an_address_named_only_in_prose_is_a_problem(self, tmp_path: Path):
        recipe = _python_recipe(tmp_path)
        (recipe / "batch.py").write_text(f"{SCRIPT_HEADER}# Calls {ADDRESS} by its address.\nMETHOD_REF = 'somewhere else'\n", encoding="utf-8")
        [problem] = recipe_problems(tmp_path)
        assert f"never names {ADDRESS}" in problem

    def test_a_tree_that_lost_its_sidecar_and_its_lock_is_still_found(self, tmp_path: Path):
        recipe = _python_recipe(tmp_path)
        tree = recipe / "generated" / "invoice_extraction"
        (tree / "sources.json").unlink()
        (tree / "codegen.lock").unlink()
        (recipe / "generated" / "__pycache__").mkdir()
        assert [found.directory for found in find_trees(tmp_path)] == [tree]
        [problem] = recipe_problems(tmp_path)
        assert problem.startswith("recipes/code/python/batch/generated/invoice_extraction/sources.json: missing")

    def test_a_tree_without_its_sidecar_is_a_problem(self, tmp_path: Path):
        recipe = _python_recipe(tmp_path)
        (recipe / "generated" / "invoice_extraction" / "sources.json").unlink()
        [problem] = recipe_problems(tmp_path)
        assert problem.startswith("recipes/code/python/batch/generated/invoice_extraction/sources.json: missing")

    def test_a_script_that_does_not_declare_the_sdk_is_a_problem(self, tmp_path: Path):
        _python_recipe(tmp_path, header='# /// script\n# dependencies = ["httpx"]\n# ///\n')
        [problem] = recipe_problems(tmp_path)
        assert problem == "recipes/code/python/batch/batch.py: its inline dependencies do not name pipelex-sdk"

    def test_typescript_types_need_a_package(self, tmp_path: Path):
        recipe = _python_recipe(tmp_path)
        sidecar = recipe / "generated" / "invoice_extraction" / "sources.json"
        sidecar.write_text(json.dumps({"method": {"method_ref": ADDRESS}, "target": "ts-zod"}), encoding="utf-8")
        [problem] = recipe_problems(tmp_path)
        assert "target ts-zod needs a package.json" in problem

    def test_installed_packages_and_scripts_without_inline_dependencies_are_left_out(self, tmp_path: Path):
        recipe = _python_recipe(tmp_path)
        vendored = recipe / "node_modules" / "some-package" / "generated" / "thing"
        vendored.mkdir(parents=True)
        (vendored / "codegen.lock").write_text("lock_version = 1\n", encoding="utf-8")
        (recipe / "helpers.py").write_text("VALUE = 1\n", encoding="utf-8")
        assert [tree.directory for tree in find_trees(tmp_path)] == [recipe / "generated" / "invoice_extraction"]
        assert python_scripts(tmp_path) == [recipe / "batch.py"]

    def test_a_cookbook_without_recipes_has_nothing_to_check(self, tmp_path: Path):
        assert find_trees(tmp_path) == []
        assert python_scripts(tmp_path) == []
        assert recipe_problems(tmp_path) == []
