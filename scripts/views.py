"""What a method page shows of its sample and of its output, as Markdown computed from the contract, the sample records and the snapshot.

The sample is shown by the kind the contract gives each input: an image embedded, a document as its first-page preview linking to the file, prose
as a quotation, a structure as a field and value table. The output is shown as a reader would use it: a flat structure as a field and value
table, a list of structures as a table, Markdown text as Markdown under demoted headings and folded when long, HTML embedded without its head,
styles and scripts, and a file the output holds as an embedded image or a link. Two hints of `[methods.<name>.output]` in `cookbook.toml` settle
what the contract cannot: `formats`, how a text field reads, and `item_label`, the noun naming each item of a list output.

The page's sentences, headings and links live in `templates/method_page.md.j2`; what is computed here is the method-specific Markdown.
"""

import json
import re
from datetime import date
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from scripts.contract import Contract
from scripts.cookbook import INPUTS_FILE, Cookbook, MethodPackage, OutputHints, SampleRecord, TextFormat, file_urls, input_content
from scripts.exceptions import CookbookLayoutError
from scripts.snapshot import OUTPUT_DIR, OutputSnapshot, SnapshotRoute, preview_path

# The page's own sections are `##`, so a heading the output holds starts at `###`, and at `####` inside an item of a list output.
SECTION_LEVEL = 2
MAX_HEADING_LEVEL = 6
# A Markdown or plain text longer than this many lines shows its first part and folds the rest.
FOLD_LINES = 60
FOLD_SUMMARY = "Read the rest"
# A text longer than this, or holding a line break, is shown as a paragraph under its field's name rather than in the field and value table.
TABLE_TEXT_LIMIT = 120
# How wide the page shows a document's preview and an image in a table cell, in pixels.
PREVIEW_WIDTH = 480
CELL_IMAGE_WIDTH = 160
DEFAULT_ITEM_LABEL = "Item"
# A sample that is a list of structures is shown as JSON up to this many characters, and linked in `inputs.json` beyond, as the snippets do.
SAMPLE_INLINE_LIMIT = 4096
# The concept of a text-only output: a native `Text` or a concept refining it carries this one field.
_TEXT_ONLY_FIELDS = {"text"}
_HTML_FIELD = "inner_html"
_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"})
_LIST_MULTIPLICITIES = frozenset({"variable", "fixed"})
_IMAGE_KIND = "image"
_DOCUMENT_KIND = "document"
_TEXT_KINDS = frozenset({"prose", "text"})
_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
_ATX_HEADING = re.compile(r"^(#{1,6})(\s)")
_FENCE = re.compile(r"^\s*(```|~~~)")
_HTML_DROPPED = [
    re.compile(r"<!DOCTYPE[^>]*>", re.IGNORECASE),
    re.compile(r"<head\b.*?</head\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<style\b.*?</style\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<script\b.*?</script\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"</?(?:html|body)\b[^>]*>", re.IGNORECASE),
]
_HTML_HEADING = re.compile(r"<(/?)h([1-6])\b", re.IGNORECASE)


class SampleView(BaseModel):
    """One input of the sample, as the page shows it."""

    model_config = ConfigDict(frozen=True)

    name: str
    label: str
    body: str = Field(description="The input itself, as Markdown")
    record: SampleRecord | None = Field(description="Its source and licence, or None while its record is missing")


class OutputView(BaseModel):
    """The snapshot's run and its output, as the page shows them."""

    model_config = ConfigDict(frozen=True)

    date: str = Field(description="The day the run finished, such as `28 September 2026`")
    duration: str = Field(description="How long the run took, such as `37 seconds`")
    from_files: bool = Field(description="Whether the run was from the package's files rather than by its address")
    method_ref: str | None
    body: str = Field(description="The output, as Markdown")


def sample_label(*, package: MethodPackage, input_name: str) -> str:
    """The link text of an input's sample: its record's label, or `sample` and the input's name while it has no record."""
    record = package.editorial.samples.get(input_name)
    return record.label if record is not None else f"sample {input_name.replace('_', ' ')}"


def sample_views(*, cookbook: Cookbook, package: MethodPackage, contract: Contract) -> list[SampleView]:
    """Each input of the sample, in the order of `inputs.json`, shown by the kind the contract gives it."""
    kinds = {contract_input.name: contract_input.kind for contract_input in contract.inputs}
    views: list[SampleView] = []
    for input_name, value in package.inputs.items():
        label = sample_label(package=package, input_name=input_name)
        content = input_content(value)
        urls = file_urls(content)
        kind = kinds.get(input_name)
        if urls:
            body = "\n\n".join(
                _file_sample(cookbook=cookbook, package=package, url=url, label=label if len(urls) == 1 else f"{label} {index}", kind=kind)
                for index, url in enumerate(urls, start=1)
            )
        elif kind in _TEXT_KINDS and (text := _text_of(content)) is not None:
            body = _quotation(_demote_markdown(text.strip(), level=SECTION_LEVEL + 1))
        elif isinstance(content, dict):
            body = _field_table(content)
        elif isinstance(content, list):
            written = json.dumps(content, indent=2, ensure_ascii=False)
            if len(written) > SAMPLE_INLINE_LIMIT:
                body = f"[The {label}, in {INPUTS_FILE}]({INPUTS_FILE})"
            else:
                body = f"<details>\n<summary>The {label}, as JSON</summary>\n\n```json\n{written}\n```\n\n</details>"
        else:
            body = _quotation(str(content))
        views.append(SampleView(name=input_name, label=label, body=body, record=package.editorial.samples.get(input_name)))
    return views


def output_view(*, contract: Contract, hints: OutputHints, snapshot: OutputSnapshot) -> OutputView:
    """The snapshot's output, rendered from the contract's multiplicity and the method's hints, with the run's date and duration."""
    finished = snapshot.run.finished_at
    return OutputView(
        date=day_phrase(finished.date()),
        duration=duration_phrase(snapshot.run.duration_seconds),
        from_files=snapshot.run.route == SnapshotRoute.FILES,
        method_ref=snapshot.run.method_ref,
        body=output_markdown(contract=contract, hints=hints, output=snapshot.output),
    )


def output_markdown(*, contract: Contract, hints: OutputHints, output: JsonValue) -> str:
    """An output as a reader would use it: each item of a list output under its own heading, a single output as it is."""
    level = SECTION_LEVEL + 1
    if contract.output.multiplicity not in _LIST_MULTIPLICITIES:
        return _value(output, hints=hints, level=level)
    items: list[JsonValue]
    if isinstance(output, dict) and isinstance(envelope := output.get("items"), list):
        items = envelope
    elif isinstance(output, list):
        items = output
    else:
        items = [output]
    label = hints.item_label or DEFAULT_ITEM_LABEL
    return "\n\n".join(f"{'#' * level} {label} {index}\n\n{_value(item, hints=hints, level=level + 1)}" for index, item in enumerate(items, start=1))


def day_phrase(day: date) -> str:
    return f"{day.day} {_MONTHS[day.month - 1]} {day.year}"


def duration_phrase(seconds: float) -> str:
    """A run's duration as a reader says it: `37 seconds`, `1 minute 5 seconds`, `4 minutes`."""
    total = max(1, round(seconds))
    minutes, rest = divmod(total, 60)
    parts: list[str] = []
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if rest or not minutes:
        parts.append(f"{rest} second{'s' if rest != 1 else ''}")
    return " ".join(parts)


# ── The sample ───────────────────────────────────────────────────────


def _file_sample(*, cookbook: Cookbook, package: MethodPackage, url: str, label: str, kind: str | None) -> str:
    """One file of the sample: an image embedded, a document as its preview linking to it, anything else as a link.

    A file kept in this repository is linked by its path from the page, which reads the same on every branch and at every tag. A URL into this
    repository naming no file of this checkout keeps its URL, which the link check reports.
    """
    try:
        local_file = cookbook.local_file_of(url)
    except CookbookLayoutError:
        local_file = None
    target = url
    preview: str | None = None
    if local_file is not None:
        page_dir = package.directory.relative_to(cookbook.root)
        local_path = local_file.path.relative_to(cookbook.root.resolve())
        target = _relative_link(from_dir=page_dir, to_path=PurePosixPath(local_path.as_posix()))
        preview_file = preview_path(cookbook.root / local_path)
        if preview_file.is_file():
            preview = _relative_link(from_dir=page_dir, to_path=PurePosixPath(preview_file.relative_to(cookbook.root).as_posix()))
    if kind == _IMAGE_KIND:
        return f"![{label}]({target})"
    if kind == _DOCUMENT_KIND and preview is not None:
        return f'<a href="{target}"><img src="{preview}" alt="{_attribute(label)}" width="{PREVIEW_WIDTH}"></a>'
    return f"[{label}]({target})"


def _relative_link(*, from_dir: Path, to_path: PurePosixPath) -> str:
    """The link from a page's directory to a file, both given from the repository root."""
    depth = len(from_dir.parts)
    return "/".join([".."] * depth + list(to_path.parts))


def _text_of(content: JsonValue) -> str | None:
    if isinstance(content, str):
        return content
    if isinstance(content, dict) and set(content) == _TEXT_ONLY_FIELDS and isinstance(text := content.get("text"), str):
        return text
    return None


def _quotation(text: str) -> str:
    return "\n".join(f"> {line}".rstrip() for line in text.strip().split("\n"))


# ── The output ───────────────────────────────────────────────────────


def _value(value: JsonValue, *, hints: OutputHints, level: int) -> str:
    """A single output, or one item of a list output."""
    if isinstance(value, dict):
        if set(value) == _TEXT_ONLY_FIELDS and isinstance(text := value.get("text"), str):
            return _text(text, text_format=hints.formats.get("text", "markdown"), level=level)
        if _is_file(value):
            return _file(value, label="output", width=None)
        if _is_html(value):
            return _html(str(value[_HTML_FIELD]), level=level)
        return _structure(value, hints=hints, level=level)
    if isinstance(value, str):
        return _text(value, text_format="markdown", level=level)
    return _code_json(value)


def _structure(value: dict[str, JsonValue], *, hints: OutputHints, level: int) -> str:
    """A structure: its short values in a field and value table, then each longer one under its field's name."""
    rows: list[tuple[str, str]] = []
    blocks: list[str] = []
    for key, item in value.items():
        text_format = hints.formats.get(key)
        if _is_short(item) and text_format in {None, "text"}:
            rows.append((key, _cell(item)))
        elif isinstance(item, str):
            blocks.append(f"**`{key}`**\n\n{_text(item, text_format=text_format or 'text', level=level)}")
        elif isinstance(item, list):
            blocks.append(f"**`{key}`**\n\n{_list(item, hints=hints, level=level)}")
        elif isinstance(item, dict):
            if _is_file(item):
                blocks.append(f"**`{key}`**\n\n{_file(item, label=key, width=None)}")
            elif _is_html(item):
                blocks.append(f"**`{key}`**\n\n{_html(str(item[_HTML_FIELD]), level=level)}")
            else:
                blocks.append(f"**`{key}`**\n\n{_structure(item, hints=hints, level=level)}")
    parts = ([_table(["Field", "Value"], [[f"`{key}`", cell] for key, cell in rows])] if rows else []) + blocks
    return "\n\n".join(parts)


def _list(items: list[JsonValue], *, hints: OutputHints, level: int) -> str:
    """A list: none, bullets for texts and numbers, a table for structures, and each item in turn otherwise."""
    if not items:
        return "None."
    if all(not isinstance(item, dict | list) for item in items):
        return "\n".join(f"- {_inline(item)}" for item in items)
    if all(isinstance(item, dict) and not _is_file(item) and not _is_html(item) for item in items):
        structures = [item for item in items if isinstance(item, dict)]
        columns: list[str] = []
        for structure in structures:
            columns.extend(key for key in structure if key not in columns)
        return _table([f"`{column}`" for column in columns], [[_cell(structure.get(column)) for column in columns] for structure in structures])
    return "\n\n".join(_value(item, hints=hints, level=level) for item in items)


def _text(text: str, *, text_format: TextFormat, level: int) -> str:
    match text_format:
        case "markdown":
            return _fold(_demote_markdown(text.strip(), level=level))
        case "html":
            return _html(text, level=level)
        case "text":
            return _fold(text.strip())


def _demote_markdown(text: str, *, level: int) -> str:
    """Move every heading down so that the text's highest one sits at `level`, and none goes below `######`; code blocks are left alone."""
    lines = text.split("\n")
    in_fence = False
    heading_levels: list[int] = []
    for line in lines:
        if _FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and (match := _ATX_HEADING.match(line)):
            heading_levels.append(len(match.group(1)))
    if not heading_levels:
        return text
    shift = max(0, level - min(heading_levels))
    demoted: list[str] = []
    in_fence = False
    for line in lines:
        if _FENCE.match(line):
            in_fence = not in_fence
            demoted.append(line)
        elif not in_fence and (match := _ATX_HEADING.match(line)):
            new_level = min(MAX_HEADING_LEVEL, len(match.group(1)) + shift)
            demoted.append("#" * new_level + line[len(match.group(1)) :])
        else:
            demoted.append(line)
    return "\n".join(demoted)


def _fold(text: str) -> str:
    """Show a long text's first part and fold the rest, cutting at the first blank line past `FOLD_LINES` outside a code block."""
    lines = text.split("\n")
    if len(lines) <= FOLD_LINES:
        return text
    in_fence = False
    for index, line in enumerate(lines):
        if _FENCE.match(line):
            in_fence = not in_fence
        elif index >= FOLD_LINES and not in_fence and not line.strip():
            head = "\n".join(lines[:index]).rstrip()
            rest = "\n".join(lines[index:]).strip()
            if not rest:
                return text
            return f"{head}\n\n<details>\n<summary>{FOLD_SUMMARY}</summary>\n\n{rest}\n\n</details>"
    return text


def _html(text: str, *, level: int) -> str:
    """Embed HTML without its head, styles and scripts, its headings moved down as Markdown's are, as one block the page renders whole.

    Every line is left-trimmed and blank lines are dropped, since a blank line would close the HTML block and an indented line after it would
    read as code.
    """
    body = text
    for pattern in _HTML_DROPPED:
        body = pattern.sub("", body)
    heading_levels = [int(match.group(2)) for match in _HTML_HEADING.finditer(body) if not match.group(1)]
    if heading_levels:
        shift = max(0, level - min(heading_levels))
        body = _HTML_HEADING.sub(lambda match: f"<{match.group(1)}h{min(MAX_HEADING_LEVEL, int(match.group(2)) + shift)}", body)
    lines = [line.strip() for line in body.split("\n") if line.strip()]
    return "<div>\n" + "\n".join(lines) + "\n</div>"


def _is_file(value: dict[str, JsonValue]) -> bool:
    """Whether a structure is a file the snapshot copied: its `url` is a path under `output/`."""
    url = value.get("url")
    return isinstance(url, str) and url.startswith(f"{OUTPUT_DIR}/")


def _is_image(value: dict[str, JsonValue]) -> bool:
    mime_type = value.get("mime_type")
    if isinstance(mime_type, str) and mime_type.lower().startswith("image/"):
        return True
    return PurePosixPath(str(value.get("url"))).suffix.lower() in _IMAGE_EXTENSIONS


def _is_html(value: dict[str, JsonValue]) -> bool:
    return isinstance(value.get(_HTML_FIELD), str)


def _file(value: dict[str, JsonValue], *, label: str, width: int | None) -> str:
    """A copied file: an image embedded, anything else linked, named by its caption or filename when it has one."""
    url = str(value.get("url"))
    caption = value.get("caption") or value.get("filename") or label
    name = str(caption)
    if not _is_image(value):
        return f"[{name}]({url})"
    if width is None:
        return f"![{name}]({url})"
    return f'<a href="{url}"><img src="{url}" alt="{_attribute(name)}" width="{width}"></a>'


def _is_short(value: JsonValue) -> bool:
    if value is None or isinstance(value, bool | int | float):
        return True
    return isinstance(value, str) and len(value) <= TABLE_TEXT_LIMIT and "\n" not in value


def _cell(value: JsonValue) -> str:
    """A value in a table cell: a file as its image or link, a structure as its fields on lines of their own, a list joined."""
    if value is None:
        return ""
    if isinstance(value, dict):
        if _is_file(value):
            return _file(value, label="file", width=CELL_IMAGE_WIDTH)
        if _is_html(value):
            return "HTML"
        return "<br>".join(_escape_cell(f"{key}: {_inline(item)}") for key, item in value.items() if item is not None)
    if isinstance(value, list):
        return _escape_cell(", ".join(_inline(item) for item in value))
    return _escape_cell(_inline(value))


def _inline(value: JsonValue) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, int | float):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\r\n", "\n").replace("\n", "<br>")


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [f"| {' | '.join(headers)} |", f"|{'|'.join('---' for _ in headers)}|"]
    lines.extend(f"| {' | '.join(cell or ' ' for cell in row)} |" for row in rows)
    return "\n".join(lines)


def _field_table(content: dict[str, JsonValue]) -> str:
    return _table(["Field", "Value"], [[f"`{key}`", _cell(item)] for key, item in content.items()])


def _code_json(value: JsonValue) -> str:
    return f"```json\n{json.dumps(value, indent=2, ensure_ascii=False)}\n```"


def _attribute(text: str) -> str:
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
