import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.image_content import ImageContent
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

SAMPLE_NAME = "photopposite"
IMAGE_URL = "https://storage.googleapis.com/public_test_files_7fa6_4277_9ab/fashion/fashion_photo_1.jpg"


async def generate_photopposite(image_url: str):
    """Generate the opposite of a photo using the pipeline."""

    pipe_output = await execute_pipeline(
        pipe_code="gen_photopposite",
        input_memory={
            "photo": {
                "concept": "Image",
                "content": ImageContent(url=image_url),
            }
        },
    )

    return pipe_output


# Start Pipelex
Pipelex.make()

print(f"Using photo: {IMAGE_URL}")

# Run the pipeline using asyncio
result = asyncio.run(generate_photopposite(image_url=IMAGE_URL))

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()

# Output results
pretty_print(result, title="Photo Opposite Generation Result")

# Generate pipeline flowchart
get_pipeline_tracker().output_flowchart()
