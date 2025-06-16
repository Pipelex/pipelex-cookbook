from typing import ClassVar

from bs4 import BeautifulSoup
from pipelex.core.stuff_content import StructuredContent
from pydantic import Field, model_validator
from typing_extensions import Self


class HtmlTable(StructuredContent):
    title: str
    inner_html_table: str = Field(examples=["<table><tr><th>Name</th><th>Age</th></tr><tr><td>John</td><td>25</td></tr></table>"])
    # Class variable to store allowed HTML tags for table structure
    allowed_tags: ClassVar[set[str]] = {
        "br",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
    }

    @model_validator(mode="after")
    def validate_html_table(self) -> Self:
        soup = BeautifulSoup(self.inner_html_table, "html.parser")
        # Check if there's exactly one table element
        tables = soup.find_all("table")
        if len(tables) != 1:
            raise ValueError(f"HTML must contain exactly one table element. inner_html_table:\n{self.inner_html_table}")
        the_table = tables[0]

        # Validate that only allowed table-related tags are present
        all_tags = {tag.name for tag in soup.find_all()}
        invalid_tags = all_tags - self.allowed_tags
        if invalid_tags:
            raise ValueError(f"Invalid HTML tags found: {invalid_tags}")

        # Check if table has any content
        if not the_table.find_all(["tr"]):
            raise ValueError("Table must contain at least one row")

        return self
