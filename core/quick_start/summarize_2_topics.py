# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio

from pipelex import pretty_print
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_mission_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code


async def summarize_by_steps(text: str):
    # Load the working memory with the text
    working_memory = WorkingMemoryFactory.make_from_text(text=text)

    # Run the pipe
    pipe_output = await run_pipe_code(
        pipe_code="summarize_by_steps",
        working_memory=working_memory,
    )

    summary_text = pipe_output.main_stuff_as_text

    # Print the output
    pretty_print(summary_text, title="Summarized by steps")

    # Get the report (tokens used and cost)
    get_report_delegate().generate_report()
    get_mission_tracker().output_flowchart()


with open("assets/sample_text_1.txt", "r", encoding="utf-8") as f:
    text = f.read()

Pipelex.make()
asyncio.run(summarize_by_steps(text))
