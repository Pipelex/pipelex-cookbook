import json
from pathlib import Path

import pytest

from scripts.recipes import (
    RecipeAddress,
    find_addresses,
    find_trees,
    python_scripts,
    recipe_addresses,
    recipe_problems,
    shell_scripts,
    typescript_packages,
)

ADDRESS = "github.com/Pipelex/methods/invoice_extraction@v0.1.1"
SCRIPT_HEADER = '# /// script\n# dependencies = ["pipelex-sdk==0.12.0"]\n# ///\n'
DPE_ADDRESS = "github.com/Pipelex/pipelex-cookbook/extract_dpe@v0.18.0"
# The files a page snippet's sidecar names, from the repository root: the `.mthds` files of its method's package.
SNIPPET_FILES = ["methods/extract_gantt/bundle.mthds", "methods/extract_gantt/charts.mthds"]


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


def _typescript_recipe(
    root: Path, *, dependencies: dict[str, str] | None = None, codegen_check: str = "node scripts/codegen-check.mjs generated/extract_gantt"
) -> Path:
    """A TypeScript recipe calling the address its one generated tree names, with its package.json."""
    recipe = root / "recipes" / "code" / "typescript" / "upload"
    tree = recipe / "generated" / "extract_gantt"
    tree.mkdir(parents=True)
    (tree / "sources.json").write_text(json.dumps({"method": {"method_ref": ADDRESS}, "target": "ts-zod"}), encoding="utf-8")
    (tree / "codegen.lock").write_text("lock_version = 1\n", encoding="utf-8")
    (tree / "types.ts").write_text("export const GanttChartSchema = {};\n", encoding="utf-8")
    (recipe / "extract.ts").write_text(f'const METHOD_REF = "{ADDRESS}";\n', encoding="utf-8")
    package = {"dependencies": {"@pipelex/sdk": "0.25.1"} if dependencies is None else dependencies, "scripts": {"codegen:check": codegen_check}}
    (recipe / "package.json").write_text(json.dumps(package), encoding="utf-8")
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

    def test_a_typescript_recipe_depending_on_the_sdk_and_gating_its_types_is_clean(self, tmp_path: Path):
        recipe = _typescript_recipe(tmp_path)
        (recipe / "node_modules" / "zod").mkdir(parents=True)
        (recipe / "node_modules" / "zod" / "package.json").write_text("{}", encoding="utf-8")
        assert typescript_packages(tmp_path) == [recipe]
        assert recipe_problems(tmp_path) == []

    def test_a_package_that_does_not_depend_on_the_sdk_is_a_problem(self, tmp_path: Path):
        _typescript_recipe(tmp_path, dependencies={"zod": "^4.4.3"})
        [problem] = recipe_problems(tmp_path)
        assert problem == "recipes/code/typescript/upload/package.json: its dependencies do not name @pipelex/sdk"

    def test_a_tree_its_codegen_gate_does_not_check_is_a_problem(self, tmp_path: Path):
        _typescript_recipe(tmp_path, codegen_check="node scripts/codegen-check.mjs generated/extract_gantt_old")
        [problem] = recipe_problems(tmp_path)
        assert "its `codegen:check` script does not check generated/extract_gantt" in problem

    def test_a_codegen_gate_naming_its_tree_by_another_spelling_of_the_path_is_clean(self, tmp_path: Path):
        _typescript_recipe(tmp_path, codegen_check="node scripts/codegen-check.mjs ./generated/extract_gantt/")
        assert recipe_problems(tmp_path) == []

    def test_a_package_without_a_codegen_gate_is_a_problem_even_with_no_tree(self, tmp_path: Path):
        recipe = _typescript_recipe(tmp_path)
        for generated_file in (recipe / "generated" / "extract_gantt").iterdir():
            generated_file.unlink()
        (recipe / "generated" / "extract_gantt").rmdir()
        (recipe / "generated").rmdir()
        (recipe / "package.json").write_text(json.dumps({"dependencies": {"@pipelex/sdk": "0.25.1"}, "scripts": {}}), encoding="utf-8")
        [problem] = recipe_problems(tmp_path)
        assert problem == "recipes/code/typescript/upload/package.json: it has no `codegen:check` script, the gate over its generated types"

    def test_an_unreadable_package_json_is_a_problem(self, tmp_path: Path):
        recipe = _typescript_recipe(tmp_path)
        (recipe / "package.json").write_text("{not json", encoding="utf-8")
        [problem] = recipe_problems(tmp_path)
        assert problem.startswith("recipes/code/typescript/upload/package.json: must be JSON")

    def test_a_recipe_tree_generated_from_files_is_a_problem(self, tmp_path: Path):
        recipe = _python_recipe(tmp_path)
        sidecar = {"method": {"files": ["methods/invoice_extraction/bundle.mthds"]}, "target": "python-pydantic"}
        (recipe / "generated" / "invoice_extraction" / "sources.json").write_text(json.dumps(sidecar), encoding="utf-8")
        [problem] = recipe_problems(tmp_path)
        assert problem == (
            "recipes/code/python/batch/generated/invoice_extraction/sources.json: "
            "names files rather than an address, but a recipe's types come from the address its code calls"
        )
        assert recipe_addresses(tmp_path) == {}

    @pytest.mark.parametrize(
        "method",
        [
            {"method_ref": ADDRESS, "files": ["methods/invoice_extraction/bundle.mthds"]},
            {},
            {"method_ref": None, "files": None},
        ],
    )
    def test_a_sidecar_naming_both_an_address_and_files_or_neither_is_a_problem(self, tmp_path: Path, method: dict[str, object]):
        recipe = _python_recipe(tmp_path)
        (recipe / "generated" / "invoice_extraction" / "sources.json").write_text(
            json.dumps({"method": method, "target": "python-pydantic"}), encoding="utf-8"
        )
        [problem] = recipe_problems(tmp_path)
        assert problem == (
            "recipes/code/python/batch/generated/invoice_extraction/sources.json: "
            "must be JSON naming `target` and exactly one of `method.method_ref` and `method.files`"
        )


def _snippets(root: Path, *, with_trees: bool = False) -> Path:
    """The page snippets of one method under `tests/snippets/`, with their shared package, and a generated tree per language if asked.

    Nothing here keeps a recipe's promises: the trees name the package's files rather than an address the snippets call, the script
    declares no SDK, and the package names neither the SDK nor a gate.
    """
    snippets = root / "tests" / "snippets"
    (snippets / "extract_gantt" / "typescript").mkdir(parents=True)
    (snippets / "extract_gantt" / "python").mkdir(parents=True)
    (snippets / "package.json").write_text(json.dumps({"scripts": {"typecheck": "tsc --noEmit"}}), encoding="utf-8")
    (snippets / "extract_gantt" / "typescript" / "snippet.ts").write_text('console.log("snippet");\n', encoding="utf-8")
    (snippets / "extract_gantt" / "python" / "snippet.py").write_text(
        '# /// script\n# dependencies = ["httpx"]\n# ///\nprint("snippet")\n', encoding="utf-8"
    )
    (snippets / "node_modules" / "zod").mkdir(parents=True)
    (snippets / "node_modules" / "zod" / "package.json").write_text("{}", encoding="utf-8")
    if with_trees:
        for language, target in (("typescript", "ts-zod"), ("python", "python-pydantic")):
            tree = snippets / "extract_gantt" / language / "generated" / "extract_gantt"
            tree.mkdir(parents=True)
            (tree / "sources.json").write_text(json.dumps({"method": {"files": SNIPPET_FILES}, "target": target}), encoding="utf-8")
    return snippets


class TestSnippets:
    def test_the_snippet_scripts_and_their_package_are_found_beside_the_recipes(self, tmp_path: Path):
        recipe = _python_recipe(tmp_path)
        snippets = _snippets(tmp_path)
        assert python_scripts(tmp_path) == [recipe / "batch.py", snippets / "extract_gantt" / "python" / "snippet.py"]
        assert typescript_packages(tmp_path) == [snippets]

    def test_the_snippets_trees_are_found_and_a_typescript_tree_belongs_to_the_nearest_package(self, tmp_path: Path):
        snippets = _snippets(tmp_path, with_trees=True)
        trees = {tree.directory.relative_to(snippets).as_posix(): tree for tree in find_trees(tmp_path)}
        assert sorted(trees) == ["extract_gantt/python/generated/extract_gantt", "extract_gantt/typescript/generated/extract_gantt"]
        typescript_tree = trees["extract_gantt/typescript/generated/extract_gantt"]
        assert typescript_tree.recipe_dir == snippets / "extract_gantt" / "typescript"
        assert typescript_tree.package_dir == snippets

    def test_a_snippet_trees_sidecar_naming_its_packages_files_is_read(self, tmp_path: Path):
        _snippets(tmp_path, with_trees=True)
        assert [(tree.method_ref, tree.files, tree.target, tree.sidecar_problem) for tree in find_trees(tmp_path)] == [
            (None, SNIPPET_FILES, "python-pydantic", None),
            (None, SNIPPET_FILES, "ts-zod", None),
        ]

    def test_the_rules_only_a_recipe_needs_do_not_fire_on_snippets(self, tmp_path: Path):
        _snippets(tmp_path, with_trees=True)
        assert recipe_problems(tmp_path) == []
        assert recipe_addresses(tmp_path) == {}

    def test_a_snippet_tree_without_its_sidecar_is_still_a_problem(self, tmp_path: Path):
        snippets = _snippets(tmp_path, with_trees=True)
        (snippets / "extract_gantt" / "python" / "generated" / "extract_gantt" / "sources.json").unlink()
        [problem] = recipe_problems(tmp_path)
        assert problem.startswith("tests/snippets/extract_gantt/python/generated/extract_gantt/sources.json: missing")

    def test_a_typescript_snippet_tree_needs_a_package_at_or_above_it(self, tmp_path: Path):
        snippets = _snippets(tmp_path, with_trees=True)
        (snippets / "package.json").unlink()
        [problem] = recipe_problems(tmp_path)
        assert problem == (
            "tests/snippets/extract_gantt/typescript/generated/extract_gantt: "
            "target ts-zod needs a package.json in tests/snippets/extract_gantt/typescript or above it"
        )

    def test_a_recipe_tree_below_its_package_is_gated_by_that_package(self, tmp_path: Path):
        recipe = _typescript_recipe(tmp_path, codegen_check="node scripts/codegen-check.mjs src/generated/extract_gantt")
        (recipe / "src").mkdir()
        (recipe / "generated").rename(recipe / "src" / "generated")
        [tree] = find_trees(tmp_path)
        assert tree.recipe_dir == recipe / "src"
        assert tree.package_dir == recipe
        assert recipe_problems(tmp_path) == []
        (recipe / "package.json").write_text(
            json.dumps({"dependencies": {"@pipelex/sdk": "0.25.1"}, "scripts": {"codegen:check": "node scripts/codegen-check.mjs"}}), encoding="utf-8"
        )
        [problem] = recipe_problems(tmp_path)
        assert "its `codegen:check` script does not check src/generated/extract_gantt" in problem


def _run_recipe(root: Path, *, readme: str, script: str | None = None) -> Path:
    """A recipe with no code of its own under `recipes/run/`: a README, and a shell script when one is given."""
    recipe = root / "recipes" / "run" / "http"
    recipe.mkdir(parents=True)
    (recipe / "README.md").write_text(readme, encoding="utf-8")
    if script is not None:
        (recipe / "run.sh").write_text(script, encoding="utf-8")
    return recipe


class TestRecipeAddresses:
    def test_addresses_in_a_readme_a_shell_script_and_a_json_file_are_found(self, tmp_path: Path):
        recipe = _run_recipe(tmp_path, readme=f"Run `{ADDRESS}` on the invoice.\n", script=f'#!/bin/sh\nMETHOD_REF="{DPE_ADDRESS}"\n')
        (recipe / "request.json").write_text(f'{{"method_ref": "{DPE_ADDRESS}"}}', encoding="utf-8")
        assert find_addresses(tmp_path) == [
            RecipeAddress(address=ADDRESS, file=recipe / "README.md"),
            RecipeAddress(address=DPE_ADDRESS, file=recipe / "request.json"),
            RecipeAddress(address=DPE_ADDRESS, file=recipe / "run.sh"),
        ]
        assert recipe_problems(tmp_path) == []

    def test_an_address_closing_a_sentence_keeps_its_tag_without_the_full_stop(self, tmp_path: Path):
        _run_recipe(tmp_path, readme=f"It runs {DPE_ADDRESS}.\n")
        assert [found.address for found in find_addresses(tmp_path)] == [DPE_ADDRESS]
        assert recipe_problems(tmp_path) == []

    def test_catalog_ids_repository_links_and_other_hosts_are_not_addresses(self, tmp_path: Path):
        readme = (
            "Point every door at `mt_…`, or at mt_ca0aa9d3-61ac-4db1-8b46-fb0cc75787df.\n"
            "Install [the plugin](https://github.com/Pipelex/pipelex-plugins), read "
            "https://github.com/Pipelex/methods/tree/v0.1.1/methods/invoice_extraction, and mail noreply@github.com.\n"
            "https://api.github.com/repos/Pipelex/methods@main is the API, not an address.\n"
        )
        _run_recipe(tmp_path, readme=readme)
        assert find_addresses(tmp_path) == []
        assert recipe_problems(tmp_path) == []

    @pytest.mark.parametrize("tag", ["main", "beta", "v0.18", "v0.18.0-rc.1"])
    def test_an_address_without_a_release_tag_is_a_problem(self, tmp_path: Path, tag: str):
        floating = f"github.com/Pipelex/pipelex-cookbook/extract_dpe@{tag}"
        _run_recipe(tmp_path, readme=f"Run `{floating}` on the sample.\n")
        [problem] = recipe_problems(tmp_path)
        assert problem == (
            f"recipes/run/http/README.md: {floating!r} is not an address pinned to a release tag (github.com/<owner>/<repo>/<name>@vX.Y.Z)"
        )

    def test_generated_trees_installed_packages_npm_locks_and_other_files_are_not_read_for_addresses(self, tmp_path: Path):
        recipe = _python_recipe(tmp_path)
        floating = "github.com/Pipelex/methods/invoice_extraction@main"
        (recipe / "generated" / "invoice_extraction" / "README.md").write_text(floating, encoding="utf-8")
        (recipe / "node_modules" / "some-package").mkdir(parents=True)
        (recipe / "node_modules" / "some-package" / "README.md").write_text(floating, encoding="utf-8")
        (recipe / "package-lock.json").write_text(f'{{"note": "{floating}"}}', encoding="utf-8")
        (recipe / "NOTES.md").write_text(floating, encoding="utf-8")
        assert find_addresses(tmp_path) == []
        assert recipe_problems(tmp_path) == []

    def test_the_addresses_to_validate_gather_sidecars_and_files_by_recipe(self, tmp_path: Path):
        _python_recipe(tmp_path)
        _run_recipe(tmp_path, readme=f"Run `{ADDRESS}`, or `{DPE_ADDRESS}`.\n", script=f'METHOD_REF="{DPE_ADDRESS}"\n')
        assert recipe_addresses(tmp_path) == {
            ADDRESS: ["recipes/code/python/batch", "recipes/run/http"],
            DPE_ADDRESS: ["recipes/run/http"],
        }


class TestShellScripts:
    def test_a_shell_script_that_parses_is_clean(self, tmp_path: Path):
        recipe = _run_recipe(tmp_path, readme="A recipe.\n", script='#!/bin/sh\nset -u\nif [ -n "${1:-}" ]; then echo "$1"; fi\n')
        assert shell_scripts(tmp_path) == [recipe / "run.sh"]
        assert recipe_problems(tmp_path) == []

    def test_a_shell_script_that_does_not_parse_is_a_problem(self, tmp_path: Path):
        _run_recipe(tmp_path, readme="A recipe.\n", script='#!/bin/sh\nif [ -n "$1" ]; then echo started\n')
        [problem] = recipe_problems(tmp_path)
        assert problem.startswith("recipes/run/http/run.sh: `sh -n` cannot parse it: ")

    def test_shell_scripts_in_installed_packages_are_left_out(self, tmp_path: Path):
        recipe = _run_recipe(tmp_path, readme="A recipe.\n")
        vendored = recipe / "node_modules" / "some-package"
        vendored.mkdir(parents=True)
        (vendored / "install.sh").write_text("if then\n", encoding="utf-8")
        assert shell_scripts(tmp_path) == []
        assert recipe_problems(tmp_path) == []
