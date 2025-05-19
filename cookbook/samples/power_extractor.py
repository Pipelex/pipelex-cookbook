# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio
from typing import List

from pydantic import BaseModel
from pipelex import pretty_print
from pipelex.core.stuff_content import ImageContent, TextAndImagesContent, TextContent
from pipelex.core.working_memory import WorkingMemory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.libraries.pipelines.documents import PageContent
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

SAMPLE_NAME = "extract_table"


class TextAndImage(BaseModel):
    text: str
    images: List[str]


async def simple_ocr(page_scan: str):
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=page_scan,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="extract_page_contents_from_pdf",
        working_memory=working_memory,
    )
    text_and_image = pipe_output.main_stuff_as_list(item_type=PageContent)

    pretty_print(text_and_image)


async def power_extractor(page_scan: str):
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=page_scan,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="update_page_content_with_markdown",
        working_memory=working_memory,
    )
    working_memory = pipe_output.working_memory
    merged_text = merge_markdown_and_images(working_memory)
    pretty_print(merged_text)


def merge_markdown_and_images(working_memory: WorkingMemory) -> TextAndImage:
    pages_markdown = working_memory.main_stuff_as_list(item_type=TextContent)
    page_contents = working_memory.get_stuff_as_list(item_type=PageContent, name="page_content")
    if len(pages_markdown.items) != len(page_contents.items):
        raise ValueError("The number of markdown and text_and_images are not the same")
    concatenated_text: str = "\n".join([page_markdown.text for page_markdown in pages_markdown.items])
    concatenated_images: List[str] = []
    for page_content in page_contents.items:
        if page_content.text_and_images.images:
            concatenated_images.extend([image.url for image in page_content.text_and_images.images])
    return TextAndImage(
        text=concatenated_text,
        images=concatenated_images,
    )


IMAGE_URL = "data/table_1.png"
# PDF_URL = "data/solar_system.pdf"
PDF_URL = "https://arxiv.org/pdf/2201.04234"
Pipelex.make()
asyncio.run(
    # simple_ocr(
    #     page_scan=PDF_URL,
    # )
    power_extractor(
        page_scan=PDF_URL,
    )
)
