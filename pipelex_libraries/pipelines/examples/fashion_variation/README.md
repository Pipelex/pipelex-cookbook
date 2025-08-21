# Fashion Variation Pipeline

A Pipelex pipeline that analyzes fashion photos and generates creative variations by modifying specific garment details using AI image generation.

## Overview

This pipeline takes a fashion photograph as input and:

1. **Analyzes** the garments, styles, colors, and setting
2. **Generates** a creative variation idea for one specific garment detail  
3. **Creates** a new image with the variation applied while maintaining the original composition

## Pipeline Structure

### Input
- **Fashion Photo**: Any image containing fashion garments (Image concept)

### Output  
- **Varied Fashion Photo**: New image with a creative variation applied (Image concept)

### Pipeline Steps

1. **Fashion Analysis** (`analyze_fashion_photo`)
   - Identifies all visible garments and their details
   - Analyzes colors, materials, styles, and setting
   - Uses vision LLM to create structured analysis

2. **Variation Generation** (`generate_variation_idea`) 
   - Creates a creative, realistic variation for one garment detail
   - Ensures the change is subtle but noticeable
   - Considers fashion trends and feasibility

3. **Prompt Creation** (`create_generation_prompt`)
   - Builds a detailed image generation prompt
   - Maintains original composition and setting
   - Applies the specific variation to the targeted garment

4. **Image Generation** (`generate_fashion_variation`)
   - Uses AI image generation to create the varied photo
   - Preserves pose, lighting, and background
   - Applies only the specified garment modification

## Models and Concepts

### Python Models (`fashion_models.py`)

- **`Garment`**: Individual garment with type, color, style, material, and details
- **`FashionAnalysis`**: Complete analysis of the fashion photo including garments, style, and setting  
- **`VariationIdea`**: Creative variation specification with target garment and modification details

### TOML Concepts (`fashion_variation.toml`)

- **`FashionGenerationPrompt`**: Refines `images.ImgGenPrompt` for fashion-specific image generation

## Usage

### Running the Example

```bash
python examples/fashion_variation.py
```

### Using in Your Code

```python
import asyncio
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipeline.execute import execute_pipeline
from pipelex.core.stuffs.stuff_content import ImageContent

async def generate_fashion_variation(image_url: str) -> ImageContent:
    # Create working memory with fashion photo
    working_memory = WorkingMemoryFactory.make_from_image(
        image_url=image_url,
        concept_str="native.Image", 
        name="fashion_photo",
    )
    
    # Execute the pipeline
    result = await execute_pipeline(
        pipe_code="fashion_variation_pipeline",
        working_memory=working_memory,
    )
    
    return result.main_stuff_as(content_type=ImageContent)
```

## Example Variations

The pipeline can generate various types of creative variations:

- **Color Changes**: "Change the shirt from blue to burgundy"
- **Pattern Additions**: "Add subtle floral pattern to plain dress"  
- **Material Modifications**: "Change from smooth to ribbed knit texture"
- **Style Updates**: "Modify collar from round to V-neck"
- **Detail Enhancements**: "Change buttons from plastic to wood"

## Configuration

### LLM Models Used
- **Vision Analysis**: `llm_to_describe_img` - For analyzing fashion photos
- **Creative Writing**: `llm_for_creative_writing` - For generating variation ideas  
- **Prompt Creation**: `llm_to_write_imgg_prompt` - For creating image generation prompts

### Image Generation
- **Model**: `fal-ai/flux-pro/v1.1-ultra` 
- **Steps**: 8 (configurable in pipeline)

## Files

- `fashion_variation.toml` - Pipeline definition
- `fashion_models.py` - Python data models
- `__init__.py` - Module initialization
- `README.md` - This documentation

## Requirements

- Fashion photos with clearly visible garments
- Internet connection for LLM and image generation APIs
- Properly configured Pipelex environment with API keys 