import asyncio

from pipelex import pretty_print
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline


async def summarize_by_steps(text: str):
    pipe_output = await execute_pipeline(
        pipe_code="summarize_by_steps",
        input_memory={
            "text": text,
        },
    )

    summary_text = pipe_output.main_stuff_as_text
    return summary_text


with open("assets/summarize/sample_text_3.txt", "r", encoding="utf-8") as f:
    text = f.read()

# start Pipelex
Pipelex.make()

# run sample using asyncio
summary_text = asyncio.run(summarize_by_steps(text))

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()
# output results
pretty_print(summary_text, title="Summarized by steps")

get_pipeline_tracker().output_flowchart()
