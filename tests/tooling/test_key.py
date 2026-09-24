import pytest

from scripts.exceptions import CookbookLayoutError
from scripts.key import KeyLine, parse_key
from tests.tooling.test_data import WIDGETS_KEY


class TestKey:
    def test_labelled_lines_are_grouped_by_section(self):
        key = parse_key(WIDGETS_KEY, source="key.md")
        assert key.case == "catalogue"
        assert key.planted_facts == [KeyLine(label="F1", text="The page lists three widgets: Sprocket, Flange and Gasket.")]
        assert [line.label for line in key.must] == ["M1", "M2"]
        assert key.must[1].text == "Each widget's `colour` is the colour printed beside it, in any wording."
        assert key.must_not == [KeyLine(label="N1", text="A widget listed twice.")]
        assert key.also_acceptable == []
        assert key.pass_bar == "Every Must and Must not line."

    def test_a_key_without_a_title_is_refused(self):
        with pytest.raises(CookbookLayoutError, match="# Key: <case>"):
            parse_key("## Must\nM1. Something.\n", source="key.md")

    def test_a_key_without_must_lines_is_refused(self):
        with pytest.raises(CookbookLayoutError, match="at least one labelled line under `## Must`"):
            parse_key("# Key: empty\n\n## Must not\nN1. Something.\n", source="key.md")
