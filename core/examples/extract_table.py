# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio

from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

from pipelex_libraries.pipelines.examples.extraction.tables import HtmlTable
from utils.results_utils import output_result

SAMPLE_NAME = "extract_table"


async def extract_table(table_screenshot: str):
    working_memory = WorkingMemoryFactory.make_from_image(
        image_url=table_screenshot,
        concept_code="tables.TableScreenshot",
        name="table_screenshot",
    )
    pipe_output = await run_pipe_code(
        pipe_code="extract_html_table_and_review",
        working_memory=working_memory,
    )
    html_table = pipe_output.main_stuff_as(content_type=HtmlTable)

    output_result(
        sample_name=SAMPLE_NAME,
        title="HTML Table extracted",
        file_name="extracted_table.html",
        content=html_table.inner_html_table,
    )


IMAGE_URL = "assets/table_1.png"
Pipelex.make()
asyncio.run(
    extract_table(
        table_screenshot=IMAGE_URL,
    )
)
