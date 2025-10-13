import asyncio

from pipelex import pretty_print
from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from quick_start.pipelines.summarize_struct import StructuredSummary


async def summarize_with_structure(text: str) -> StructuredSummary:
    pipe_output = await execute_pipeline(
        pipe_code="summarize_with_structure",
        input_memory={
            "text": text,
        },
    )

    summary = pipe_output.main_stuff_as(content_type=StructuredSummary)
    return summary


with open("assets/summarize/sample_text_1.txt", "r", encoding="utf-8") as f:
    text = f.read()

# start Pipelex
Pipelex.make()

# run sample using asyncio
summary = asyncio.run(summarize_with_structure(text))

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()

# output results
pretty_print(summary, title="Structured summary")
