import asyncio

from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.b_basics.document_extract.extract_gantt.gantt_struct import GanttChart
from examples.constants import LIBRARY_DIRS
from utils.results_utils import output_result

SAMPLE_NAME = "extract_gantt"
IMAGE_URL = "https://pipelex-web.s3.us-west-2.amazonaws.com/cookbook/gantt_tree_house.png"
# IMAGE_URL = "assets/gantt/gantt_tree_house.png"


async def extract_gantt(image_url: str) -> GanttChart:
    # Run the pipe
    pipe_output = await execute_pipeline(
        pipe_code="extract_gantt_by_steps",
        inputs={
            "gantt_chart_image": {
                "concept": "gantt.GanttChartImage",
                "content": {"url": image_url},
            }
        },
    )
    # Output the result
    return pipe_output.main_stuff_as(content_type=GanttChart)


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        # run sample using asyncio
        gantt_chart = asyncio.run(extract_gantt(IMAGE_URL))

        # Display cost report (tokens used and cost)
        get_report_delegate().generate_report()

        output_result(
            sample_name=SAMPLE_NAME,
            title="Gantt Chart",
            file_name="gantt_chart.json",
            content=gantt_chart.rendered_json(),
        )
