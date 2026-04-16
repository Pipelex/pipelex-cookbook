from typing import Literal

from pipelex.core.stuffs.structured_content import StructuredContent
from pydantic import Field


class ReviewAnalysis(StructuredContent):
    """Structured analysis of a product review."""

    sentiment: Literal["positive", "neutral", "negative"] = Field(..., description="Overall sentiment.")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall score from 0.0 to 1.0.")
    key_themes: list[str] = Field(default_factory=list, description="Short descriptors of what the reviewer talks about.")
    complaints: list[str] = Field(default_factory=list, description="Specific complaints raised.")
    feature_requests: list[str] = Field(default_factory=list, description="Features explicitly or implicitly requested.")
    standout_praise: list[str] = Field(default_factory=list, description="Things the reviewer liked.")
