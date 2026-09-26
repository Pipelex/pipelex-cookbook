from datetime import date

import pytest
from pydantic import JsonValue

from scripts.contract import Contract, ContractInput, ContractOutput
from scripts.cookbook import OutputHints, load_cookbook
from scripts.views import OUTPUT_FOLD_LINES, day_phrase, duration_phrase, output_markdown, output_summary, sample_views
from tests.tooling.test_data import WIDGETS_CONTRACT, WORDS_CONTRACT, MakeCookbook, make_word_document_sample


def _contract(*, multiplicity: str = "single") -> Contract:
    return Contract(pipe="demo.run", output=ContractOutput(concept="demo.Result", multiplicity=multiplicity))


class TestOutputView:
    def test_a_flat_structure_is_a_field_and_value_table(self):
        output: JsonValue = {"address": "12 rue des Lilas", "energy_class": "G", "consumption": 560, "heated": True, "note": None}
        assert output_markdown(contract=_contract(), hints=OutputHints(), output=output) == (
            "| Field | Value |\n|---|---|\n| `address` | 12 rue des Lilas |\n| `energy_class` | G |\n| `consumption` | 560 |\n"
            "| `heated` | yes |\n| `note` |   |"
        )

    def test_a_list_of_structures_is_a_table_and_a_list_of_texts_bullets(self):
        output: JsonValue = {
            "tasks": [{"name": "Plan", "start": "2025-09-01"}, {"name": "Build | test", "end": "2025-09-10"}],
            "notes": ["one", "two"],
            "gaps": [],
        }
        markdown = output_markdown(contract=_contract(), hints=OutputHints(), output=output)
        assert (
            "**`tasks`**\n\n| `name` | `start` | `end` |\n|---|---|---|\n| Plan | 2025-09-01 |   |\n| Build \\| test |   | 2025-09-10 |" in markdown
        )
        assert "**`notes`**\n\n- one\n- two" in markdown
        assert "**`gaps`**\n\nNone." in markdown

    def test_a_long_text_is_a_paragraph_under_its_field(self):
        answer = "A long answer. " * 20
        markdown = output_markdown(contract=_contract(), hints=OutputHints(), output={"status": "answered", "answer": answer})
        assert markdown == f"| Field | Value |\n|---|---|\n| `status` | answered |\n\n**`answer`**\n\n{answer.strip()}"

    def test_a_text_output_is_markdown_with_its_headings_below_the_pages(self):
        output: JsonValue = {"text": "# Report\n\n## Findings\n\n```md\n# not a heading\n```\n\nText."}
        assert output_markdown(contract=_contract(), hints=OutputHints(), output=output) == (
            "### Report\n\n#### Findings\n\n```md\n# not a heading\n```\n\nText."
        )

    def test_a_long_text_is_shown_whole_since_the_page_folds_a_long_output_as_a_whole(self):
        text = "\n\n".join(f"Paragraph {index}." for index in range(OUTPUT_FOLD_LINES))
        assert output_markdown(contract=_contract(), hints=OutputHints(), output={"text": text}) == text

    @pytest.mark.parametrize(
        ("concept", "multiplicity", "item_label", "expected"),
        [
            ("presentation.MarkdownReport", "single", None, "The markdown report"),
            ("dpe.DPEReport", "single", None, "The DPE report"),
            ("native.Text", "single", None, "The text"),
            ("native.Text", "variable", "Page", "The pages"),
            ("synthetic_data_generation.Sample", "variable", "Profile", "The profiles"),
            ("demo.Result", "fixed", None, "The items"),
            ("demo.Summary", "variable", "Summary", "The summaries"),
        ],
    )
    def test_a_folded_output_is_named_by_its_item_label_or_its_concept(self, concept: str, multiplicity: str, item_label: str | None, expected: str):
        contract = Contract(pipe="demo.run", output=ContractOutput(concept=concept, multiplicity=multiplicity))
        assert output_summary(contract=contract, hints=OutputHints(item_label=item_label)) == expected

    def test_a_field_hinted_markdown_or_html_is_rendered_so(self):
        hints = OutputHints(formats={"content": "markdown", "text": "html"})
        article = output_markdown(contract=_contract(), hints=hints, output={"seo_title": "Capybaras", "content": "# Meet the capybara\n\nHi."})
        assert article == "| Field | Value |\n|---|---|\n| `seo_title` | Capybaras |\n\n**`content`**\n\n### Meet the capybara\n\nHi."
        newsletter = output_markdown(contract=_contract(), hints=hints, output={"text": "<!-- Summary -->\n<h2>Weekly</h2>\n\n   <p>News</p>"})
        assert newsletter == "<div>\n<!-- Summary -->\n<h3>Weekly</h3>\n   <p>News</p>\n</div>"

    def test_a_short_value_that_is_no_text_goes_to_the_table_whatever_its_fields_hint(self):
        hints = OutputHints(formats={"summary": "markdown", "score": "html", "approved": "markdown", "notes": "markdown"})
        output: JsonValue = {"summary": "## Verdict\n\nSound.", "score": 7, "approved": False, "notes": None}
        assert output_markdown(contract=_contract(), hints=hints, output=output) == (
            "| Field | Value |\n|---|---|\n| `score` | 7 |\n| `approved` | no |\n| `notes` |   |\n\n**`summary`**\n\n### Verdict\n\nSound."
        )

    def test_html_keeps_its_indentation_and_the_blank_lines_of_a_pre(self):
        page = (
            "<h2>Code</h2>\n<pre><code>def area(width, height):\n\n    return width * height\n\n\nprint(area(2, 3))\n</code></pre>\n\n"
            "<ul>\n  <li>Indented</li>\n</ul>\n   \n<pre>last</pre>"
        )
        assert output_markdown(contract=_contract(), hints=OutputHints(formats={"text": "html"}), output={"text": page}) == (
            "<div>\n<h3>Code</h3>\n<pre><code>def area(width, height):&#10;\n    return width * height&#10;&#10;\nprint(area(2, 3))\n</code></pre>\n"
            "<ul>\n  <li>Indented</li>\n</ul>\n<pre>last</pre>\n</div>"
        )

    def test_html_is_embedded_without_its_head_styles_and_scripts(self):
        report = (
            "<html lang='en'><head><title>R</title><style>td { color: red; }</style></head>\n"
            "<body>\n<h1>Report</h1>\n<script>x()</script>\n</body></html>"
        )
        markdown = output_markdown(contract=_contract(), hints=OutputHints(), output={"html_report": {"inner_html": report, "css_class": None}})
        assert markdown == "**`html_report`**\n\n<div>\n<h3>Report</h3>\n</div>"

    def test_each_item_of_a_list_output_is_under_its_label(self):
        output: JsonValue = {"items": [{"text": "# First page"}, {"text": "Second page"}]}
        markdown = output_markdown(contract=_contract(multiplicity="variable"), hints=OutputHints(item_label="Page"), output=output)
        assert markdown == "### Page 1\n\n#### First page\n\n### Page 2\n\nSecond page"

    def test_the_items_of_a_list_output_share_one_heading_shift(self):
        output: JsonValue = {"items": [{"text": "# The article\n\n## Introduction"}, {"text": "## Industry response\n\n### Banks"}]}
        markdown = output_markdown(contract=_contract(multiplicity="variable"), hints=OutputHints(item_label="Page"), output=output)
        # A `##` of the source lands at one level of the page, whichever page holds it.
        assert markdown == ("### Page 1\n\n#### The article\n\n##### Introduction\n\n### Page 2\n\n##### Industry response\n\n###### Banks")

    def test_the_fields_of_one_output_share_one_heading_shift_markdown_and_html_alike(self):
        hints = OutputHints(formats={"body": "markdown", "sidebar": "html"})
        output: JsonValue = {"body": "## Findings\n\nText.", "sidebar": "<h3>Sources</h3>"}
        assert output_markdown(contract=_contract(), hints=hints, output=output) == (
            "**`body`**\n\n### Findings\n\nText.\n\n**`sidebar`**\n\n<div>\n<h4>Sources</h4>\n</div>"
        )

    def test_a_copied_image_is_embedded_and_shown_in_a_table_cell(self):
        receipt: JsonValue = {"url": "output/items-0-receipt.png", "mime_type": "image/png", "caption": "Receipt"}
        output: JsonValue = {"photo": receipt, "expenses": [{"amount": 12, "receipt": receipt, "scenario": {"type": "legitimate"}}]}
        markdown = output_markdown(contract=_contract(), hints=OutputHints(), output=output)
        assert "**`photo`**\n\n![Receipt](output/items-0-receipt.png)" in markdown
        assert (
            '| 12 | <a href="output/items-0-receipt.png"><img src="output/items-0-receipt.png" alt="Receipt" width="160"></a> | type: legitimate |'
            in markdown
        )

    def test_a_copied_file_that_is_no_image_is_linked(self):
        markdown = output_markdown(
            contract=_contract(), hints=OutputHints(), output={"report": {"url": "output/report.pdf", "mime_type": "application/pdf"}}
        )
        assert markdown == "**`report`**\n\n[report](output/report.pdf)"

    @pytest.mark.parametrize(("seconds", "expected"), [(0.2, "1 second"), (37.4, "37 seconds"), (60, "1 minute"), (125, "2 minutes 5 seconds")])
    def test_durations(self, seconds: float, expected: str):
        assert duration_phrase(seconds) == expected

    def test_days(self):
        assert day_phrase(date(2026, 9, 28)) == "28 September 2026"


class TestSampleView:
    def test_an_image_sample_kept_here_is_embedded_from_the_page(self, make_cookbook: MakeCookbook):
        cookbook = load_cookbook(make_cookbook(with_sample=True))
        [package] = [package for package in cookbook.packages if package.name == "extract_widgets"]
        [view] = sample_views(cookbook=cookbook, package=package, contract=WIDGETS_CONTRACT)
        assert view.body == "![sample catalogue](../../assets/extract_widgets/catalogue.png)"
        assert view.is_file is True
        assert view.record is not None
        assert view.record.attribution == "The Widget Society"

    def test_a_document_sample_shows_its_preview_linking_to_it(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        (root / "assets" / "extract_widgets" / "catalogue.preview.png").write_bytes(b"png")
        cookbook = load_cookbook(root)
        [package] = [package for package in cookbook.packages if package.name == "extract_widgets"]
        contract = WIDGETS_CONTRACT.model_copy(
            update={"inputs": [ContractInput(name="catalogue", concept="widgets.CataloguePage", kind="document", multiplicity="single")]}
        )
        [view] = sample_views(cookbook=cookbook, package=package, contract=contract)
        assert view.body == (
            '<a href="../../assets/extract_widgets/catalogue.png">'
            '<img src="../../assets/extract_widgets/catalogue.preview.png" alt="sample catalogue" width="480"></a>'
        )

    def test_a_document_sample_that_is_no_pdf_is_linked(self, make_cookbook: MakeCookbook):
        root = make_cookbook()
        make_word_document_sample(root)
        cookbook = load_cookbook(root)
        [package] = [package for package in cookbook.packages if package.name == "extract_widgets"]
        assert package.contract is not None
        [view] = sample_views(cookbook=cookbook, package=package, contract=package.contract)
        assert view.body == "[sample catalogue](../../assets/extract_widgets/catalogue.docx)"

    def test_prose_is_quoted_and_a_structure_is_a_table(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        inputs_path = root / "methods" / "count_words" / "inputs.json"
        inputs_path.write_text('{"text": {"concept": "native.Text", "content": {"text": "# Brief\\n\\nThe quick fox."}}}', encoding="utf-8")
        cookbook = load_cookbook(root)
        [package] = [package for package in cookbook.packages if package.name == "count_words"]
        [view] = sample_views(cookbook=cookbook, package=package, contract=WORDS_CONTRACT)
        assert view.body == "> ### Brief\n>\n> The quick fox."
        assert view.label == "sample text"
        assert view.is_file is False
        assert view.record is None

        inputs_path.write_text('{"text": {"words": 4, "language": "en"}}', encoding="utf-8")
        cookbook = load_cookbook(root)
        [package] = [package for package in cookbook.packages if package.name == "count_words"]
        [view] = sample_views(cookbook=cookbook, package=package, contract=WORDS_CONTRACT)
        assert view.body == "| Field | Value |\n|---|---|\n| `words` | 4 |\n| `language` | en |"

    def test_a_long_list_sample_is_linked_in_inputs_json(self, make_cookbook: MakeCookbook):
        root = make_cookbook(with_sample=True)
        (root / "methods" / "count_words" / "inputs.json").write_text('{"text": [' + ",".join(['{"line": "' + "x" * 100 + '"}'] * 50) + "]}")
        cookbook = load_cookbook(root)
        [package] = [package for package in cookbook.packages if package.name == "count_words"]
        [view] = sample_views(cookbook=cookbook, package=package, contract=WORDS_CONTRACT)
        assert view.body == "[The sample text, in inputs.json](inputs.json)"
