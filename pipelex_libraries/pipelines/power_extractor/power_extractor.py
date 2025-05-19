from typing import List

from pipelex.core.stuff_content import ImageContent, PageContent, TextAndImagesContent, TextContent
from pipelex.core.working_memory import WorkingMemory
from pydantic import BaseModel


class PageContentAndMarkdownMatchError(ValueError):
    pass


class TextAndImages(BaseModel):
    text: str
    images: List[str]


# TODO: wrap this in a PipeFunc
def merge_markdown_and_images(working_memory: WorkingMemory) -> TextAndImagesContent:
    # Pages extracted from the PDF by PipeOCR
    page_contents_list = working_memory.get_stuff_as_list(item_type=PageContent, name="page_content")
    # Markdown text extracted from the Pages by PipeLLM
    page_markdown_list = working_memory.main_stuff_as_list(item_type=TextContent)

    # Check if the number of markdown and text_and_images are the same
    if len(page_markdown_list.items) != len(page_contents_list.items):
        raise PageContentAndMarkdownMatchError(
            f"The number of markdown and text_and_images are not the same: {len(page_markdown_list.items)} != {len(page_contents_list.items)}"
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
