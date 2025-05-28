from pipelex.core.stuff_content import StructuredContent
from pydantic import Field


class RetrievedExcerpt(StructuredContent):
    """
    This model represents an excerpt from a text with its justification for being relevant to a question.
    """

    text: str
    justification: str = Field(..., description="The justification for why this excerpt is relevant to the question")
