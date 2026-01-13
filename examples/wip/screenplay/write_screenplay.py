import asyncio

from pipelex import pretty_print
from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

SAMPLE_NAME = "write_screenplay"
PITCH = """
A screenplay about a young woman who discovers she has the ability to see ghosts.
"""


async def generate_screenplay(pitch: str):
    """Generate a screenplay from a pitch using the pipeline."""

    pipe_output = await execute_pipeline(
        pipe_code="generate_screenplay",
        inputs={
            "pitch": {
                "concept": "screenplay.Pitch",
                "content": pitch,
            }
        },
    )
    pretty_print(pipe_output, title="Pipe Output")


if __name__ == "__main__":
    with Pipelex.make():
        # Run the pipeline using asyncio
        screenplay = asyncio.run(generate_screenplay(pitch=PITCH))

        # Display cost report (tokens used and cost)
        get_report_delegate().generate_report()

        # Output results
        pretty_print(screenplay, title="Generated Screenplay")

        # Generate pipeline flowchart
