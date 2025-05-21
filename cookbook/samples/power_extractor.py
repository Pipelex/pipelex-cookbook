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
from pipelex.tools.utils.file_utils import save_text_to_path

from pipelex_libraries.pipelines.power_extractor.power_extractor import merge_markdown_and_images

SAMPLE_NAME = "extract_table"


async def power_extractor(
    pdf_url: str,
    export_dir: Optional[str] = None,
) -> None:
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=pdf_url,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="power_extractor",
        working_memory=working_memory,
        params={"export_dir": export_dir} if export_dir else None,
    )
    working_memory = pipe_output.working_memory
    markdown_and_images = merge_markdown_and_images(working_memory)
    pretty_print(markdown_and_images)

    # Save the markdown and images to a file
    # TODO: Use ActivityHandlerForResultFiles for exporting results

    if export_dir:
        save_text_to_path(
            text=markdown_and_images.text.rendered_markdown() if markdown_and_images.text else "",
            path=os.path.join(export_dir, "markdown_with_ocr_then_vision.md"),
        )


async def main():
    # 2 pages PDF with some illustrations
    # OCR method only would have been sufficient (see markdown_with_ocr_then_vision.md VS markdown_with_ocr.md)
    PDF_URL_1 = "data/illustrated_train_article.pdf"
    await power_extractor(
        pdf_url=PDF_URL_1,
        export_dir="results/power_extractor/illustrated_train_article/",
    )

    # A page with a diagram with text inside
    # OCR method would have been insufficient (see markdown_with_ocr_then_vision.md VS markdown_with_ocr.md)
    PDF_URL_2 = "data/fintech_article_with_text_in_images.pdf"
    await power_extractor(
        pdf_url=PDF_URL_2,
        export_dir="results/power_extractor/fintech_article_with_text_in_images/",
    )


Pipelex.make()

# Run both extractions in a single asyncio.run call
asyncio.run(main())
