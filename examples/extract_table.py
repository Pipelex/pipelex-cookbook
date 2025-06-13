import asyncio

from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from pipelex_libraries.pipelines.examples.extract_table.table import HtmlTable
from utils.results_utils import output_result

SAMPLE_NAME = "extract_table"
IMAGE_URL = "assets/extract_table/table_1.png"


async def extract_table(table_screenshot: str) -> HtmlTable:
    working_memory = WorkingMemoryFactory.make_from_image(
        image_url=table_screenshot,
        concept_code="tables.TableScreenshot",
        name="table_screenshot",
    )
    pipe_output, _ = await execute_pipeline(
        pipe_code="extract_html_table_and_review",
        working_memory=working_memory,
    )
    html_table = pipe_output.main_stuff_as(content_type=HtmlTable)
    return html_table


# start Pipelex
Pipelex.make()
# run sample using asyncio
html_table = asyncio.run(extract_table(IMAGE_URL))

# output results
output_result(
    sample_name=SAMPLE_NAME,
    title="HTML Table extracted",
    file_name="extracted_table.html",
    content=html_table.inner_html_table,
)
