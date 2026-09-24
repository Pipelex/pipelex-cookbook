"""Read a method's answer key, `key.md`, in the format of the Pipelex lab skill.

A key has fixed sections (`## Planted facts`, `## Must`, `## Must not`, `## Also acceptable`, `## Pass bar`), and every line of the first four
carries a label such as `M3.` so that a run can be scored line by line. The method page renders the `## Must` lines as "What you get".
"""

import re

from pydantic import BaseModel, ConfigDict, Field

from scripts.exceptions import CookbookLayoutError

_SECTION_PATTERN = re.compile(r"^##\s+(?P<title>.+?)\s*$")
_LINE_PATTERN = re.compile(r"^(?P<label>[A-Z]\d+)\.\s+(?P<text>.+)$")

_SECTION_FIELDS = {
    "planted facts": "planted_facts",
    "must": "must",
    "must not": "must_not",
    "also acceptable": "also_acceptable",
}


class KeyLine(BaseModel):
    """One labelled line of an answer key, such as `M1. \\`tasks\\` holds the chart's twelve tasks`."""

    model_config = ConfigDict(frozen=True)

    label: str
    text: str


class AnswerKey(BaseModel):
    """The right answers for one method's sample, written before the method ran on it."""

    model_config = ConfigDict(frozen=True)

    case: str
    planted_facts: list[KeyLine] = Field(default_factory=list[KeyLine])
    must: list[KeyLine] = Field(default_factory=list[KeyLine])
    must_not: list[KeyLine] = Field(default_factory=list[KeyLine])
    also_acceptable: list[KeyLine] = Field(default_factory=list[KeyLine])
    pass_bar: str = ""


def parse_key(text: str, *, source: str) -> AnswerKey:
    """Parse the text of a `key.md`.

    Args:
        text: The file's contents.
        source: Where the text came from, named in every error.

    Returns:
        The key, its labelled lines grouped by section.

    Raises:
        CookbookLayoutError: The key has no `# Key:` title or no `## Must` line.
    """
    case: str | None = None
    sections: dict[str, list[KeyLine]] = {field_name: [] for field_name in _SECTION_FIELDS.values()}
    pass_bar_lines: list[str] = []
    current_section: str | None = None
    current_lines: list[KeyLine] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if case is None and line.startswith("# Key:"):
            case = line.removeprefix("# Key:").strip()
            continue
        section_match = _SECTION_PATTERN.match(line)
        if section_match:
            section_title = section_match.group("title").strip().lower()
            current_section = section_title
            field_name = _SECTION_FIELDS.get(section_title)
            current_lines = sections[field_name] if field_name else None
            continue
        if not line:
            continue
        if current_section == "pass bar":
            pass_bar_lines.append(line)
            continue
        if current_lines is None:
            continue
        line_match = _LINE_PATTERN.match(line)
        if line_match:
            current_lines.append(KeyLine(label=line_match.group("label"), text=line_match.group("text")))
        elif current_lines:
            # A line with no label continues the labelled line above it.
            previous = current_lines[-1]
            current_lines[-1] = KeyLine(label=previous.label, text=f"{previous.text} {line}")

    if case is None:
        msg = f"{source}: an answer key opens with a `# Key: <case>` title"
        raise CookbookLayoutError(msg)
    if not sections["must"]:
        msg = f"{source}: an answer key needs at least one labelled line under `## Must`"
        raise CookbookLayoutError(msg)
    return AnswerKey(
        case=case,
        planted_facts=sections["planted_facts"],
        must=sections["must"],
        must_not=sections["must_not"],
        also_acceptable=sections["also_acceptable"],
        pass_bar=" ".join(pass_bar_lines),
    )
