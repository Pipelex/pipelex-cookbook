"""Constants for the cookbook tooling's tests: the fixture cookbook's editorial file, bundles, contract and output snapshots, and outputs."""

import io
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image
from pydantic import JsonValue

from scripts.contract import Contract, ContractField, ContractInput, ContractOutput
from scripts.cookbook import load_cookbook
from scripts.library import LibraryMethod, LibrarySnapshot
from scripts.snapshot import (
    PRODUCTION_URL,
    OutputSnapshot,
    SnapshotFile,
    SnapshotRoute,
    SnapshotRun,
    bundle_digest,
    inputs_digest,
    sha256_of,
    snapshot_path,
)

FIXTURE_ADDRESS = "github.com/Pipelex/pipelex-cookbook"
FIXTURE_VERSION = "0.9.0"
LIBRARY_ADDRESS = "github.com/Pipelex/methods"
LIBRARY_REPOSITORY = "Pipelex/methods"
LIBRARY_TAG = "v0.4.0"
WIDGETS_SAMPLE_URL = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/assets/extract_widgets/catalogue.png"
# Where the fixture's widget catalogue sample is written, from the cookbook's root, and where its record says it was copied from.
WIDGETS_SAMPLE_PATH = "assets/extract_widgets/catalogue.png"
# The same sample as a Word document, which no preview can be rendered from.
WIDGETS_WORD_SAMPLE_URL = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/assets/extract_widgets/catalogue.docx"
WIDGETS_WORD_SAMPLE_PATH = "assets/extract_widgets/catalogue.docx"
WIDGETS_SOURCE = "https://widgets.example.org/catalogue.png"

COOKBOOK_TOML = f"""address = "{FIXTURE_ADDRESS}"
repository = "Pipelex/pipelex-cookbook"

[library]
address = "{LIBRARY_ADDRESS}"
repository = "{LIBRARY_REPOSITORY}"
tag = "{LIBRARY_TAG}"

[methods.extract_widgets]
title = "Widget extraction"
pitch = "Read a catalogue page and list every widget on it"
app_dir = "widgets-app"
yours_dir = "widgets"
yours_change = "add each widget's price to what it extracts"

[methods.extract_widgets.samples.catalogue]
label = "sample catalogue"
synthetic = false
source = "{WIDGETS_SOURCE}"
retrieved = 2026-09-20
license = "CC-BY-4.0"
license_url = "https://creativecommons.org/licenses/by/4.0/"
attribution = "The Widget Society"
changes = "Cut to its first page"
"""

# The fixture packages' bundles, each declaring the main pipe and the output its contract snapshot records.
WIDGETS_BUNDLE = """domain = "widgets"
main_pipe = "extract_widgets"

[concept]
CataloguePage = "A page of a widget catalogue"
Widget = "A widget"
WidgetList = "Every widget on the page"

[pipe.extract_widgets]
type = "PipeLLM"
inputs = { catalogue = "CataloguePage" }
output = "WidgetList"
prompt = "List every widget on @catalogue."
"""

WORDS_BUNDLE = """domain = "words"
main_pipe = "count_words"

[pipe.count_words]
type = "PipeLLM"
inputs = { text = "Text" }
output = "Text"
prompt = "Count the words of @text."
"""

WIDGETS_CONTRACT = Contract(
    pipe="widgets.extract_widgets",
    inputs=[
        ContractInput(
            name="catalogue",
            concept="widgets.CataloguePage",
            kind="image",
            description="A page of a widget catalogue",
            multiplicity="single",
        )
    ],
    output=ContractOutput(
        concept="widgets.WidgetList",
        description="Every widget on the page",
        multiplicity="single",
        fields=[ContractField(name="widgets", type="list[Widget]", description="The widgets, in page order")],
    ),
)

WORDS_CONTRACT = Contract(
    pipe="words.count_words",
    inputs=[ContractInput(name="text", concept="native.Text", kind="text", description=None, multiplicity="single")],
    output=ContractOutput(concept="native.Text", description="A text", multiplicity="single"),
)

# The factory the `make_cookbook` fixture returns: keyword arguments `version` and `widgets_version`, and the cookbook root as its result.
FRONT_PAGE = """# Fixture cookbook

Written by hand.

<!-- BEGIN methods, written by `make render` from methods/ and cookbook.toml: never edit this region by hand -->
<!-- END methods -->

Between the lists, written by hand.

<!-- BEGIN library, written by `make render` from library.json: never edit this region by hand -->
<!-- END library -->

## Also written by hand
"""

# The fixture library's snapshot, as `make refresh-library` writes it: two methods, sorted by name.
LIBRARY_SNAPSHOT = LibrarySnapshot(
    address=LIBRARY_ADDRESS,
    repository=LIBRARY_REPOSITORY,
    tag=LIBRARY_TAG,
    methods=[
        LibraryMethod(
            name="invoice_extraction",
            display_name="Invoice Extraction",
            description="Extract structured invoice data from a document",
            main_pipe="extract_invoice",
        ),
        LibraryMethod(
            name="text_stats",
            display_name="Text Stats",
            description="Deterministic text statistics computed in pure Python.",
            main_pipe="analyze_text",
        ),
    ],
)

MakeCookbook = Callable[..., Path]

# An output of the right shape for each method under methods/, written by hand from its contract.json, for the shape check's tests. Each is
# made up and short: the shape check reads the shape, never the content.
RIGHT_OUTPUTS: dict[str, JsonValue] = {
    "discord_newsletter": {
        "text": (
            "<h2>☀️ Weekly Summary</h2>\n<p>Two new members joined, and the finishing thread settled on thinner coats in a cold workshop.</p>"
            "<h2>🙌 New members</h2>\n<ul><li>Ada Example is a cabinetmaker near Nantes who joined to talk about pricing.</li></ul>"
            "<h2>finishing</h2><p>Ben Example asked why his oil stayed tacky; the answer was one thin coat, wiped back hard.</p>"
            "<h2>🌎 Geographic hubs</h2><h3>🇫🇷-lyon</h3><p>The monthly meetup is on Saturday 10 October at 10am.</p>"
        ),
    },
    "extract_dpe": {
        "address": "7 rue des Illustrations, 69007 Lyon, 2nd floor, lot 12",
        "dpe_number": "2669E0000000Y",
        "date_of_issue": "2026-03-02",
        "date_of_expiration": "2036-03-01",
        "energy_efficiency_class": "E",
        "per_year_per_m2_consumption": 287,
        "co2_emission_class": "D",
        "per_year_per_m2_co2_emissions": 44,
        "yearly_energy_costs_min": 1120,
        "yearly_energy_costs_max": 1540,
        "energy_prices_as_of": "2025-01-01",
        "letting_status": "Can be let",
        "no_new_lease_from": "2034-01-01",
    },
    "gen_synthetic_data": {
        "items": [
            {
                "case": "A customer whose new kettle gave off a burning smell the first time it was used asks whether it is safe to keep using it.",
                "fields": [
                    {"name": "channel", "value": "contact form"},
                    {"name": "customer_name", "value": "Ada Example"},
                    {"name": "order_number", "value": "C40718263"},
                    {"name": "message", "value": "My new kettle smelled of burning the first time I used it. Is it safe?"},
                    {"name": "queue", "value": "Warranty and repairs"},
                    {"name": "priority", "value": "urgent"},
                ],
            },
            {
                "case": "A customer writing from a phone, annoyed, whose order is a week late and who gives no order number.",
                "fields": [
                    {"name": "channel", "value": "email"},
                    {"name": "customer_name", "value": "Ben Example"},
                    {"name": "order_number", "value": ""},
                    {"name": "message", "value": "ordered a toaster 8 days ago still nothing, where is it"},
                    {"name": "queue", "value": "Orders and delivery"},
                    {"name": "priority", "value": "high"},
                ],
            },
        ],
    },
    "review_nda": {
        "verdict": "Sign after negotiating",
        "note_for_counsel": "A mutual NDA on a published standard; the confidentiality period needs our fallback wording.",
        "positions": [
            {
                "position": "Purpose",
                "clause": "Cover Page, Purpose",
                "the_draft_says": "Use is limited to evaluating a business relationship.",
                "assessment": "acceptable",
                "fallback": None,
            },
            {
                "position": "Confidentiality period",
                "clause": "Cover Page, Term of Confidentiality",
                "the_draft_says": 'Confidentiality lasts "In perpetuity".',
                "assessment": "negotiate",
                "fallback": "Five years from the Effective Date.",
            },
        ],
    },
}

# Contracts written by hand, each with an output of the right shape, so that the shape check's tests over every method also cover the shapes no
# method under methods/ declares today: a list output, and a structure whose fields are all optional. Their names are no method's.
SHAPE_FIXTURES: dict[str, tuple[Contract, JsonValue]] = {
    "fixture_list_output": (
        Contract(
            pipe="pages.extract_pages",
            output=ContractOutput(
                concept="native.Text",
                description="A text",
                multiplicity="variable",
                fields=[ContractField(name="text", type="text", description="The text", required=True)],
            ),
        ),
        {"items": [{"text": "# Page 1\n\nThe first page."}, {"text": "# Page 2\n\nThe second page."}]},
    ),
    "fixture_optional_fields": (
        Contract(
            pipe="schedule.extract_schedule",
            output=ContractOutput(
                concept="schedule.Schedule",
                description="A project schedule",
                multiplicity="single",
                fields=[
                    ContractField(name="tasks", type="list[Task]", description="The tasks, in start order", required=False),
                    ContractField(name="milestones", type="list[Milestone]", description="The milestones, in date order", required=False),
                ],
            ),
        ),
        {
            "tasks": [{"name": "Foundations", "start_date": "2026-03-02", "end_date": "2026-03-13"}],
            "milestones": [{"name": "Roof on", "milestone_date": "2026-04-10"}],
        },
    ),
}


def make_widgets_sample_synthetic(root: Path) -> None:
    """Turn the fixture's widget sample record into one of a made-up sample, which may be linked where it is hosted."""
    cookbook_path = root / "cookbook.toml"
    real_lines = f'synthetic = false\nsource = "{WIDGETS_SOURCE}"\nretrieved = 2026-09-20\n'
    contents = cookbook_path.read_text(encoding="utf-8")
    assert real_lines in contents
    cookbook_path.write_text(contents.replace(real_lines, "synthetic = true\n").replace('changes = "Cut to its first page"\n', ""), encoding="utf-8")


def drop_widgets_record(root: Path) -> None:
    """Remove the fixture's widget sample record, as for a sample whose provenance is not settled."""
    cookbook_path = root / "cookbook.toml"
    contents = cookbook_path.read_text(encoding="utf-8")
    header = "[methods.extract_widgets.samples.catalogue]\n"
    assert header in contents
    cookbook_path.write_text(contents[: contents.index(header)], encoding="utf-8")


def make_widgets_sample_a_document(root: Path) -> None:
    """Make the fixture's widget sample a document input in its contract snapshot, which the page shows by its preview."""
    contract = WIDGETS_CONTRACT.model_copy(
        update={"inputs": [ContractInput(name="catalogue", concept="widgets.CataloguePage", kind="document", multiplicity="single")]}
    )
    (root / "methods" / "extract_widgets" / "contract.json").write_text(contract.to_json(), encoding="utf-8")


def make_word_document_sample(root: Path) -> None:
    """Make the fixture's widget sample a Word document kept under `assets/`, which its contract calls a document and its record describes."""
    sample_path = root / WIDGETS_WORD_SAMPLE_PATH
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    # A Word file is a zip archive: its header, and its name, are what tell it from a PDF.
    sample_path.write_bytes(b"PK\x03\x04 a Word document")
    inputs = {"catalogue": {"concept": "widgets.CataloguePage", "content": {"url": WIDGETS_WORD_SAMPLE_URL}}}
    (root / "methods" / "extract_widgets" / "inputs.json").write_text(json.dumps(inputs, indent=2), encoding="utf-8")
    make_widgets_sample_a_document(root)


def add_words_synthetic_record(root: Path) -> None:
    """Give the fixture's inline text sample the record of one written for the example."""
    with (root / "cookbook.toml").open("a", encoding="utf-8") as cookbook_file:
        cookbook_file.write(
            '\n[methods.count_words.samples.text]\nlabel = "sample text"\nsynthetic = true\nlicense = "MIT"\n'
            'license_url = "https://github.com/Pipelex/pipelex-cookbook/blob/main/LICENSE"\nattribution = "Evotis S.A.S"\n'
        )


# What the fixture's widget extraction returned on its sample, as its output snapshot holds it.
WIDGETS_OUTPUT: JsonValue = {"widgets": [{"name": "Sprocket", "colour": "red"}, {"name": "Flange", "colour": "blue"}]}
RUN_STARTED_AT = datetime(2026, 9, 28, 9, 14, 2, tzinfo=UTC)
RUN_FINISHED_AT = datetime(2026, 9, 28, 9, 14, 39, tzinfo=UTC)


def write_snapshot(root: Path, name: str, *, output: JsonValue, files: dict[str, tuple[bytes, str]] | None = None) -> OutputSnapshot:
    """Write a method's output snapshot as `make snapshot` would, from its package as it is now, with each file of `files` (its path relative
    to the package, mapped to its bytes and its content type) written under `output/`."""
    cookbook = load_cookbook(root)
    [package] = [package for package in cookbook.packages if package.name == name]
    contract = package.contract
    assert contract is not None
    entries: dict[str, SnapshotFile] = {}
    for relative, (data, content_type) in (files or {}).items():
        path = package.directory / relative
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        entries[relative] = SnapshotFile(sha256=sha256_of(data), content_type=content_type)
    snapshot = OutputSnapshot(
        pipe=contract.pipe,
        concept=contract.output.concept,
        run=SnapshotRun(
            started_at=RUN_STARTED_AT,
            finished_at=RUN_FINISHED_AT,
            server=PRODUCTION_URL,
            route=SnapshotRoute.FILES,
            method_ref=None,
            commit_sha=None,
            bundle_sha256=bundle_digest(cookbook=cookbook, package=package),
            inputs_sha256=inputs_digest(cookbook=cookbook, package=package),
        ),
        output=output,
        files=entries,
    )
    snapshot_path(package).write_text(snapshot.to_json(), encoding="utf-8")
    return snapshot


def png_bytes(*, width: int, height: int, colour: str = "white") -> bytes:
    """A plain PNG image of the given size."""
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, format="PNG")
    return buffer.getvalue()


def pdf_bytes(*, width: int, height: int) -> bytes:
    """A one-page PDF of the given size, blank."""
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(buffer, format="PDF")
    return buffer.getvalue()
