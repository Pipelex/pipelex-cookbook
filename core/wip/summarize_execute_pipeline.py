import asyncio

from pipelex import pretty_print
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline


async def summarize_execute_pipeline(text: str) -> str:
    # Load the working memory with the text
    working_memory = WorkingMemoryFactory.make_from_text(text=text)

    # Run the pipe
    pipe_output, pipeline_run_id = await execute_pipeline(
        pipe_code="summarize_by_steps",
        working_memory=working_memory,
    )

    summary_text = pipe_output.main_stuff_as_str

    pretty_print(pipeline_run_id, title="Pipeline run id")

    # Get the report (tokens used and cost)
    get_report_delegate().generate_report(pipeline_run_id=pipeline_run_id)
    return summary_text


with open("assets/sample_text_3.txt", "r", encoding="utf-8") as f:
    text = f.read()


# start Pipelex
Pipelex.make()
# run sample using asyncio
summary_text = asyncio.run(summarize_execute_pipeline(text))

# Print the output
pretty_print(summary_text, title="Summarized by steps")
