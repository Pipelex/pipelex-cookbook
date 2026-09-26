"""Constants for the cookbook tooling's tests: the fixture cookbook's editorial file, bundles and contract snapshots, and hand-built outputs."""

from collections.abc import Callable
from pathlib import Path

from pydantic import JsonValue

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
    "advisory_board": {"text": "# Strategic report\n\n## Consensus\n\nShorten onboarding before adding features."},
    "answer_from_documents": {
        "status": "answered",
        "answer": "Three of the report's sources are its own.",
        "explanation": "The references appendix attributes three entries to the publisher of the report.",
        "supporting_passages": [
            {
                "document_identifier": "report.pdf",
                "page_number": 21,
                "quote": "Washington, D.C.: Example Research Center.",
                "relevance_reasoning": "The entry names the report's own publisher.",
            }
        ],
        "contradictions_noted": [],
        "caveats": "Only the appendix was counted.",
        "confidence": "high",
    },
    "blog_article_generator": {
        "seo_title": "Capybaras, the calmest animals on the riverbank",
        "meta_description": "Why capybaras get along with everyone.",
        "content": "# Capybaras\n\nCapybaras are the largest rodents in the world.",
    },
    "discord_newsletter": {"text": "<html><body><h1>This week on the server</h1></body></html>"},
    "extract_dpe": {
        "address": "12 rue de l'Exemple, 75011 Paris",
        "date_of_issue": "2024-05-02",
        "date_of_expiration": "2034-05-01",
        "energy_efficiency_class": "D",
        "per_year_per_m2_consumption": 230.0,
        "co2_emission_class": "B",
        "per_year_per_m2_co2_emissions": 9,
        "yearly_energy_costs_min": 900.0,
        "yearly_energy_costs_max": 1200.0,
    },
    "extract_gantt": {
        "tasks": [{"name": "Foundations", "start_date": "2026-03-02", "end_date": "2026-03-13"}],
        "milestones": [{"name": "Roof on", "milestone_date": "2026-04-10"}],
    },
    "extract_generic": {"items": [{"text": "# Page 1\n\nThe first page."}, {"text": "# Page 2\n\nThe second page."}]},
    "extract_slides": {"text": "## Slide 1: Welcome\n\nA title slide with the company logo."},
    "gen_expense_data": {
        "items": [
            {
                "employee": {"employee_id": "E-001", "full_name": "Alex Martin", "email": "alex@example.com", "department": "Sales"},
                "expenses_with_receipts": [
                    {
                        "expense": {"amount": 42.5, "currency": "EUR"},
                        "receipt": {"url": "pipelex-storage://org_1/results/receipt.png"},
                        "scenario": {"label": "legitimate"},
                    }
                ],
                "html_report": {"inner_html": "<h1>Expenses</h1>", "css_class": "report"},
            }
        ]
    },
    "gen_synthetic_data": {
        "items": [
            {
                "student_name": "Sam Lee",
                "current_performance": "Average",
                "learns_best_with": "Visual examples",
                "pace": "Normal",
                "complexity": "Balanced",
                "strengths": "Geometry",
                "needs_help_with": "Fractions",
                "prior_knowledge": "Basic algebra",
                "hobbies_interests": "Football",
                "career_goals": "Architect",
                "example_style": "Real-world problems",
                "question_format": "Multiple choice",
            }
        ]
    },
    "research_report": {"text": "# Research Report\n\n## Question\n\nWhat is the question?\n\n---\nGenerated by Pipelex"},
}
