# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio

from pipelex import pretty_print
from pipelex.hub import get_report_delegate
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

    # Get the report (tokens used and cost)
    get_report_delegate().generate_report()


Pipelex.make()
asyncio.run(hello_world())
