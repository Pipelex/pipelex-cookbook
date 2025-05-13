# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

from pipelex.core.stuff_content import StructuredContent
from pydantic import Field


class StructuredSummary(StructuredContent):
    summary: str = Field(description="Summary of the text, super clear and factual")
    abstract: str = Field(description="Abstract of the summary 1 short sentences")
    main_concepts: list[str] = Field(default_factory=list, description="Array of main concepts tackled in the text")
