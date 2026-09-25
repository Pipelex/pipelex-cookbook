"""Render every method's page, `methods/<name>/README.md`, from its package, its editorial fields and the templates, and the front page's methods.

Everything a page says about its method is derived here, from committed files only: the address from the manifest and the version file, the
samples and the code snippets' inputs from `inputs.json`, and the "Takes" and "Returns" lines from the contract snapshot; the answer key is
not shown on the page. The templates under `templates/` hold the wording and the links, one block per door, so a change to a door is made
once and every page inherits it at the next render.

The page's TypeScript and Python snippets are also written as files, `tests/snippets/<name>/typescript/snippet.ts` and
`tests/snippets/<name>/python/snippet.py`, from the same templates under `templates/snippets/`, so that what the page shows is what the type
checkers read. Each file ends with a typed read of the output the page does not show, through the types generated beside it, and each
language's generated tree gets its `sources.json` here too, naming the package's `.mthds` files that `make refresh` generates the types from.

The front page, `README.md`, is written by hand except for two regions, each between its two markers: one lists every method with its page and
its pitch, and the other the method library's methods, from the snapshot `library.json` taken at the library tag `cookbook.toml` pins.
"""

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pydantic import BaseModel, ConfigDict, Field, JsonValue

from scripts.contract import Contract, ContractField, ContractInput, short_concept
from scripts.cookbook import INPUTS_FILE, METHODS_DIR, SNIPPETS_DIR, Cookbook, MethodPackage
from scripts.exceptions import CookbookLayoutError
from scripts.library import LIBRARY_METHODS_DIR
from scripts.recipes import GENERATED_DIR, PYTHON_TARGET, SIDECAR_FILE, TYPESCRIPT_TARGET

PAGE_TEMPLATE = "method_page.md.j2"
# Each file `make render` writes in a method's `tests/snippets/<name>/`, mapped to the template writing it around the page's snippet.
SNIPPET_TEMPLATES = {"typescript/snippet.ts": "snippets/file.ts.j2", "python/snippet.py": "snippets/file.py.j2"}
# The sidecar of each language's generated tree, `tests/snippets/<name>/<language>/generated/<name>/sources.json`, with the codegen target
# `make refresh` generates the tree for. It names the package's `.mthds` files rather than the page's address, since the page names the last
# release's tag, which does not hold a method added since.
SIDECAR_TEMPLATE = "snippets/sources.json.j2"
SIDECAR_TARGETS = {"typescript": TYPESCRIPT_TARGET, "python": PYTHON_TARGET}
# The most characters of sample inputs, serialised as JSON, that the code snippets write out. Above it, every snippet fetches the inputs from
# the method's `inputs.json` at the page's tag instead, since a sample written out in three languages would bury the page's doors.
INLINE_INPUTS_LIMIT = 4096
FRONT_PAGE_FILE = "README.md"
FRONT_REGION_TEMPLATE = "front_region.md.j2"
FRONT_REGION_BEGIN = "<!-- BEGIN methods, written by `make render` from methods/ and cookbook.toml: never edit this region by hand -->"
FRONT_REGION_END = "<!-- END methods -->"
LIBRARY_REGION_TEMPLATE = "library_region.md.j2"
LIBRARY_REGION_BEGIN = "<!-- BEGIN library, written by `make render` from library.json: never edit this region by hand -->"
LIBRARY_REGION_END = "<!-- END library -->"
RAW_BASE_URL = "https://raw.githubusercontent.com"
GITHUB_BASE_URL = "https://github.com"
DEFAULT_CHATBOT_WITH_SAMPLES = "Run {address} on {samples}"
DEFAULT_CHATBOT_WITHOUT_SAMPLES = "Run {address} with the sample inputs in {inputs_url}"
DEFAULT_YOURS_CHANGE = "adapt what it does to my case"

_TYPESCRIPT_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")

# The input form's kind for each input, as a reader says it. The kind `list` only restates the multiplicity, so a list is phrased from its
# concept instead.
_KIND_NOUNS = {"prose": "text", "list": None}
# A concept refining the native `Text` carries a single `text` field, which says nothing the concept's own description does not.
_TEXT_ONLY_FIELDS = ["text"]
_NATIVE_PREFIX = "native."
# The output multiplicities that make the main pipe return a list.
_LIST_MULTIPLICITIES = frozenset({"variable", "fixed"})

_SCALAR_PHRASES = {
    "text": ("text", "texts"),
    "date": ("a date", "dates"),
    "datetime": ("a date and time", "dates and times"),
    "integer": ("an integer", "integers"),
    "number": ("a number", "numbers"),
    "boolean": ("true or false", "true-or-false values"),
    "object": ("an object", "objects"),
    "any": ("any value", "values"),
}


class Sample(BaseModel):
    """A sample input the page links to."""

    model_config = ConfigDict(frozen=True)

    label: str
    url: str


class FrontRegion(BaseModel):
    """A region of the front page that `make render` writes between its two markers, from its template."""

    model_config = ConfigDict(frozen=True)

    what: str = Field(description="What the region lists, as a refusal names it")
    begin: str
    end: str
    template: str


METHODS_REGION = FrontRegion(what="the list of methods", begin=FRONT_REGION_BEGIN, end=FRONT_REGION_END, template=FRONT_REGION_TEMPLATE)
LIBRARY_REGION = FrontRegion(
    what="the list of the library's methods", begin=LIBRARY_REGION_BEGIN, end=LIBRARY_REGION_END, template=LIBRARY_REGION_TEMPLATE
)


class LibraryLine(BaseModel):
    """One line of the front page's list of the library's methods."""

    model_config = ConfigDict(frozen=True)

    display_name: str
    url: str = Field(description="The method's directory in the library's repository, at the pinned tag")
    address: str
    description: str


class LibraryContext(BaseModel):
    """Everything the library region's template needs, derived from the snapshot and `cookbook.toml`."""

    model_config = ConfigDict(frozen=True)

    url: str = Field(description="The library's repository at the pinned tag")
    tag: str
    methods: list[LibraryLine]


class PageContext(BaseModel):
    """Everything the page template needs, derived from one package."""

    model_config = ConfigDict(frozen=True)

    title: str
    pitch: str
    name: str
    address: str
    tag: str
    header_links: str
    samples: list[Sample]
    has_file_inputs: bool
    takes: list[str]
    returns: str
    returns_fields: list[str]
    output_concept: str = Field(description="The output concept's name without its domain, which the generated types name it by")
    output_is_list: bool
    bundle_sources: list[str] = Field(description="The package's `.mthds` files, by their paths from the repository root")
    chatbot: str
    fetches_inputs: bool
    python_inputs_typed: bool
    inputs_typescript: str
    inputs_python: str
    start_body_json: str
    inputs_url: str
    app_dir: str
    yours_dir: str
    yours_change: str
    source_dir: str


def make_environment(templates_dir: Path) -> Environment:
    """The Jinja2 environment for Markdown pages: no escaping, strict about undefined names, and trailing newlines kept."""
    return Environment(
        loader=FileSystemLoader(templates_dir),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_pages(*, cookbook: Cookbook, templates_dir: Path) -> dict[Path, str]:
    """Render every package's page.

    Returns:
        Each page's path, mapped to its rendered contents.

    Raises:
        CookbookLayoutError: A package has no contract snapshot yet.
    """
    environment = make_environment(templates_dir)
    template = environment.get_template(PAGE_TEMPLATE)
    pages: dict[Path, str] = {}
    for package in cookbook.packages:
        context = build_page_context(cookbook=cookbook, package=package)
        pages[package.page_path] = template.render(page=context)
    return pages


def render_front_page(*, cookbook: Cookbook, templates_dir: Path) -> dict[Path, str]:
    """Render the front page's two regions, the list of methods and the list of the library's methods, leaving every line outside them as it is.

    Returns:
        The front page's path, mapped to its contents with both regions re-rendered.

    Raises:
        CookbookLayoutError: The front page is missing, does not hold each region exactly once between its two markers, or holds two regions
            that overlap; or the library's snapshot was not loaded.
    """
    front_page_path = cookbook.root / FRONT_PAGE_FILE
    if not front_page_path.is_file():
        msg = f"{front_page_path} does not exist, and it holds the lists `make render` writes"
        raise CookbookLayoutError(msg)
    current = front_page_path.read_text(encoding="utf-8")
    environment = make_environment(templates_dir)
    bodies = [
        (
            METHODS_REGION,
            environment.get_template(METHODS_REGION.template).render(
                methods=[build_page_context(cookbook=cookbook, package=package) for package in cookbook.packages]
            ),
        ),
        (LIBRARY_REGION, environment.get_template(LIBRARY_REGION.template).render(library=build_library_context(cookbook))),
    ]
    spans: list[tuple[int, int, FrontRegion, str]] = []
    for region, body in bodies:
        begin = current.find(region.begin)
        end = current.find(region.end)
        if current.count(region.begin) != 1 or current.count(region.end) != 1 or end < begin:
            msg = f"{FRONT_PAGE_FILE} must hold one region for {region.what}, opened by `{region.begin}` and closed by `{region.end}`"
            raise CookbookLayoutError(msg)
        spans.append((begin, end, region, body))
    spans.sort(key=lambda span: span[0])
    for (_, earlier_end, earlier, _), (later_begin, _, later, _) in zip(spans, spans[1:], strict=False):
        if later_begin < earlier_end + len(earlier.end):
            msg = (
                f"{FRONT_PAGE_FILE} opens the region for {later.what} inside the region for {earlier.what}: each region closes before the next opens"
            )
            raise CookbookLayoutError(msg)
    # Each region is replaced from the last to the first, so the offsets found above still hold for the regions not yet replaced.
    rendered = current
    for begin, end, region, body in reversed(spans):
        rendered = rendered[: begin + len(region.begin)] + "\n" + body + rendered[end:]
    return {front_page_path: rendered}


def build_library_context(cookbook: Cookbook) -> LibraryContext:
    """Derive the library region's lines from the snapshot, linking each method's directory at the pinned tag.

    Raises:
        CookbookLayoutError: The cookbook was loaded without its library snapshot.
    """
    snapshot = cookbook.library
    if snapshot is None:
        msg = "the cookbook was loaded without library.json, which the front page's list of the library's methods is written from"
        raise CookbookLayoutError(msg)
    repository_url = f"{GITHUB_BASE_URL}/{cookbook.settings.library.repository}/tree/{snapshot.tag}"
    return LibraryContext(
        url=repository_url,
        tag=snapshot.tag,
        methods=[
            LibraryLine(
                display_name=method.display_name,
                url=f"{repository_url}/{LIBRARY_METHODS_DIR}/{method.name}",
                address=f"{snapshot.address}/{method.name}@{snapshot.tag}",
                description=_sentence(method.description),
            )
            for method in snapshot.methods
        ],
    )


def render_snippets(*, cookbook: Cookbook, templates_dir: Path) -> dict[Path, str]:
    """Render every package's TypeScript and Python snippets as files, and the sidecar of each one's generated tree.

    Each snippet file is the page's own snippet under a header saying where it comes from, followed by a typed read of the output that the
    page does not show. Each sidecar names the package's `.mthds` files and the codegen target its tree is generated for.

    Returns:
        Each file's path, under `tests/snippets/<name>/`, mapped to its rendered contents.

    Raises:
        CookbookLayoutError: A package has no contract snapshot yet.
    """
    environment = make_environment(templates_dir)
    sidecar_template = environment.get_template(SIDECAR_TEMPLATE)
    snippets: dict[Path, str] = {}
    for package in cookbook.packages:
        context = build_page_context(cookbook=cookbook, package=package)
        snippets_dir = cookbook.root / SNIPPETS_DIR / package.name
        for relative_path, template_name in SNIPPET_TEMPLATES.items():
            snippets[snippets_dir / relative_path] = environment.get_template(template_name).render(page=context)
        for language, target in SIDECAR_TARGETS.items():
            snippets[snippets_dir / language / GENERATED_DIR / package.name / SIDECAR_FILE] = sidecar_template.render(page=context, target=target)
    return snippets


def render_all(*, cookbook: Cookbook, templates_dir: Path) -> dict[Path, str]:
    """Every file `make render` writes: each method's page and its snippet files, and the front page with its two lists."""
    return (
        render_pages(cookbook=cookbook, templates_dir=templates_dir)
        | render_snippets(cookbook=cookbook, templates_dir=templates_dir)
        | render_front_page(cookbook=cookbook, templates_dir=templates_dir)
    )


def build_page_context(*, cookbook: Cookbook, package: MethodPackage) -> PageContext:
    """Derive what the page of `package` says, from committed files only.

    Raises:
        CookbookLayoutError: The package has no contract snapshot yet.
    """
    contract = package.contract
    if contract is None:
        msg = f"{package.directory} has no contract snapshot yet: run `make refresh` (it needs PIPELEX_API_KEY), then `make render`"
        raise CookbookLayoutError(msg)
    editorial = package.editorial
    address = cookbook.address_of(package)
    snippet_inputs = _snippet_inputs(package.inputs)
    samples = _samples(package=package)
    inputs_url = f"{RAW_BASE_URL}/{cookbook.settings.repository}/{cookbook.tag}/{METHODS_DIR}/{package.name}/{INPUTS_FILE}"
    fetches_inputs = len(json.dumps(snippet_inputs, ensure_ascii=False)) > INLINE_INPUTS_LIMIT

    chatbot_template = editorial.chatbot or (DEFAULT_CHATBOT_WITH_SAMPLES if samples else DEFAULT_CHATBOT_WITHOUT_SAMPLES)
    try:
        chatbot = chatbot_template.format(address=address, samples=" and ".join(sample.url for sample in samples), inputs_url=inputs_url)
    except (KeyError, IndexError, AttributeError, ValueError) as exc:
        # `str.format` raises KeyError or IndexError for an unknown placeholder, AttributeError for `{address.x}` and ValueError for a stray brace.
        msg = (
            f"the chatbot sentence of `{package.name}` in cookbook.toml does not format; "
            f"its placeholders are {{address}}, {{samples}} and {{inputs_url}}, and a literal brace is written doubled: {exc}"
        )
        raise CookbookLayoutError(msg) from exc

    return PageContext(
        title=editorial.title or package.manifest.display_name or package.name,
        pitch=_sentence(editorial.pitch or package.manifest.description),
        name=package.name,
        address=address,
        tag=cookbook.tag,
        header_links=" · ".join(
            [f"[{bundle_file}]({bundle_file})" for bundle_file in package.bundle_files] + [f"[{sample.label}]({sample.url})" for sample in samples]
        ),
        samples=samples,
        has_file_inputs=bool(samples),
        takes=[_input_line(contract_input) for contract_input in contract.inputs],
        returns=_described(
            _output_phrase(contract), description=None if contract.output.concept.startswith(_NATIVE_PREFIX) else contract.output.description
        ),
        returns_fields=[]
        if [contract_field.name for contract_field in contract.output.fields] == _TEXT_ONLY_FIELDS
        else [_field_line(contract_field) for contract_field in contract.output.fields],
        output_concept=short_concept(contract.output.concept),
        output_is_list=contract.output.multiplicity in _LIST_MULTIPLICITIES,
        bundle_sources=[f"{METHODS_DIR}/{package.name}/{bundle_file}" for bundle_file in package.bundle_files],
        chatbot=chatbot,
        fetches_inputs=fetches_inputs,
        python_inputs_typed=fetches_inputs or all(_python_sdk_admits(value) for value in snippet_inputs.values()),
        inputs_typescript=_indent_continuation(typescript_literal(snippet_inputs), prefix="  "),
        inputs_python=_indent_continuation(python_literal(snippet_inputs), prefix="            "),
        start_body_json=_shell_single_quote(json.dumps({"method_ref": address, "inputs": snippet_inputs}, ensure_ascii=False)),
        inputs_url=inputs_url,
        app_dir=editorial.app_dir or f"{package.name.replace('_', '-')}-app",
        yours_dir=editorial.yours_dir or package.name,
        yours_change=editorial.yours_change or DEFAULT_YOURS_CHANGE,
        source_dir=f"{METHODS_DIR}/{package.name}",
    )


def typescript_literal(value: JsonValue, *, indent: int = 0) -> str:
    """Write a JSON value as a TypeScript literal, formatted the way Prettier formats one: bare keys where they are identifiers, trailing commas."""
    padding = "  " * indent
    inner = "  " * (indent + 1)
    match value:
        case None:
            return "null"
        case bool():
            return "true" if value else "false"
        case int() | float():
            return json.dumps(value)
        case str():
            return json.dumps(value, ensure_ascii=False)
        case list():
            if not value:
                return "[]"
            items = [f"{inner}{typescript_literal(item, indent=indent + 1)}," for item in value]
            return "[\n" + "\n".join(items) + f"\n{padding}]"
        case dict():
            if not value:
                return "{}"
            entries: list[str] = []
            for key, item in value.items():
                key_text = key if _TYPESCRIPT_IDENTIFIER_PATTERN.match(key) else json.dumps(key, ensure_ascii=False)
                entries.append(f"{inner}{key_text}: {typescript_literal(item, indent=indent + 1)},")
            return "{\n" + "\n".join(entries) + f"\n{padding}}}"


def python_literal(value: JsonValue, *, indent: int = 0) -> str:
    """Write a JSON value as a Python literal, formatted the way ruff formats one: double quotes, one item per line, trailing commas."""
    padding = "    " * indent
    inner = "    " * (indent + 1)
    match value:
        case None:
            return "None"
        case bool():
            return "True" if value else "False"
        case int() | float():
            return repr(value)
        case str():
            return _python_string(value)
        case list():
            if not value:
                return "[]"
            items = [f"{inner}{python_literal(item, indent=indent + 1)}," for item in value]
            return "[\n" + "\n".join(items) + f"\n{padding}]"
        case dict():
            if not value:
                return "{}"
            entries = [f"{inner}{_python_string(key)}: {python_literal(item, indent=indent + 1)}," for key, item in value.items()]
            return "{\n" + "\n".join(entries) + f"\n{padding}}}"


def _python_string(text: str) -> str:
    """Quote a string as ruff does: in double quotes, unless it holds more double quotes than single ones, where single quotes escape less."""
    double_quoted = json.dumps(text, ensure_ascii=False)
    if text.count('"') <= text.count("'"):
        return double_quoted
    return "'" + double_quoted[1:-1].replace('\\"', '"').replace("'", "\\'") + "'"


def _snippet_inputs(inputs: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """The inputs as code passes them: `inputs.json` may wrap a value as `{"concept": …, "content": …}`, and the code passes the content.

    Only a dict whose keys are exactly `concept` and `content` is that wrapper, as the runtime reads it: a structured input whose concept has a
    field named `content` is passed whole.
    """
    snippet_inputs: dict[str, JsonValue] = {}
    for input_name, input_value in inputs.items():
        if isinstance(input_value, dict) and set(input_value) == {"concept", "content"}:
            snippet_inputs[input_name] = input_value["content"]
        else:
            snippet_inputs[input_name] = input_value
    return snippet_inputs


def _python_sdk_admits(value: JsonValue) -> bool:
    """Whether the Python SDK's type for an input's value admits this value, written out in a snippet.

    `pipelex-sdk` types each input as `mthds.protocol.pipeline_inputs.StuffContentOrData`: a string, a list of strings, a content object or a
    list of them, or a dict. A list of plain objects, such as several documents each given by its URL, is none of them, although the hosted
    API reads it as the input's content, so pyright refuses a snippet writing one out.
    """
    return isinstance(value, str | dict) or (isinstance(value, list) and all(isinstance(item, str) for item in value))


def _samples(*, package: MethodPackage) -> list[Sample]:
    """The files the sample inputs name, one per URL: an input holding a list of files gives each its own numbered label."""
    samples: list[Sample] = []
    for input_name, content in _snippet_inputs(package.inputs).items():
        urls = _file_urls(content)
        label = package.editorial.sample_labels.get(input_name) or f"sample {input_name.replace('_', ' ')}"
        for index, url in enumerate(urls, start=1):
            samples.append(Sample(label=label if len(urls) == 1 else f"{label} {index}", url=url))
    return samples


def _file_urls(content: JsonValue) -> list[str]:
    """The URLs of a file input, given as one `{"url": …}` object or as a list of them."""
    if isinstance(content, dict):
        url = content.get("url")
        return [url] if isinstance(url, str) else []
    if isinstance(content, list):
        return [url for item in content if isinstance(item, dict) and isinstance(url := item.get("url"), str)]
    return []


def _input_line(contract_input: ContractInput) -> str:
    concept = f"`{short_concept(contract_input.concept)}`"
    kind = _KIND_NOUNS.get(contract_input.kind, contract_input.kind) if contract_input.kind else None
    what: str
    if kind:
        match contract_input.multiplicity:
            case "variable" | "fixed":
                what = f"a list of {kind}s ({concept})"
            case _:
                what = f"{_with_article(kind)} ({concept})"
    else:
        match contract_input.multiplicity:
            case "variable" | "fixed":
                what = f"a list of {concept}"
            case _:
                what = concept
    if not contract_input.required:
        what = f"{what}, optional"
    # A native concept's description only restates its type ("A text"), so only a method's own concept is described.
    description = None if contract_input.concept.startswith(_NATIVE_PREFIX) else contract_input.description
    return _described(f"`{contract_input.name}`, {what}", description=description)


def _output_phrase(contract: Contract) -> str:
    concept = f"`{short_concept(contract.output.concept)}`"
    match contract.output.multiplicity:
        case "variable":
            return f"a list of {concept}"
        case "fixed":
            count = contract.output.item_count
            return f"{count} {concept}" if count else f"a list of {concept}"
        case _:
            return _with_article(concept)


def _field_line(contract_field: ContractField) -> str:
    return _described(f"`{contract_field.name}`, {type_phrase(contract_field.type)}", description=contract_field.description)


def _described(subject: str, *, description: str | None) -> str:
    """A contract line: what a thing is, then what it is for when the method says so."""
    return f"{subject}: {_sentence(description)}" if description else f"{subject}."


def type_phrase(type_expression: str) -> str:
    """Phrase a contract type expression for a reader: `list[GanttTaskDetails]` becomes "a list of `GanttTaskDetails`"."""
    if type_expression.startswith("list[") and type_expression.endswith("]"):
        item_type = type_expression.removeprefix("list[").removesuffix("]")
        scalar = _SCALAR_PHRASES.get(item_type)
        return f"a list of {scalar[1]}" if scalar else f"a list of `{item_type}`"
    scalar = _SCALAR_PHRASES.get(type_expression)
    if scalar:
        return scalar[0]
    if " or " in type_expression:
        return " or ".join(type_phrase(branch) for branch in type_expression.split(" or "))
    return _with_article(f"`{type_expression}`")


def _with_article(noun: str) -> str:
    first_letter = noun.lstrip("`")[:1].lower()
    return f"an {noun}" if first_letter in "aeiou" and first_letter else f"a {noun}"


def _sentence(text: str | None) -> str:
    stripped = (text or "").strip()
    if stripped and stripped[-1].isalnum():
        return f"{stripped}."
    return stripped


def _indent_continuation(text: str, *, prefix: str) -> str:
    """Indent every line but the first, so a multi-line literal sits under the code that opens it."""
    first, *rest = text.split("\n")
    return "\n".join([first, *(f"{prefix}{line}" for line in rest)])


def _shell_single_quote(text: str) -> str:
    """Quote text for a POSIX shell's single quotes, closing and reopening them around each embedded quote."""
    return "'" + text.replace("'", "'\\''") + "'"
