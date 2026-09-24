from typing import Any

import pytest

from scripts.contract import Contract, ContractField, ContractInput, ContractOutput, project_contract, schema_type
from scripts.exceptions import CookbookLayoutError

# A verdict of `POST /v1/validate`, cut down to what the projection reads, in the shape production answered for extract_gantt.
GANTT_VERDICT: dict[str, Any] = {
    "is_valid": True,
    "pipe_io_contracts": {
        "gantt.extract_gantt_by_steps": {
            "inputs": {
                "gantt_chart_image": {
                    "concept_ref": "gantt.GanttChartImage",
                    "presence": "plain",
                    "multiplicity": "single",
                    "item_count": None,
                    "json_schema": {"description": "A gantt chart detailing a project timeline", "type": "object"},
                }
            },
            "output": {
                "concept_ref": "gantt.GanttChart",
                "multiplicity": "single",
                "item_count": None,
                "optional": False,
                "json_schema": {
                    "description": "A gantt chart transcript fully detailing the contents of the chart",
                    "properties": {
                        "tasks": {
                            "anyOf": [{"items": {"$ref": "#/$defs/gantt__GanttTaskDetails"}, "type": "array"}, {"type": "null"}],
                            "default": None,
                            "description": "The list of tasks in the gantt chart",
                        },
                        "title": {"type": "string", "description": "The chart's title"},
                    },
                    "required": ["title"],
                    "type": "object",
                },
            },
        },
        "gantt.extract_gantt_timescale": {"inputs": {}, "output": {"concept_ref": "gantt.GanttTimescaleDescription", "multiplicity": "single"}},
    },
    "input_form": {"gantt.extract_gantt_by_steps": {"fields": [{"kind": "image", "name": "gantt_chart_image"}]}},
}


class TestContract:
    def test_the_main_pipe_is_projected_from_the_verdict(self):
        contract = project_contract(verdict=GANTT_VERDICT, main_pipe="extract_gantt_by_steps")
        assert contract == Contract(
            pipe="gantt.extract_gantt_by_steps",
            inputs=[
                ContractInput(
                    name="gantt_chart_image",
                    concept="gantt.GanttChartImage",
                    kind="image",
                    description="A gantt chart detailing a project timeline",
                    multiplicity="single",
                    required=True,
                )
            ],
            output=ContractOutput(
                concept="gantt.GanttChart",
                description="A gantt chart transcript fully detailing the contents of the chart",
                multiplicity="single",
                fields=[
                    ContractField(name="tasks", type="list[GanttTaskDetails]", description="The list of tasks in the gantt chart", required=False),
                    ContractField(name="title", type="text", description="The chart's title", required=True),
                ],
            ),
        )

    def test_a_snapshot_round_trips_through_its_json(self):
        contract = project_contract(verdict=GANTT_VERDICT, main_pipe="extract_gantt_by_steps")
        assert Contract.model_validate_json(contract.to_json()) == contract

    def test_a_main_pipe_missing_from_the_verdict_is_refused(self):
        with pytest.raises(CookbookLayoutError, match="matches 0 of the validated pipes"):
            project_contract(verdict=GANTT_VERDICT, main_pipe="extract_gantt_directly")

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
