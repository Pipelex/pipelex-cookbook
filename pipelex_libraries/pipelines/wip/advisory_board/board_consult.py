from typing import List

from pipelex.core.stuff_content import StructuredContent
from pydantic import Field


class BoardRecommendation(StructuredContent):
    recommendation: str = Field(..., description="Specific recommendation from the board")
    rationale: str = Field(..., description="Reasoning behind the recommendation")
    implementation_timeline: str = Field(..., description="Suggested timeline for implementation")
    resource_requirements: List[str] = Field(default_factory=list, description="Required resources")
    risks: List[str] = Field(default_factory=list, description="Potential risks identified")
    success_metrics: List[str] = Field(default_factory=list, description="Metrics to measure success")
    confidence_level: str = Field(..., description="Confidence level (high, medium, low)")


class BoardResponse(StructuredContent):
    board_name: str = Field(..., description="Name of the advisory board")
    strategic_analysis: str = Field(..., description="Strategic analysis from domain expertise")
    recommendations: List[BoardRecommendation] = Field(..., description="Specific recommendations")
    implementation_considerations: str = Field(..., description="Key implementation factors")
    risk_mitigation: List[str] = Field(default_factory=list, description="Risk mitigation strategies")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies on other areas")
