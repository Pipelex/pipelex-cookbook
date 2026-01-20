import asyncio

from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

LIBRARY_DIRS = ["tutorial"]


async def main():
    pipe_output = await execute_pipeline(pipe_code="compare_models")
    result = pipe_output.main_stuff_as_str

    pretty_print(result, title="Model Configuration Comparison")


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        asyncio.run(main())
