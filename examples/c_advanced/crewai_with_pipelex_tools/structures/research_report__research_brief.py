from pipelex.core.stuffs.structured_content import StructuredContent
from pydantic import Field


class ResearchBrief(StructuredContent):
    """A final research brief synthesizing verified sources."""

    executive_summary: str = Field(..., description="One-paragraph overview.")
    key_findings: list[str] = Field(default_factory=list, description="Key findings as short bullets.")
    open_questions: list[str] = Field(default_factory=list, description="Questions still open after research.")
