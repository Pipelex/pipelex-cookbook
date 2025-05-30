import asyncio

from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code


async def hello_world():
    """
    This function demonstrates the use of a super simple Pipelex pipeline to generate text.
    """
    # Run the pipe
    pipe_output = await run_pipe_code(
        pipe_code="hello_world",
    )

    # Print the output
    pretty_print(pipe_output, title="Your first Pipelex output")


# start Pipelex
Pipelex.make()
# run sample using asyncio
asyncio.run(hello_world())
