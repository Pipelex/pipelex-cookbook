import json
from typing import Any

import pytest

from scripts.contract import Contract, ContractField, ContractInput, ContractOutput, project_contract, schema_type
from scripts.exceptions import CookbookLayoutError

# A verdict of `POST /v1/validate`, cut down to what the projection reads, in the shape production answers, for the fixture cookbook's widget
# extraction: its main pipe beside another pipe, an optional list field and a required text field.
WIDGETS_VERDICT: dict[str, Any] = {
    "is_valid": True,
    "pipe_io_contracts": {
        "widgets.extract_widgets": {
            "inputs": {
                "catalogue": {
                    "concept_ref": "widgets.CataloguePage",
                    "presence": "plain",
                    "multiplicity": "single",
                    "item_count": None,
                    "json_schema": {"description": "A page of a widget catalogue", "type": "object"},
                }
            },
            "output": {
                "concept_ref": "widgets.WidgetList",
                "multiplicity": "single",
                "item_count": None,
                "optional": False,
                "json_schema": {
                    "description": "Every widget on the page",
                    "properties": {
                        "widgets": {
                            "anyOf": [{"items": {"$ref": "#/$defs/widgets__Widget"}, "type": "array"}, {"type": "null"}],
                            "default": None,
                            "description": "The widgets, in page order",
                        },
                        "title": {"type": "string", "description": "The page's title"},
                    },
                    "required": ["title"],
                    "type": "object",
                },
            },
        },
        "widgets.read_page_number": {"inputs": {}, "output": {"concept_ref": "widgets.PageNumber", "multiplicity": "single"}},
    },
    "input_form": {"widgets.extract_widgets": {"fields": [{"kind": "image", "name": "catalogue"}]}},
}


class TestContract:
    def test_the_main_pipe_is_projected_from_the_verdict(self):
        contract = project_contract(verdict=WIDGETS_VERDICT, main_pipe="extract_widgets")
        assert contract == Contract(
            pipe="widgets.extract_widgets",
            inputs=[
                ContractInput(
                    name="catalogue",
                    concept="widgets.CataloguePage",
                    kind="image",
                    description="A page of a widget catalogue",
                    multiplicity="single",
                    required=True,
                )
            ],
            output=ContractOutput(
                concept="widgets.WidgetList",
                description="Every widget on the page",
                multiplicity="single",
                fields=[
                    ContractField(name="widgets", type="list[Widget]", description="The widgets, in page order", required=False),
                    ContractField(name="title", type="text", description="The page's title", required=True),
                ],
            ),
        )

    def test_a_list_input_records_the_kind_of_its_items_which_no_other_input_writes(self):
        main = WIDGETS_VERDICT["pipe_io_contracts"]["widgets.extract_widgets"]
        pages: dict[str, Any] = {"concept_ref": "native.Document", "presence": "plain", "multiplicity": "variable", "json_schema": {}}
        verdict: dict[str, Any] = {
            **WIDGETS_VERDICT,
            "pipe_io_contracts": {"widgets.extract_widgets": {**main, "inputs": {**main["inputs"], "pages": pages}}},
            "input_form": {
                "widgets.extract_widgets": {
                    "fields": [
                        {"kind": "image", "name": "catalogue"},
                        {"kind": "list", "name": "pages", "item": {"kind": "document", "concept_ref": "native.Document"}},
                    ]
                }
            },
        }
        contract = project_contract(verdict=verdict, main_pipe="extract_widgets")
        catalogue, pages_input = contract.inputs
        assert (pages_input.kind, pages_input.item_kind, pages_input.sample_kind) == ("list", "document", "document")
        assert (catalogue.item_kind, catalogue.sample_kind) == (None, "image")
        written = json.loads(contract.to_json())
        assert ["item_kind" in written_input for written_input in written["inputs"]] == [False, True]
        assert Contract.model_validate_json(contract.to_json()) == contract

    def test_a_snapshot_round_trips_through_its_json(self):
        contract = project_contract(verdict=WIDGETS_VERDICT, main_pipe="extract_widgets")
        assert Contract.model_validate_json(contract.to_json()) == contract

    def test_a_main_pipe_missing_from_the_verdict_is_refused(self):
        with pytest.raises(CookbookLayoutError, match="matches 0 of the validated pipes"):
            project_contract(verdict=WIDGETS_VERDICT, main_pipe="extract_widgets_directly")

    @pytest.mark.parametrize(
        ("schema", "expected"),
        [
            ({"type": "string"}, "text"),
            ({"type": "string", "format": "date"}, "date"),
            ({"type": "string", "format": "date-time"}, "datetime"),
            ({"type": "integer"}, "integer"),
            ({"type": "array", "items": {"type": "string"}}, "list[text]"),
            ({"$ref": "#/$defs/invoices__LineItem"}, "LineItem"),
            ({"anyOf": [{"type": "number"}, {"type": "null"}]}, "number"),
            ({"anyOf": [{"type": "number"}, {"type": "string"}]}, "number or text"),
        ],
    )
    def test_schema_types(self, schema: dict[str, Any], expected: str):
        assert schema_type(schema) == expected

    def test_a_list_output_is_described_by_its_item_fields(self):
        verdict: dict[str, object] = {
            "is_valid": True,
            "pipe_io_contracts": {
                "words.list_words": {
                    "inputs": {"text": {"concept_ref": "native.Text", "presence": "required", "multiplicity": "single", "json_schema": {}}},
                    "output": {
                        "concept_ref": "words.Word",
                        "multiplicity": "variable",
                        "json_schema": {
                            "properties": {"items": {"type": "array", "items": {"$ref": "#/$defs/Word"}}},
                            "$defs": {
                                "Word": {
                                    "description": "A word of the text",
                                    "properties": {"spelling": {"type": "string", "description": "The word as written"}},
                                    "required": ["spelling"],
                                }
                            },
                        },
                    },
                }
            },
        }
        contract = project_contract(verdict=verdict, main_pipe="list_words")
        assert contract.output.description == "A word of the text"
        assert [(field.name, field.type, field.required) for field in contract.output.fields] == [("spelling", "text", True)]

    def test_a_single_output_whose_only_field_is_items_keeps_its_own_fields(self):
        verdict: dict[str, object] = {
            "is_valid": True,
            "pipe_io_contracts": {
                "shop.fill_basket": {
                    "inputs": {"text": {"concept_ref": "native.Text", "presence": "required", "multiplicity": "single", "json_schema": {}}},
                    "output": {
                        "concept_ref": "shop.Basket",
                        "multiplicity": "single",
                        "json_schema": {
                            "description": "A basket of products",
                            "properties": {"items": {"type": "array", "description": "The products", "items": {"$ref": "#/$defs/Product"}}},
                            "required": ["items"],
                            "$defs": {"Product": {"description": "A product", "properties": {"name": {"type": "string"}}}},
                        },
                    },
                }
            },
        }
        contract = project_contract(verdict=verdict, main_pipe="fill_basket")
        assert contract.output.description == "A basket of products"
        assert [field.name for field in contract.output.fields] == ["items"]
