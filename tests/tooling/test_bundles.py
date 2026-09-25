from pathlib import Path

import pytest

from scripts.bundles import DeclaredOutput, declared_main_output
from scripts.contract import Contract, ContractOutput
from scripts.cookbook import load_cookbook
from scripts.exceptions import CookbookLayoutError
from tests.tooling.test_data import WIDGETS_BUNDLE, WIDGETS_CONTRACT, MakeCookbook


def _write_bundles(tmp_path: Path, *bundles: str) -> list[Path]:
    paths: list[Path] = []
    for index, bundle in enumerate(bundles):
        path = tmp_path / f"bundle_{index}.mthds"
        path.write_text(bundle, encoding="utf-8")
        paths.append(path)
    return paths


def _bundle(*, output: str, domain: str = "widgets", concepts: str = 'WidgetList = "Every widget"\n') -> str:
    return f'domain = "{domain}"\n\n[concept]\n{concepts}\n[pipe.extract_widgets]\ntype = "PipeLLM"\noutput = "{output}"\nprompt = "List them."\n'


def _replace_contract(root: Path, contract: Contract) -> None:
    (root / "methods" / "extract_widgets" / "contract.json").write_text(contract.to_json(), encoding="utf-8")


class TestDeclaredMainOutput:
    @pytest.mark.parametrize(
        ("output", "expected"),
        [
            ("WidgetList", DeclaredOutput(pipe="widgets.extract_widgets", concept="widgets.WidgetList", multiplicity="single")),
            ("WidgetList?", DeclaredOutput(pipe="widgets.extract_widgets", concept="widgets.WidgetList", multiplicity="single")),
            ("WidgetList[1]", DeclaredOutput(pipe="widgets.extract_widgets", concept="widgets.WidgetList", multiplicity="single")),
            ("WidgetList[]", DeclaredOutput(pipe="widgets.extract_widgets", concept="widgets.WidgetList", multiplicity="variable")),
            ("WidgetList[3]", DeclaredOutput(pipe="widgets.extract_widgets", concept="widgets.WidgetList", multiplicity="fixed", item_count=3)),
            ("Text", DeclaredOutput(pipe="widgets.extract_widgets", concept="native.Text", multiplicity="single")),
            ("Text[]", DeclaredOutput(pipe="widgets.extract_widgets", concept="native.Text", multiplicity="variable")),
            ("catalogue.Page", DeclaredOutput(pipe="widgets.extract_widgets", concept="catalogue.Page", multiplicity="single")),
        ],
    )
    def test_the_output_is_read_as_the_contract_records_it(self, tmp_path: Path, output: str, expected: DeclaredOutput):
        paths = _write_bundles(tmp_path, _bundle(output=output))
        assert declared_main_output(bundle_paths=paths, main_pipe="extract_widgets") == expected

    def test_a_native_code_wins_over_a_concept_of_the_domain(self, tmp_path: Path):
        paths = _write_bundles(tmp_path, _bundle(output="Text", concepts='Text = "A text of our own"\n'))
        assert declared_main_output(bundle_paths=paths, main_pipe="extract_widgets").concept == "native.Text"

    def test_a_concept_declared_in_another_file_of_the_domain_resolves(self, tmp_path: Path):
        paths = _write_bundles(
            tmp_path,
            _bundle(output="Widget", concepts=""),
            'domain = "widgets"\n\n[concept]\nWidget = "A widget"\n',
        )
        assert declared_main_output(bundle_paths=paths, main_pipe="extract_widgets").concept == "widgets.Widget"

    def test_a_bare_concept_of_another_domain_is_refused(self, tmp_path: Path):
        paths = _write_bundles(
            tmp_path,
            _bundle(output="Widget", concepts=""),
            'domain = "gadgets"\n\n[concept]\nWidget = "A widget"\n',
        )
        with pytest.raises(CookbookLayoutError, match="neither a native concept nor one of the domain `widgets`"):
            declared_main_output(bundle_paths=paths, main_pipe="extract_widgets")

    def test_a_concept_of_another_package_is_refused(self, tmp_path: Path):
        paths = _write_bundles(tmp_path, _bundle(output="scoring->scoring.Score"))
        with pytest.raises(CookbookLayoutError, match="a concept of another package"):
            declared_main_output(bundle_paths=paths, main_pipe="extract_widgets")

    @pytest.mark.parametrize("copies", [0, 2])
    def test_the_main_pipe_must_be_declared_exactly_once(self, tmp_path: Path, copies: int):
        paths = _write_bundles(tmp_path, *([_bundle(output="WidgetList")] * copies), 'domain = "widgets"\n')
        with pytest.raises(CookbookLayoutError, match=f"is declared in {copies} of the package's .mthds files"):
            declared_main_output(bundle_paths=paths, main_pipe="extract_widgets")


class TestContractAgainstBundles:
    def test_a_contract_naming_another_concept_of_the_package_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        # CataloguePage exists in the package, so its generated types would hold a parser for it: only the main pipe's output tells them apart.
        _replace_contract(
            root, WIDGETS_CONTRACT.model_copy(update={"output": ContractOutput(concept="widgets.CataloguePage", multiplicity="single")})
        )
        with pytest.raises(
            CookbookLayoutError, match=r"returns one `widgets.CataloguePage`, .* returning one `widgets.WidgetList`: run `make refresh`"
        ):
            load_cookbook(root)

    def test_a_contract_with_another_multiplicity_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        _replace_contract(root, WIDGETS_CONTRACT.model_copy(update={"output": ContractOutput(concept="widgets.WidgetList", multiplicity="variable")}))
        with pytest.raises(CookbookLayoutError, match="returns a list of `widgets.WidgetList`"):
            load_cookbook(root)

    def test_a_contract_naming_another_pipe_is_refused(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        _replace_contract(root, WIDGETS_CONTRACT.model_copy(update={"pipe": "catalogue.extract_widgets"}))
        with pytest.raises(CookbookLayoutError, match="says the main pipe `catalogue.extract_widgets`"):
            load_cookbook(root)

    def test_a_bundle_changed_without_a_refresh_is_refused_until_contracts_are_left_unread(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        bundle_path = root / "methods" / "extract_widgets" / "bundle.mthds"
        bundle_path.write_text(WIDGETS_BUNDLE.replace('output = "WidgetList"', 'output = "Widget[]"'), encoding="utf-8")
        with pytest.raises(CookbookLayoutError, match="declare `widgets.extract_widgets` returning a list of `widgets.Widget`"):
            load_cookbook(root)
        # `make refresh` loads without the snapshots, so it can take the contract again.
        assert [package.contract for package in load_cookbook(root, read_contracts=False).packages] == [None, None]
