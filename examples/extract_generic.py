import asyncio
from typing import List

from pipelex import pretty_print
from pipelex.core.stuff_content import ImageContent, PageContent, TextAndImagesContent, TextContent
from pipelex.core.working_memory import WorkingMemory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from utils.results_utils import get_results_dir_path

SAMPLE_NAME = "pdf_power_extractor_generic"
PDF_PATH = "assets/extract_generic/fintech_article_with_text_in_images.pdf"


class PageContentAndMarkdownMatchError(ValueError):
    pass


# TODO: wrap this in a PipeFunc
def merge_markdown_and_images(working_memory: WorkingMemory) -> TextAndImagesContent:
    # Pages extracted from the PDF by PipeOCR
    page_contents_list = working_memory.get_stuff_as_list(item_type=PageContent, name="page_contents")
    # Markdown text extracted from the Pages by PipeLLM
    page_markdown_list = working_memory.get_stuff_as_list(item_type=TextContent, name="markdowns")

    # Check if the number of markdown and text_and_images are the same
    if len(page_markdown_list.items) != len(page_contents_list.items):
        raise PageContentAndMarkdownMatchError(
            f"The number of markdown and page_contents items are not the same: {len(page_markdown_list.items)} != {len(page_contents_list.items)}"
        )

    # Concatenate the markdown text
    concatenated_markdown_text: str = "\n".join([page_markdown.text for page_markdown in page_markdown_list.items])

    # Aggregate the images from the page contents
    image_contents: List[ImageContent] = []
    for page_content in page_contents_list.items:
        if page_content.text_and_images.images:
            image_contents.extend(page_content.text_and_images.images)

    return TextAndImagesContent(
        text=TextContent(text=concatenated_markdown_text),
        images=image_contents,
    )


async def extract_generic(pdf_url: str) -> TextAndImagesContent:
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=pdf_url,
        concept_str="PDF",
        name="pdf",
    )
    pipe_output, _ = await execute_pipeline(
        pipe_code="power_extractor",
        working_memory=working_memory,
    )
    working_memory = pipe_output.working_memory
    markdown_and_images: TextAndImagesContent = merge_markdown_and_images(working_memory)
    return markdown_and_images


# start Pipelex
Pipelex.make()
# run sample using asyncio
markdown_and_images = asyncio.run(extract_generic(pdf_url=PDF_PATH))

# output results
pretty_print(markdown_and_images)
output_dir = get_results_dir_path(sample_name=SAMPLE_NAME)
markdown_and_images.save_to_directory(directory=output_dir)
