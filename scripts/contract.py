"""A method's contract: what its main pipe takes and what it returns, as production reports it.

The contract comes from the validation verdict of `POST /v1/validate`: its `pipe_io_contracts` carries each pipe's inputs and output with their
JSON schemas, and its `input_form` view carries each input's kind (an image, a document, a text). `make refresh` projects the main pipe's entry into
the small, stable shape below and commits it as `contract.json` beside the package, so the renderer reads committed files and never the network.
"""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from scripts.exceptions import CookbookLayoutError

CONTRACT_FILE = "contract.json"
# How a JSON schema refers to one of its own definitions.
_DEFS_PREFIX = "#/$defs/"


class ContractInput(BaseModel):
    """One input of the main pipe."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    concept: str = Field(description="The concept the input expects, domain-qualified, such as `gantt.GanttChartImage`")
    kind: str | None = Field(default=None, description="The input form's kind for the input, such as `image`, when the form names one")
    description: str | None = None
    multiplicity: str = Field(description="`single`, `variable` or `fixed`")
    item_count: int | None = None
    required: bool = True


class ContractField(BaseModel):
    """One top-level field of the output concept."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    type: str = Field(description="A type expression: `text`, `date`, `integer`, a concept name, or `list[<type>]`")
    description: str | None = None
    required: bool = False


class ContractOutput(BaseModel):
    """What the main pipe returns."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    concept: str
    description: str | None = None
    multiplicity: str
    item_count: int | None = None
    fields: list[ContractField] = Field(default_factory=list[ContractField])


class Contract(BaseModel):
    """The main pipe's contract, as committed in `contract.json`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pipe: str = Field(description="The main pipe's domain-qualified reference")
    inputs: list[ContractInput] = Field(default_factory=list[ContractInput])
    output: ContractOutput

    def to_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"


def load_contract(path: Path) -> Contract:
    """Read a committed `contract.json`.

    Raises:
        CookbookLayoutError: The file is not a contract.
    """
    try:
        return Contract.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        msg = f"{path}: not a contract snapshot, run `make refresh` to rewrite it:\n{exc}"
        raise CookbookLayoutError(msg) from exc


def short_concept(concept: str) -> str:
    """The concept's name without its domain: `gantt.GanttChart` becomes `GanttChart`."""
    return concept.rsplit(".", maxsplit=1)[-1]


def find_main_pipe_ref(*, pipe_refs: list[str], main_pipe: str) -> str:
    """Find the domain-qualified reference of the manifest's `main_pipe` among the verdict's pipes.

    Raises:
        CookbookLayoutError: No pipe, or several, carry that code.
    """
    matches = [pipe_ref for pipe_ref in pipe_refs if pipe_ref.rsplit(".", maxsplit=1)[-1] == main_pipe]
    if len(matches) != 1:
        msg = f"the manifest's main_pipe `{main_pipe}` matches {len(matches)} of the validated pipes ({', '.join(sorted(pipe_refs))})"
        raise CookbookLayoutError(msg)
    return matches[0]


def project_contract(*, verdict: Mapping[str, Any], main_pipe: str) -> Contract:
    """Project a valid verdict of `POST /v1/validate` onto the main pipe's contract.

    Args:
        verdict: The verdict's JSON body, requested with the `input_form` view.
        main_pipe: The manifest's `main_pipe`, a bare pipe code.

    Returns:
        The contract of the main pipe.

    Raises:
        CookbookLayoutError: The verdict does not describe the main pipe.
    """
    io_contracts = cast("dict[str, Any]", verdict.get("pipe_io_contracts") or {})
    pipe_ref = find_main_pipe_ref(pipe_refs=list(io_contracts), main_pipe=main_pipe)
    io_contract = cast("dict[str, Any]", io_contracts[pipe_ref])
    input_forms = cast("dict[str, Any]", verdict.get("input_form") or {})
    form_fields = cast("list[dict[str, Any]]", cast("dict[str, Any]", input_forms.get(pipe_ref) or {}).get("fields") or [])
    kinds_by_name: dict[str, str] = {}
    for form_field in form_fields:
        field_kind = form_field.get("kind")
        if isinstance(field_kind, str):
            kinds_by_name[str(form_field["name"])] = field_kind

    inputs: list[ContractInput] = []
    for input_name, input_contract in cast("dict[str, dict[str, Any]]", io_contract.get("inputs") or {}).items():
        input_schema = cast("dict[str, Any]", input_contract.get("json_schema") or {})
        inputs.append(
            ContractInput(
                name=input_name,
                concept=str(input_contract["concept_ref"]),
                kind=kinds_by_name.get(input_name),
                description=_optional_str(input_schema.get("description")),
                multiplicity=str(input_contract.get("multiplicity") or "single"),
                item_count=_optional_int(input_contract.get("item_count")),
                required=input_contract.get("presence") != "optional",
            )
        )

    output_contract = cast("dict[str, Any]", io_contract["output"])
    output_multiplicity = str(output_contract.get("multiplicity") or "single")
    output_schema = cast("dict[str, Any]", output_contract.get("json_schema") or {})
    if output_multiplicity != "single":
        output_schema = _item_schema(output_schema)
    required_fields = set(cast("list[str]", output_schema.get("required") or []))
    fields: list[ContractField] = []
    for field_name, field_schema in cast("dict[str, dict[str, Any]]", output_schema.get("properties") or {}).items():
        fields.append(
            ContractField(
                name=field_name,
                type=schema_type(field_schema),
                description=_optional_str(field_schema.get("description")),
                required=field_name in required_fields,
            )
        )
    return Contract(
        pipe=pipe_ref,
        inputs=inputs,
        output=ContractOutput(
            concept=str(output_contract["concept_ref"]),
            description=_optional_str(output_schema.get("description")),
            multiplicity=output_multiplicity,
            item_count=_optional_int(output_contract.get("item_count")),
            fields=fields,
        ),
    )


def _item_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """The schema a reader wants for a list output, whose schema wraps its items as `{"items": [<$ref>]}`: the item's schema."""
    properties = cast("dict[str, Any]", schema.get("properties") or {})
    if list(properties) != ["items"]:
        return schema
    reference = cast("dict[str, Any]", cast("dict[str, Any]", properties["items"]).get("items") or {}).get("$ref")
    definitions = cast("dict[str, Any]", schema.get("$defs") or {})
    if not isinstance(reference, str) or not reference.startswith(_DEFS_PREFIX):
        return schema
    item_schema = definitions.get(reference.removeprefix(_DEFS_PREFIX))
    return cast("dict[str, Any]", item_schema) if isinstance(item_schema, dict) else schema


def schema_type(schema: Mapping[str, Any]) -> str:
    """Reduce a field's JSON schema to a type expression the page can phrase.

    `$ref`s name concepts, whose `$defs` keys read `<domain>__<Concept>`; an optional field's `anyOf` with `null` reduces to its other branch.
    """
    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        branches = [cast("dict[str, Any]", branch) for branch in cast("list[Any]", any_of) if isinstance(branch, dict)]
        non_null = [branch for branch in branches if branch.get("type") != "null"]
        if len(non_null) == 1:
            return schema_type(non_null[0])
        return " or ".join(schema_type(branch) for branch in non_null) or "any"
    reference = schema.get("$ref")
    if isinstance(reference, str):
        definition_name = reference.rsplit("/", maxsplit=1)[-1]
        return definition_name.rsplit("__", maxsplit=1)[-1]
    schema_kind = schema.get("type")
    match schema_kind:
        case "string":
            match schema.get("format"):
                case "date":
                    return "date"
                case "date-time":
                    return "datetime"
                case _:
                    return "text"
        case "integer":
            return "integer"
        case "number":
            return "number"
        case "boolean":
            return "boolean"
        case "array":
            items = schema.get("items")
            item_type = schema_type(cast("dict[str, Any]", items)) if isinstance(items, dict) else "any"
            return f"list[{item_type}]"
        case "object":
            return "object"
        case _:
            return "any"


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None
