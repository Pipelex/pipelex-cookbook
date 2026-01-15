import asyncio

from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.constants import LIBRARY_DIRS


async def hello_world():
    """
    This function demonstrates the use of a super simple Pipelex pipeline to generate text.
    """
    # Run the pipe
    pipe_output = await execute_pipeline(
        pipe_code="hello_world",
    )

    # Print the output
    haiku = pipe_output.main_stuff_as_str
    pretty_print(haiku, title="Your first Pipelex output: a haiku about Hello World")


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        # run sample using asyncio
        asyncio.run(hello_world())
