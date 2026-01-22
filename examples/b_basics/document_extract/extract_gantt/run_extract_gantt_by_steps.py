import sys
from pathlib import Path

# Add script directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

import asyncio


from structures.gantt__gantt_chart import GanttChart
from structures.gantt__gantt_chart_image import GanttChartImage

from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline


async def run_extract_gantt_by_steps() -> GanttChart:
    pipe_output = await execute_pipeline(
        pipe_code="extract_gantt_by_steps",
        inputs={
            "gantt_chart_image": {
            "concept": "gantt.GanttChartImage",
            "content": GanttChartImage(url="https://pipelex-web.s3.us-west-2.amazonaws.com/cookbook/gantt_tree_house.png"),
        },
        },
    )
    return pipe_output.main_stuff_as(content_type=GanttChart)


if __name__ == "__main__":
    # Initialize Pipelex
    with Pipelex.make(library_dirs=["/Users/thomashebrardevotis/dev/pipelex/pipelex-cookbook/examples/b_basics/document_extract/extract_gantt"]):
        # Run the pipeline
        result = asyncio.run(run_extract_gantt_by_steps())
