"""Constants for the cookbook tooling's tests: the fixture cookbook's editorial file, answer keys and contract snapshots."""

from collections.abc import Callable
from pathlib import Path

from scripts.contract import Contract, ContractField, ContractInput, ContractOutput
from scripts.library import LibraryMethod, LibrarySnapshot

FIXTURE_ADDRESS = "github.com/Pipelex/pipelex-cookbook"
FIXTURE_VERSION = "0.9.0"
LIBRARY_ADDRESS = "github.com/Pipelex/methods"
LIBRARY_REPOSITORY = "Pipelex/methods"
LIBRARY_TAG = "v0.4.0"
WIDGETS_SAMPLE_URL = "https://raw.githubusercontent.com/Pipelex/pipelex-cookbook/main/assets/extract_widgets/catalogue.png"

COOKBOOK_TOML = f"""address = "{FIXTURE_ADDRESS}"
repository = "Pipelex/pipelex-cookbook"

[library]
address = "{LIBRARY_ADDRESS}"
repository = "{LIBRARY_REPOSITORY}"
tag = "{LIBRARY_TAG}"

[methods.extract_widgets]
title = "Widget extraction"
pitch = "Read a catalogue page and list every widget on it"
sample_labels = {{ catalogue = "sample catalogue" }}
app_dir = "widgets-app"
yours_dir = "widgets"
yours_change = "add each widget's price to what it extracts"
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

WIDGETS_KEY = """# Key: catalogue

Inputs: one catalogue page listing three widgets.

## Planted facts
F1. The page lists three widgets: Sprocket, Flange and Gasket.

## Must
M1. `widgets` holds three widgets: Sprocket, Flange and Gasket.
M2. Each widget's `colour` is the colour printed beside it,
in any wording.

## Must not
N1. A widget listed twice.

## Pass bar
Every Must and Must not line.
"""

WORDS_KEY = """# Key: fox

Inputs: one sentence of four words.

## Must
M1. The output says the text has four words.

## Pass bar
Every Must line.
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
