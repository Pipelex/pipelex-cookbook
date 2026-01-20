"""
Using Object Fields - Access specific fields from structured objects

This pipeline:
1. Generates a BookIdea (with title, genre, synopsis, target_audience)
2. Uses only the title and genre to write a marketing pitch
"""

import asyncio

from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

LIBRARY_DIRS = ["tutorial"]


async def main():
    pipe_output = await execute_pipeline(pipe_code="generate_and_pitch")
    result = pipe_output.main_stuff_as_str

    pretty_print(result, title="Marketing Pitch")


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        asyncio.run(main())
