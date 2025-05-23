# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_content import TextAndImagesContent
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

from pipelex_libraries.pipelines.examples.power_extractor.power_extractor import merge_markdown_and_images
from utils.results_utils import get_results_dir_path

SAMPLE_NAME = "pdf_2_power_extractor"


async def power_extractor(pdf_url: str) -> None:
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
    pretty_print(markdown_and_images)

    output_dir = get_results_dir_path(sample_name=SAMPLE_NAME)
    markdown_and_images.save_to_directory(directory=output_dir)


async def main():
    # simple OCR method would have been insufficient
    PDF_PATH_2 = "assets/fintech_article_with_text_in_images.pdf"
    await power_extractor(
        pdf_url=PDF_PATH_2,
    )


Pipelex.make()
asyncio.run(main())
