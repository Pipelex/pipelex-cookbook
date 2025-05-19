# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio

from pipelex import pretty_print
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

from pipelex_libraries.pipelines.power_extractor.power_markdown_extractor import merge_markdown_and_images

SAMPLE_NAME = "extract_table"


async def power_markdown_extractor(pdf_url: str):
    working_memory = WorkingMemoryFactory.make_from_pdf(
        pdf_url=pdf_url,
        concept_code="documents.PDF",
        name="pdf",
    )
    pipe_output = await run_pipe_code(
        pipe_code="power_markdown_extractor",
        working_memory=working_memory,
    )
    working_memory = pipe_output.working_memory
    markdown_and_images = merge_markdown_and_images(working_memory)
    pretty_print(markdown_and_images)

    # Save the markdown and images to a file
    with open("markdown_and_images.md", "w") as f:
        f.write(markdown_and_images.text)


# PDF_URL = "data/solar_system.pdf"
PDF_URL = "https://arxiv.org/pdf/2201.04234"
Pipelex.make()
asyncio.run(
    power_markdown_extractor(
        pdf_url=PDF_URL,
    )
)
