# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio
import os
from typing import Optional

from pipelex import pretty_print
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

from cookbook.utils.results_utils import output_result
from pipelex_libraries.pipelines.power_extractor.power_extractor import merge_markdown_and_images

SAMPLE_NAME = "power_extractor"


async def power_extractor(
    pdf_path: str,
) -> None:
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=pdf_path,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="power_extractor",
        working_memory=working_memory,
    )
    working_memory = pipe_output.working_memory
    markdown_and_images = merge_markdown_and_images(working_memory)
    pretty_print(markdown_and_images)

    if markdown_and_images.text:
        # Get the base filename without extension
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        output_result(
            sample_name=SAMPLE_NAME,
            title=f"Markdown with OCR and Vision for {base_filename}",
            file_name=f"{base_filename}_markdown.md",
            content=markdown_and_images.text.rendered_markdown(),
        )


async def main():
    # 2 pages PDF with some illustrations
    # OCR method only would have been sufficient (see markdown_with_ocr_then_vision.md VS markdown_with_ocr.md)
    PDF_PATH_1 = "data/illustrated_train_article.pdf"
    await power_extractor(
        pdf_path=PDF_PATH_1,
    )

    # A page with a diagram with text inside
    # OCR method would have been insufficient (see markdown_with_ocr_then_vision.md VS markdown_with_ocr.md)
    PDF_PATH_2 = "data/fintech_article_with_text_in_images.pdf"
    await power_extractor(
        pdf_path=PDF_PATH_2,
    )


Pipelex.make()

# Run both extractions in a single asyncio.run call
asyncio.run(main())
