"""The shape check: whether a run's output has the shape its method's contract declares, read from the contract alone.

The check never compares content. It holds the output to four things: its envelope matches the output's multiplicity, one object for a single
output and a list of objects for a list output; every required field is present and not null; every value matches its field's type expression;
and no key the contract does not name appears at the top of an object. A list output arrives as the `{"items": [...]}` envelope the runtime
writes, and a bare list is read the same way, as the page snippets read one. A contract that names no field, such as one taken before its
concept had a structure, holds the output to its envelope only.

A type expression is what `contract.json` records: `text`, `date`, `datetime`, `integer`, `number`, `boolean`, `object`, `any`, a concept's
name, `list[<type>]`, or branches joined by ` or `. A concept is serialised as an object, whatever its fields, and its own fields are not read.
"""

from datetime import date, datetime

from pydantic import JsonValue

from scripts.contract import Contract, ContractField, type_branches

# The key a list output's envelope carries its items under, as the runtime serialises a list.
LIST_ENVELOPE_KEY = "items"
_LIST_MULTIPLICITIES = frozenset({"variable", "fixed"})
_LIST_PREFIX = "list["
_LIST_SUFFIX = "]"


def shape_problems(*, contract: Contract, output: JsonValue) -> list[str]:
    """Every way `output` departs from the shape `contract` declares for the main pipe's output, each said in a sentence; empty when it has it.

    Args:
        contract: The method's contract, as `contract.json` records it.
        output: The run's main output, as the results relay it.
    """
    declared = contract.output
    if declared.multiplicity not in _LIST_MULTIPLICITIES:
        if not isinstance(output, dict):
            return [f"the output is {_kind(output)}, where `{declared.concept}` is one object"]
        return _object_problems(fields=declared.fields, value=output, where="the output")
    items = _list_items(output)
    if items is None:
        return [f"the output is {_kind(output)}, where a list of `{declared.concept}` is a list or an object holding it under `{LIST_ENVELOPE_KEY}`"]
    problems: list[str] = []
    if declared.item_count is not None and len(items) != declared.item_count:
        problems.append(f"the output holds {len(items)} items, where the contract declares {declared.item_count}")
    for index, item in enumerate(items):
        where = f"item {index} of the output"
        if isinstance(item, dict):
            problems.extend(_object_problems(fields=declared.fields, value=item, where=where))
        else:
            problems.append(f"{where} is {_kind(item)}, where `{declared.concept}` is an object")
    return problems


def value_matches(*, type_expression: str, value: JsonValue) -> bool:
    """Whether a value, not null, has the type a contract's type expression names."""
    branches = type_branches(type_expression)
    if len(branches) > 1:
        return any(value_matches(type_expression=branch, value=value) for branch in branches)
    if type_expression.startswith(_LIST_PREFIX) and type_expression.endswith(_LIST_SUFFIX):
        item_type = type_expression.removeprefix(_LIST_PREFIX).removesuffix(_LIST_SUFFIX)
        return isinstance(value, list) and all(item is not None and value_matches(type_expression=item_type, value=item) for item in value)
    match type_expression:
        case "text":
            return isinstance(value, str)
        case "date":
            return isinstance(value, str) and _parses(value, parser=date)
        case "datetime":
            return isinstance(value, str) and _parses(value, parser=datetime)
        case "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        case "number":
            return isinstance(value, int | float) and not isinstance(value, bool)
        case "boolean":
            return isinstance(value, bool)
        case "any":
            return True
        case _:
            # `object`, and any concept's name: a concept is serialised as an object.
            return isinstance(value, dict)


def _object_problems(*, fields: list[ContractField], value: dict[str, JsonValue], where: str) -> list[str]:
    if not fields:
        return []
    problems: list[str] = []
    known = {contract_field.name for contract_field in fields}
    for contract_field in fields:
        field_value = value.get(contract_field.name)
        if field_value is None:
            if contract_field.required:
                problems.append(f"{where} has no `{contract_field.name}`, which the contract requires")
            continue
        if not value_matches(type_expression=contract_field.type, value=field_value):
            problems.append(f"`{contract_field.name}` of {where} is {_kind(field_value)}, where the contract declares `{contract_field.type}`")
    for key in value:
        if key not in known:
            problems.append(f"{where} has a key `{key}` the contract does not name")
    return problems


def _list_items(output: JsonValue) -> list[JsonValue] | None:
    """The items of a list output, given bare or in its envelope, or None when the output is neither."""
    if isinstance(output, list):
        return output
    if isinstance(output, dict) and list(output) == [LIST_ENVELOPE_KEY]:
        items = output[LIST_ENVELOPE_KEY]
        return items if isinstance(items, list) else None
    return None


def _parses(text: str, *, parser: type[date]) -> bool:
    """Whether `parser`, `date` or `datetime`, reads the text as an ISO 8601 value."""
    try:
        parser.fromisoformat(text)
    except ValueError:
        return False
    return True


def _kind(value: JsonValue) -> str:
    """What a JSON value is, as a problem names it."""
    match value:
        case None:
            return "null"
        case bool():
            return "a boolean"
        case int() | float():
            return "a number"
        case str():
            return "a text"
        case list():
            return "a list"
        case dict():
            return "an object"
