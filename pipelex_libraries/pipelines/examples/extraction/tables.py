# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

from typing import ClassVar, Self

from bs4 import BeautifulSoup
from pipelex.core.stuff_content import StructuredContent
from pydantic import model_validator


class HtmlTable(StructuredContent):
    title: str
    inner_html_table: str
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
            raise ValueError("HTML must contain exactly one table element")

        # Validate that only allowed table-related tags are present
        all_tags = {tag.name for tag in soup.find_all()}
        invalid_tags = all_tags - self.allowed_tags
        if invalid_tags:
            raise ValueError(f"Invalid HTML tags found: {invalid_tags}")

        # Check if table has any content
        if not tables[0].find_all(["tr"]):
            raise ValueError("Table must contain at least one row")

        return self
