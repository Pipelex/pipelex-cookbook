import asyncio

from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline


async def hello_world():
    """
    This function demonstrates the use of a super simple Pipelex pipeline to generate text.
    """
    # Run the pipe
    pipe_output = await execute_pipeline(
        pipe_code="hello_world",
    )

    # Print the output
    pretty_print(pipe_output, title="Your first Pipelex output")


# start Pipelex
Pipelex.make()
# run sample using asyncio
asyncio.run(hello_world())
