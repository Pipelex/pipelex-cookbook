import asyncio

from pipelex import pretty_print
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.extract_gantt.gantt_struct import GanttChart
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


# start Pipelex
Pipelex.make()

# run sample using asyncio
gantt_chart = asyncio.run(extract_gantt(IMAGE_URL))

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()

# output results
output_result(SAMPLE_NAME, "Gantt Chart", "gantt_chart.json", gantt_chart.rendered_json())
