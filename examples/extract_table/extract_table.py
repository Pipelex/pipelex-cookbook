import asyncio

from pipelex.core.stuffs.image_content import ImageContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.extract_table.table import HtmlTable
from utils.results_utils import output_result

SAMPLE_NAME = "extract_table"
IMAGE_URL = "assets/extract_table/table_1.png"


async def extract_table(table_screenshot: str) -> HtmlTable:
    pipe_output = await execute_pipeline(
        pipe_code="extract_html_table_and_review",
        inputs={
            "table_screenshot": {
                "concept": "tables.TableScreenshot",
                "content": ImageContent(url=table_screenshot),
            }
        },
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
