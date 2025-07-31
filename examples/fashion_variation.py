import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_content import ImageContent
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

SAMPLE_NAME = "fashion_variation"
# You can replace this with your own fashion photo URL or local file path
IMAGE_URL = "https://example.com/fashion-photo.jpg"  # Replace with actual fashion photo


async def generate_fashion_variation(image_url: str) -> ImageContent:
    """
    Generate a fashion variation by:
    1. Analyzing the original fashion photo
    2. Creating a creative variation idea for one garment detail
    3. Generating a new image with the variation applied
    """
    # Create Working Memory with the fashion photo
    working_memory = WorkingMemoryFactory.make_from_image(
        image_url=image_url,
        concept_str="native.Image",
        name="fashion_photo",
    )

    # Run the fashion variation pipeline
    pipe_output = await execute_pipeline(
        pipe_code="fashion_variation_pipeline",
        working_memory=working_memory,
    )

    # Output the result - a new image with the fashion variation
    return pipe_output.main_stuff_as(content_type=ImageContent)


async def main():
    """Main function to run the fashion variation example"""
    print("🎨 Running Fashion Variation Pipeline")
    print(f"📸 Input: {IMAGE_URL}")
    print("=" * 60)

    # Initialize Pipelex
    Pipelex.make()

    try:
        # Generate the fashion variation
        varied_image = await generate_fashion_variation(IMAGE_URL)

        print("✅ Fashion variation generated successfully!")
        print(f"🖼️  Varied image URL: {varied_image.url}")

        # Display the result
        pretty_print(varied_image, title="Fashion Variation Result")

    except Exception as e:
        print(f"❌ Error generating fashion variation: {e}")
        raise

    finally:
        # Display cost report (tokens used and cost)
        get_report_delegate().generate_report()

        # Output pipeline flowchart
        get_pipeline_tracker().output_flowchart()


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
