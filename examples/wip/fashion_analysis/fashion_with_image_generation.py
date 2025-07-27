#!/usr/bin/env python3
"""
Fashion Analysis Pipeline with Image Generation
Extended version that includes actual image generation using Fal.ai.

This pipeline demonstrates:
1. Computer vision analysis of fashion photographs
2. Creative design variation generation
3. Actual image generation using Stable Diffusion via Fal.ai
4. Comprehensive fashion industry reporting

Usage:
    python fashion_with_image_generation.py [--image-path PATH] [--generate-image]
    
Requirements:
    - FAL_KEY environment variable set with your Fal.ai API key
    - pip install fal-client (already included in pipelex[fal])
"""

import asyncio
import argparse
import base64
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import requests
from io import BytesIO

# Add the project root to the path to import from pipelex_libraries
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from pipelex import pretty_print
from pipelex.core.stuff_content import TextContent, ImageContent
from pipelex.core.stuff_factory import StuffFactory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.wip.fashion_analysis.fashion_concepts import (
    FashionPhoto, GarmentAnalysis, DetailVariation, 
    ImagePrompt, FashionReport, GeneratedImage
)

# Import Fal.ai client
try:
    import fal_client
    FAL_AVAILABLE = True
except ImportError:
    FAL_AVAILABLE = False
    print("⚠️  Fal.ai client not available. Install with: pip install fal-client")


class EnhancedFashionAnalysisPipeline:
    """Enhanced fashion analysis pipeline with actual image generation."""
    
    def __init__(self):
        """Initialize the pipeline."""
        # Start Pipelex
        Pipelex.make()
        
        # Check for Fal.ai API key
        self.fal_key = os.getenv("FAL_KEY")
        if not self.fal_key and FAL_AVAILABLE:
            print("⚠️  FAL_KEY environment variable not set. Image generation will be disabled.")
        
    async def analyze_fashion_photo(
        self, 
        image_path: str, 
        description: Optional[str] = None
    ) -> tuple[FashionReport, ImagePrompt]:
        """
        Analyze a fashion photo and generate a variation report with image prompt.
        
        Args:
            image_path: Path to the fashion photo
            description: Optional description of the photo
            
        Returns:
            Tuple of (FashionReport, ImagePrompt) for further processing
        """
        # Handle text descriptions (for testing without actual images)
        if image_path.endswith('.txt'):
            return await self._analyze_text_description(image_path, description)
        
        # Validate image file exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        # Create the fashion photo stuff
        fashion_photo = self._create_fashion_photo_stuff(image_path, description)
        
        # Create working memory
        working_memory = WorkingMemoryFactory.make_from_multiple_stuffs([fashion_photo])
        
        # Run the analysis sequence pipeline
        pipe_output = await execute_pipeline(
            pipe_code="fashion_analysis_sequence",
            working_memory=working_memory,
        )
        
        # Get the fashion report
        fashion_report = pipe_output.main_stuff_as(content_type=FashionReport)
        
        # Extract the image prompt from the working memory
        image_prompt = self._extract_image_prompt_from_memory(working_memory)
        
        return fashion_report, image_prompt
    
    async def _analyze_text_description(self, text_path: str, description: Optional[str] = None):
        """Analyze a text description instead of an actual image."""
        with open(text_path, 'r') as f:
            text_content = f.read()
        
        # Create text content as if it were an image description
        text_stuff = StuffFactory.make_stuff(
            concept_str="fashion_analysis.FashionPhoto",
            content=TextContent(text=text_content),
            name="fashion_photo",
        )
        
        # Create working memory
        working_memory = WorkingMemoryFactory.make_from_multiple_stuffs([text_stuff])
        
        # Run the analysis sequence pipeline
        pipe_output = await execute_pipeline(
            pipe_code="fashion_analysis_sequence",
            working_memory=working_memory,
        )
        
        # Get the fashion report
        fashion_report = pipe_output.main_stuff_as(content_type=FashionReport)
        
        # Create a mock image prompt for the text description
        image_prompt = ImagePrompt(
            prompt_text=f"Professional fashion photography based on: {text_content[:200]}...",
            subject_description="Fashion model in professional pose",
            modified_garment_description="Garment with creative variation",
            other_garments_description="Complementary styling",
            photography_style="Studio lighting, editorial style",
            quality_modifiers=["high-resolution", "professional", "detailed"]
        )
        
        return fashion_report, image_prompt
    
    def _create_fashion_photo_stuff(self, image_path: str, description: Optional[str] = None):
        """Create a FashionPhoto stuff object from an image file."""
        
        # Read image as base64 for vision models
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Create image content
        image_content = ImageContent(
            image_data=image_data,
            image_format=Path(image_path).suffix.lower().replace('.', ''),
            description=description or f"Fashion photo from {os.path.basename(image_path)}"
        )
        
        # Create the stuff object
        fashion_photo = StuffFactory.make_stuff(
            concept_str="fashion_analysis.FashionPhoto",
            content=image_content,
            name="fashion_photo",
        )
        
        return fashion_photo
    
    def _extract_image_prompt_from_memory(self, working_memory) -> ImagePrompt:
        """Extract the ImagePrompt from the working memory after pipeline execution."""
        # This is a simplified extraction - in a real implementation,
        # you'd need to properly extract from the pipeline results
        return ImagePrompt(
            prompt_text="Professional fashion photography with creative variation",
            subject_description="Fashion model in editorial pose",
            modified_garment_description="Garment with innovative design modification",
            other_garments_description="Complementary styling elements",
            photography_style="Studio lighting, high-end fashion photography",
            quality_modifiers=["high-resolution", "editorial", "professional", "detailed textures"]
        )
    
    async def generate_variation_image(
        self, 
        image_prompt: ImagePrompt, 
        output_path: Optional[str] = None
    ) -> GeneratedImage:
        """
        Generate a new fashion image using Fal.ai Stable Diffusion.
        
        Args:
            image_prompt: The prompt for image generation
            output_path: Optional path to save the generated image
            
        Returns:
            GeneratedImage with generation details
        """
        if not FAL_AVAILABLE or not self.fal_key:
            return self._create_placeholder_image(image_prompt, output_path)
        
        if output_path is None:
            output_path = f"generated_fashion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            print(f"🎨 Generating image with Fal.ai...")
            print(f"📝 Prompt: {image_prompt.prompt_text}")
            
            # Use Fal.ai to generate the image
            result = fal_client.run(
                "fal-ai/flux/schnell",  # Fast Flux model
                arguments={
                    "prompt": image_prompt.prompt_text,
                    "image_size": "landscape_4_3",
                    "num_inference_steps": 4,  # Fast generation
                    "enable_safety_checker": True,
                }
            )
            
            # Download and save the generated image
            if result and "images" in result and len(result["images"]) > 0:
                image_url = result["images"][0]["url"]
                
                # Download the image
                response = requests.get(image_url)
                response.raise_for_status()
                
                # Save the image
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                generated_image = GeneratedImage(
                    image_path=output_path,
                    generation_parameters={
                        "model": "fal-ai/flux/schnell",
                        "image_size": "landscape_4_3",
                        "num_inference_steps": 4,
                        "enable_safety_checker": True
                    },
                    prompt_used=image_prompt.prompt_text,
                    model_used="fal-ai/flux/schnell",
                    generation_timestamp=datetime.now().isoformat()
                )
                
                print(f"✅ Image generated successfully: {output_path}")
                return generated_image
            else:
                raise Exception("No images returned from Fal.ai")
                
        except Exception as e:
            print(f"❌ Error generating image with Fal.ai: {e}")
            return self._create_placeholder_image(image_prompt, output_path)
    
    def _create_placeholder_image(self, image_prompt: ImagePrompt, output_path: Optional[str]) -> GeneratedImage:
        """Create a placeholder GeneratedImage when actual generation fails."""
        if output_path is None:
            output_path = f"placeholder_fashion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Save the prompt as a text file
        with open(output_path, 'w') as f:
            f.write(f"Fashion Image Generation Prompt\n")
            f.write(f"================================\n\n")
            f.write(f"Prompt: {image_prompt.prompt_text}\n\n")
            f.write(f"Subject: {image_prompt.subject_description}\n")
            f.write(f"Modified Garment: {image_prompt.modified_garment_description}\n")
            f.write(f"Other Garments: {image_prompt.other_garments_description}\n")
            f.write(f"Photography Style: {image_prompt.photography_style}\n")
            f.write(f"Quality Modifiers: {', '.join(image_prompt.quality_modifiers)}\n")
        
        return GeneratedImage(
            image_path=output_path,
            generation_parameters={"model": "placeholder", "note": "Actual generation requires Fal.ai API key"},
            prompt_used=image_prompt.prompt_text,
            model_used="placeholder",
            generation_timestamp=datetime.now().isoformat()
        )


def create_sample_fashion_photo(sample_dir: Path) -> str:
    """Create a sample fashion photo description for testing."""
    sample_path = sample_dir / "sample_fashion.txt"
    
    sample_description = """
Professional fashion photography of a young woman in her twenties, standing in a confident pose with hands on hips. She is wearing:

1. A navy blue blazer with notched lapels, structured shoulders, and silver buttons
2. A white cotton button-down shirt underneath, with the collar visible
3. High-waisted straight-leg trousers in charcoal gray
4. Black leather pointed-toe pumps with 3-inch heels
5. A delicate gold chain necklace
6. Small gold stud earrings

The styling is professional and modern, with a classic color palette of navy, white, gray, and black. The blazer has a tailored fit with clean lines, the shirt is crisp and well-pressed, and the trousers have a contemporary high-waisted silhouette. The overall aesthetic is sophisticated business attire suitable for a corporate environment.

The background is a clean white studio backdrop with professional lighting that creates subtle shadows and highlights the fabric textures. The photography style is editorial fashion with sharp focus and high contrast.
"""
    
    sample_path.write_text(sample_description.strip())
    return str(sample_path)


async def main():
    """Main function to run the enhanced fashion analysis pipeline."""
    parser = argparse.ArgumentParser(description="Enhanced Fashion Analysis Pipeline with Image Generation")
    parser.add_argument(
        "--image-path", 
        type=str, 
        help="Path to the fashion photo to analyze (or .txt file with description)"
    )
    parser.add_argument(
        "--description", 
        type=str, 
        help="Optional description of the photo"
    )
    parser.add_argument(
        "--generate-image", 
        action="store_true", 
        help="Generate a new image based on the variation using Fal.ai"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="./fashion_output", 
        help="Directory to save outputs"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize pipeline
    pipeline = EnhancedFashionAnalysisPipeline()
    
    # Get image path
    if args.image_path:
        image_path = args.image_path
    else:
        # Create a sample text description for testing
        print("📝 No image provided, creating sample fashion description...")
        image_path = create_sample_fashion_photo(output_dir)
        print(f"📄 Sample created at: {image_path}")
    
    try:
        print(f"🔍 Analyzing fashion photo: {image_path}")
        
        # Run the analysis pipeline
        fashion_report, image_prompt = await pipeline.analyze_fashion_photo(
            image_path=image_path,
            description=args.description
        )
        
        # Save the report
        report_path = output_dir / f"fashion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w') as f:
            f.write(f"# {fashion_report.executive_summary}\n\n")
            f.write(f"## Original Analysis\n{fashion_report.original_analysis_summary}\n\n")
            f.write(f"## Proposed Variation\n{fashion_report.variation_description}\n\n")
            f.write(f"## Visual Generation Strategy\n{fashion_report.visual_generation_strategy}\n\n")
            f.write(f"## Recommendations\n")
            for rec in fashion_report.recommendations:
                f.write(f"- {rec}\n")
        
        print(f"📊 Fashion report saved to: {report_path}")
        
        # Display results
        pretty_print(fashion_report.executive_summary, title="Fashion Analysis Report")
        
        # Optional image generation
        if args.generate_image:
            print("\n🎨 Generating variation image...")
            generated_image = await pipeline.generate_variation_image(
                image_prompt=image_prompt,
                output_path=str(output_dir / f"generated_variation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            )
            print(f"🖼️  Generated image saved to: {generated_image.image_path}")
        
        # Generate cost report
        get_report_delegate().generate_report()
        
        # Generate pipeline flowchart
        get_pipeline_tracker().output_flowchart()
        
        print(f"\n✅ Fashion analysis complete! Check {output_dir} for outputs.")
        
        # Show next steps
        print("\n🚀 Next Steps:")
        print("1. Review the generated fashion report")
        if args.generate_image:
            print("2. Check the generated variation image")
        print("3. Consider implementing the design variation")
        print("4. Use the market assessment for business planning")
        
        if not args.generate_image:
            print("\n💡 Tip: Use --generate-image flag to create actual fashion images!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())