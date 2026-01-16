"""
Chaining LLM Calls - Chain multiple LLM calls together

This runs a PipeSequence that:
1. Generates a story idea
2. Expands it into an outline
"""

import asyncio

from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

LIBRARY_DIRS = ["tutorial"]


async def main():
    pipe_output = await execute_pipeline(pipe_code="generate_and_expand")
    result = pipe_output.main_stuff_as_str

    pretty_print(result, title="Story Outline")


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        asyncio.run(main())
