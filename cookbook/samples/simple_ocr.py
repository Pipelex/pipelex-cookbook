# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio
from typing import List, Optional

from pipelex import pretty_print
from pipelex.core.stuff_content import PageContent
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

PDF_URL = "data/illustrated_train_article.pdf"
OUTPUT_DIR = "results/ocr/illustrated_train_article/"


async def simple_ocr(page_scan: str, export_dir: Optional[str] = None):
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=page_scan,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="extract_page_contents_from_pdf",
        working_memory=working_memory,
    )
    page_content_list = pipe_output.main_stuff_as_list(item_type=PageContent)
    pretty_print(page_content_list)
    if export_dir:
        for page_content in page_content_list.items:
            page_content.save_to_directory(directory=export_dir)


async def main():
    Pipelex.make()
    await simple_ocr(
        page_scan=PDF_URL,
        export_dir=OUTPUT_DIR,
    )


if __name__ == "__main__":
    asyncio.run(main())
