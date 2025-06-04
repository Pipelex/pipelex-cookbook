import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_content import TextAndImagesContent
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

from pipelex_libraries.pipelines.examples.power_extractor.power_extractor import merge_markdown_and_images
from utils.results_utils import get_results_dir_path

SAMPLE_NAME = "pdf_power_extractor_generic"
PDF_PATH = "assets/fintech_article_with_text_in_images.pdf"


async def power_extractor(pdf_url: str) -> TextAndImagesContent:
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=pdf_url,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="power_extractor",
        working_memory=working_memory,
    )
    working_memory = pipe_output.working_memory
    markdown_and_images: TextAndImagesContent = merge_markdown_and_images(working_memory)
    return markdown_and_images


# start Pipelex
Pipelex.make()
# run sample using asyncio
markdown_and_images = asyncio.run(power_extractor(pdf_url=PDF_PATH))

# output results
pretty_print(markdown_and_images)
output_dir = get_results_dir_path(sample_name=SAMPLE_NAME)
markdown_and_images.save_to_directory(directory=output_dir)
