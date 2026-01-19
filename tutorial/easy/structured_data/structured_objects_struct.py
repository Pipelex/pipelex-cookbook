"""
Structured content definitions for Tutorial 2.

Note: These are optional when using inline structure definitions in PLX files.
They provide IDE autocomplete and type checking benefits.
"""

from pipelex.core.stuffs.structured_content import StructuredContent
from pydantic import Field


class BookIdea(StructuredContent):
    """A structured book idea with title, genre, and synopsis."""

    title: str = Field(description="The book title")
    genre: str = Field(description="The genre of the book")
    synopsis: str | None = Field(default=None, description="A brief synopsis of the book")
    target_audience: str | None = Field(default=None, description="Who this book is for")


class Answer(StructuredContent):
    """An answer to a question about a document."""

    answer: str = Field(description="The answer to the question")
    confidence: str | None = Field(default=None, description="How confident the answer is (high/medium/low)")
    source_quote: str | None = Field(default=None, description="A quote from the document supporting the answer")
