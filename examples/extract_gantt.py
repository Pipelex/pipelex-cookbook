import asyncio

from pipelex import pretty_print
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from pipelex_libraries.pipelines.examples.extract_gantt.gantt import GanttChart

SAMPLE_NAME = "extract_gantt"
IMAGE_URL = "assets/gantt/gantt_tree_house.png"


async def extract_gantt(image_url: str) -> GanttChart:
    # Create Working Memory
    working_memory = WorkingMemoryFactory.make_from_image(
        image_url=image_url,
        concept_str="gantt.GanttImage",
        name="gantt_chart_image",
    )

    # Run the pipe
    pipe_output, _ = await execute_pipeline(
        pipe_code="extract_gantt_by_steps",
        working_memory=working_memory,
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
pretty_print(gantt_chart, title="Gantt Chart")
get_pipeline_tracker().output_flowchart()
