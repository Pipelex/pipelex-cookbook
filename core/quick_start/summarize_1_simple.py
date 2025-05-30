import asyncio

from pipelex import pretty_print
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

from pipelex_libraries.pipelines.quick_start.summarize import StructuredSummary


async def summarize_with_structure(text: str) -> StructuredSummary:
    # Load the working memory with the text
    working_memory = WorkingMemoryFactory.make_from_text(text=text)

    # Run the pipe
    pipe_output = await run_pipe_code(
        pipe_code="summarize_with_structure",
        working_memory=working_memory,
    )

    summary = pipe_output.main_stuff_as(content_type=StructuredSummary)
    return summary


with open("assets/sample_text_1.txt", "r", encoding="utf-8") as f:
    text = f.read()

# start Pipelex
Pipelex.make()
# run sample using asyncio
summary = asyncio.run(summarize_with_structure(text))

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()

# output results
pretty_print(summary, title="Structured summary")
