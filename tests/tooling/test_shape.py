import copy
from pathlib import Path

import pytest
from pydantic import JsonValue

from scripts.contract import Contract, ContractField, ContractOutput, load_contract
from scripts.shape import shape_problems, value_matches
from tests.tooling.test_data import RIGHT_OUTPUTS, WORDS_CONTRACT

METHODS_DIR = Path(__file__).resolve().parents[2] / "methods"
# Every method the cookbook holds, so that a method added without an output in RIGHT_OUTPUTS fails the first test below.
METHOD_NAMES = sorted(directory.name for directory in METHODS_DIR.iterdir() if (directory / "contract.json").is_file())
_LIST_MULTIPLICITIES = ("variable", "fixed")


def _contract(name: str) -> Contract:
    return load_contract(METHODS_DIR / name / "contract.json")


def _is_list(contract: Contract) -> bool:
    return contract.output.multiplicity in _LIST_MULTIPLICITIES


def _first_object(*, contract: Contract, output: JsonValue) -> dict[str, JsonValue]:
    """The object a problem in the output names first: the output itself, or the first item of a list output's envelope."""
    target = output["items"][0] if _is_list(contract) and isinstance(output, dict) and isinstance(output["items"], list) else output
    assert isinstance(target, dict)
    return target


def _where(contract: Contract) -> str:
    return "item 0 of the output" if _is_list(contract) else "the output"


def _wrong_value(type_expression: str) -> JsonValue:
    """A value that is not null and is not of the type the expression names."""
    if type_expression.startswith("list[") and type_expression.endswith("]"):
        return [_wrong_value(type_expression.removeprefix("list[").removesuffix("]"))]
    match type_expression:
        case "text":
            return 42
        case "date":
            return "29/03/2022"
        case "number":
            return "560"
        case _:
            # A concept's name: a concept is an object, and a text is not one.
            return "a text"


class TestShape:
    def test_every_method_has_a_hand_built_output(self):
        assert sorted(RIGHT_OUTPUTS) == METHOD_NAMES

    @pytest.mark.parametrize("name", METHOD_NAMES)
    def test_a_right_output_has_no_problem(self, name: str):
        assert shape_problems(contract=_contract(name), output=RIGHT_OUTPUTS[name]) == []

    @pytest.mark.parametrize("name", METHOD_NAMES)
    def test_a_value_of_the_wrong_type_is_named_with_its_field(self, name: str):
        contract = _contract(name)
        for contract_field in contract.output.fields:
            output = copy.deepcopy(RIGHT_OUTPUTS[name])
            _first_object(contract=contract, output=output)[contract_field.name] = _wrong_value(contract_field.type)
            [problem] = shape_problems(contract=contract, output=output)
            assert problem.startswith(f"`{contract_field.name}` of {_where(contract)} is ")
            assert problem.endswith(f", where the contract declares `{contract_field.type}`")

    @pytest.mark.parametrize("name", METHOD_NAMES)
    def test_a_required_field_missing_or_null_is_named_and_an_optional_one_is_not(self, name: str):
        contract = _contract(name)
        for contract_field in contract.output.fields:
            expected = [f"{_where(contract)} has no `{contract_field.name}`, which the contract requires"] if contract_field.required else []
            missing = copy.deepcopy(RIGHT_OUTPUTS[name])
            del _first_object(contract=contract, output=missing)[contract_field.name]
            null = copy.deepcopy(RIGHT_OUTPUTS[name])
            _first_object(contract=contract, output=null)[contract_field.name] = None
            assert shape_problems(contract=contract, output=missing) == expected
            assert shape_problems(contract=contract, output=null) == expected

    @pytest.mark.parametrize("name", METHOD_NAMES)
    def test_a_key_the_contract_does_not_name_is_named(self, name: str):
        contract = _contract(name)
        output = copy.deepcopy(RIGHT_OUTPUTS[name])
        _first_object(contract=contract, output=output)["surprise"] = "not in the contract"
        assert shape_problems(contract=contract, output=output) == [f"{_where(contract)} has a key `surprise` the contract does not name"]

    @pytest.mark.parametrize("name", METHOD_NAMES)
    def test_an_output_in_the_wrong_envelope_is_one_problem(self, name: str):
        contract = _contract(name)
        concept = contract.output.concept
        output = RIGHT_OUTPUTS[name]
        if _is_list(contract):
            expected = f"the output is an object, where a list of `{concept}` is a list or an object holding it under `items`"
            assert shape_problems(contract=contract, output=_first_object(contract=contract, output=output)) == [expected]
        else:
            assert shape_problems(contract=contract, output=[output]) == [f"the output is a list, where `{concept}` is one object"]

    @pytest.mark.parametrize("name", [name for name in METHOD_NAMES if _is_list(_contract(name))])
    def test_a_list_output_is_read_bare_as_in_its_envelope(self, name: str):
        output = RIGHT_OUTPUTS[name]
        assert isinstance(output, dict)
        assert shape_problems(contract=_contract(name), output=output["items"]) == []

    def test_a_fixed_list_holds_the_count_its_contract_declares_and_every_item_is_an_object(self):
        fields = [ContractField(name="text", type="text", required=True)]
        contract = Contract(pipe="pairs.make_pair", output=ContractOutput(concept="native.Text", multiplicity="fixed", item_count=2, fields=fields))
        assert shape_problems(contract=contract, output={"items": [{"text": "one"}, {"text": "two"}]}) == []
        assert shape_problems(contract=contract, output={"items": [{"text": "one"}, {"text": "two"}, "three"]}) == [
            "the output holds 3 items, where the contract declares 2",
            "item 2 of the output is a text, where `native.Text` is an object",
        ]

    def test_a_contract_naming_no_field_holds_the_output_to_its_envelope_only(self):
        assert WORDS_CONTRACT.output.fields == []
        assert shape_problems(contract=WORDS_CONTRACT, output={"anything": 1}) == []
        assert shape_problems(contract=WORDS_CONTRACT, output="four words") == ["the output is a text, where `native.Text` is one object"]

    @pytest.mark.parametrize(
        ("type_expression", "right", "wrong"),
        [
            ("text", "Paris", 42),
            ("date", "2022-03-29", "29/03/2022"),
            ("datetime", "2026-09-26T10:00:00Z", "2026-13-01T10:00:00"),
            ("integer", 21, 21.5),
            ("integer", 21, True),
            ("number", 560.0, "560"),
            ("number", 18, False),
            ("boolean", True, 0),
            ("object", {"any": "field"}, ["a list"]),
            ("any", ["a list"], None),
            ("list[text]", [], ["a", 3]),
            ("list[text]", ["a", "b"], ["a", None]),
            ("list[text]", ["a"], "a"),
            ("list[DocumentPassage]", [{"quote": "…"}], [{"quote": "…"}, "…"]),
            ("Employee", {"full_name": "Alex Martin"}, "Alex Martin"),
            ("HtmlContent", {"inner_html": "<p>…</p>"}, ["<p>…</p>"]),
            ("text or integer", 3, 3.5),
            # A list whose items have branches keeps its branches inside its brackets, as `schema_type` writes it.
            ("list[text or integer]", ["a", 3], ["a", 3.5]),
            ("list[text] or integer", ["a"], [3]),
            ("list[text] or list[integer]", [3], ["a", 3]),
            ("list[list[text or integer]]", [["a", 3]], [["a", 3.5]]),
        ],
    )
    def test_each_type_expression_takes_its_own_values_only(self, type_expression: str, right: JsonValue, wrong: JsonValue):
        assert value_matches(type_expression=type_expression, value=right)
        if wrong is not None:
            assert not value_matches(type_expression=type_expression, value=wrong)
