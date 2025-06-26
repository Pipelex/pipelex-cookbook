import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_factory import StuffFactory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline


async def generate_screenplay(pitch: str):
    """Generate a screenplay from a pitch using the pipeline."""

    # Create Stuff object for the pitch
    pitch_stuff = StuffFactory.make_from_str(
        str_value=pitch,
        concept_str="screenplay.Pitch",
        name="pitch",
    )

    # Create Working Memory
    working_memory = WorkingMemoryFactory.make_from_single_stuff(pitch_stuff)

    # Run the pipe
    pipe_output = await execute_pipeline(
        pipe_code="generate_screenplay",
        working_memory=working_memory,
    )
    pretty_print(pipe_output, title="Pipe Output")


# Start Pipelex
Pipelex.make()

pitch = """
A screenplay about a young woman who discovers she has the ability to see ghosts.
"""

# Run the pipeline using asyncio
screenplay = asyncio.run(generate_screenplay(pitch))

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()

# Output results
pretty_print(screenplay, title="Generated Screenplay")

# Generate pipeline flowchart
get_pipeline_tracker().output_flowchart()
