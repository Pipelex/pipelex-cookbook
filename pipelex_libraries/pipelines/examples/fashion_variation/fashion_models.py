from typing import List, Optional

from pipelex.core.stuffs.stuff_content import StructuredContent
from pydantic import Field


class Garment(StructuredContent):
    """Individual garment detected in the fashion photo"""

    type: str = Field(..., description="Type of garment (e.g., shirt, pants, dress, jacket)")
    color: str = Field(..., description="Primary color of the garment")
    style: str = Field(..., description="Style description (e.g., casual, formal, vintage)")
    material: Optional[str] = Field(None, description="Apparent material or fabric type")
    details: List[str] = Field(default_factory=list, description="Notable design details")


class FashionAnalysis(StructuredContent):
    """Analysis of garments in a fashion photo"""

    garments: List[Garment] = Field(..., description="List of detected garments")
    overall_style: str = Field(..., description="Overall style aesthetic of the outfit")
    color_scheme: str = Field(..., description="Description of the color palette")
    setting: str = Field(..., description="Setting or context of the photo")


class VariationIdea(StructuredContent):
    """Creative variation idea for a fashion garment"""

    target_garment: str = Field(..., description="Which garment will be modified")
    variation_type: str = Field(..., description="Type of variation (color, pattern, texture, style detail)")
    original_detail: str = Field(..., description="Description of the original detail being changed")
    new_detail: str = Field(..., description="Description of the new variation")
    reasoning: str = Field(..., description="Why this variation would be interesting or fashionable")
