"""
Fashion Analysis Concept Definitions
Defines the data structures used in the fashion analysis pipeline.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from pipelex.core.stuff_content import StuffContent


class FashionPhoto(StuffContent):
    """An input fashion photograph showing one or more garments."""
    
    image_path: str = Field(description="Path to the fashion photo file")
    image_url: Optional[str] = Field(default=None, description="URL to the fashion photo if available")
    description: Optional[str] = Field(default=None, description="Optional description of the photo")


class GarmentDetail(BaseModel):
    """Details about a specific garment in the photo."""
    
    garment_type: str = Field(description="Type of garment (e.g., dress, jacket, pants)")
    silhouette: str = Field(description="Overall shape and fit of the garment")
    materials: List[str] = Field(description="Apparent fabric types and textures")
    colors: List[str] = Field(description="Specific color names and descriptions")
    patterns: List[str] = Field(default_factory=list, description="Patterns or prints if any")
    key_details: List[str] = Field(description="Notable design elements like buttons, zippers, etc.")
    style_characteristics: List[str] = Field(description="Style descriptors like vintage, modern, etc.")


class GarmentAnalysis(StuffContent):
    """Detailed analysis of garments in the photo including type, style, colors, patterns, and key details."""
    
    garments: List[GarmentDetail] = Field(description="List of all identified garments")
    overall_style: str = Field(description="Overall styling aesthetic")
    color_palette: List[str] = Field(description="Coordinated color scheme")
    notable_elements: List[str] = Field(description="Unique or interesting design elements")
    modification_opportunities: List[str] = Field(description="Potential points for variation")


class DetailVariation(StuffContent):
    """A creative variation idea for modifying one specific detail of a garment."""
    
    selected_garment: str = Field(description="Name of the garment being modified")
    original_detail: str = Field(description="Description of the current detail")
    proposed_variation: str = Field(description="Detailed description of the new version")
    design_rationale: str = Field(description="Why this change would be interesting/beneficial")
    visual_impact: str = Field(description="How this would change the overall appearance")
    feasibility_notes: Optional[str] = Field(default=None, description="Technical feasibility considerations")


class ImagePrompt(StuffContent):
    """A detailed text prompt for generating a new fashion image with the variation."""
    
    prompt_text: str = Field(description="Complete prompt for AI image generation")
    subject_description: str = Field(description="Description of the model/person and pose")
    modified_garment_description: str = Field(description="Description of the garment with variation")
    other_garments_description: str = Field(description="Description of unchanged garments")
    photography_style: str = Field(description="Lighting, background, and composition details")
    quality_modifiers: List[str] = Field(description="Quality and style modifiers for the generation")


class GeneratedImage(StuffContent):
    """A synthetically generated fashion photo with the modified detail."""
    
    image_path: str = Field(description="Path to the generated image file")
    generation_parameters: dict = Field(description="Parameters used for image generation")
    prompt_used: str = Field(description="The exact prompt used for generation")
    model_used: str = Field(description="The AI model used for generation")
    generation_timestamp: str = Field(description="When the image was generated")


class MarketAssessment(BaseModel):
    """Market potential assessment for the design variation."""
    
    target_demographic: List[str] = Field(description="Target customer segments")
    market_viability: str = Field(description="Assessment of commercial potential")
    price_point_estimate: Optional[str] = Field(default=None, description="Estimated retail price range")
    trend_alignment: str = Field(description="How well it aligns with current trends")
    competitive_advantage: List[str] = Field(description="Unique selling points")


class TechnicalConsiderations(BaseModel):
    """Technical considerations for implementing the design variation."""
    
    manufacturing_complexity: str = Field(description="Difficulty level of production")
    required_materials: List[str] = Field(description="Materials needed for the variation")
    production_techniques: List[str] = Field(description="Manufacturing techniques required")
    cost_implications: str = Field(description="Impact on production costs")
    timeline_estimate: Optional[str] = Field(default=None, description="Estimated development timeline")


class FashionReport(StuffContent):
    """A comprehensive report of the analysis and variation process."""
    
    executive_summary: str = Field(description="Brief overview of analysis and variation")
    original_analysis_summary: str = Field(description="Summary of the garment analysis")
    variation_description: str = Field(description="Detailed description of the proposed variation")
    market_assessment: MarketAssessment = Field(description="Market potential analysis")
    technical_considerations: TechnicalConsiderations = Field(description="Implementation considerations")
    visual_generation_strategy: str = Field(description="How the AI prompt was constructed")
    recommendations: List[str] = Field(description="Next steps and recommendations")
    report_timestamp: str = Field(description="When the report was generated")


class OptimizedTweet(StuffContent):
    """An optimized tweet for social media sharing (compatibility with existing examples)."""
    
    text: str = Field(description="The optimized tweet text")