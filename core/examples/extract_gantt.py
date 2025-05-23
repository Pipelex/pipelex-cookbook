# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio

from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

from pipelex_libraries.pipelines.examples.extraction.gantt import GanttChart
from utils.results_utils import output_result

SAMPLE_NAME = "extract_gantt"


async def extract_gantt(image_url: str):
    # Create Working Memory
    working_memory = WorkingMemoryFactory.make_from_image(
        image_url=image_url,
        concept_code="gantt.GanttImage",
        name="gantt_chart_image",
    )

    # Run the pipe
    pipe_output = await run_pipe_code(
        pipe_code="extract_gantt_by_steps",
        working_memory=working_memory,
    )

    # Output the result
    gantt_chart = pipe_output.main_stuff_as(content_type=GanttChart)
    output_result(
        sample_name=SAMPLE_NAME,
        title="Gantt Chart",
        file_name="gantt_chart.json",
        content=gantt_chart.rendered_json(),
    )
    output_result(
        sample_name=SAMPLE_NAME,
        title="Gantt Chart",
        file_name="gantt_chart.md",
        content=gantt_chart.rendered_markdown(),
    )


IMAGE_URL = "assets/gantt/gantt_tree_house.png"
Pipelex.make()
asyncio.run(extract_gantt(IMAGE_URL))
