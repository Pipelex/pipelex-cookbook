import sys
from pathlib import Path

# Add script directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

import asyncio

from pipelex.core.stuffs.text_content import TextContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from structures.summarize__structured_summary import StructuredSummary


async def run_summarize_with_structure() -> StructuredSummary:
    pipe_output = await execute_pipeline(
        pipe_code="summarize_with_structure",
        inputs={
            "text": {
                "concept": "native.Text",
                "content": TextContent(text="text_value"),
            },
        },
    )
    return pipe_output.main_stuff_as(content_type=StructuredSummary)


if __name__ == "__main__":
    # Initialize Pipelex
    with Pipelex.make(library_dirs=["/Users/thomashebrardevotis/dev/pipelex/pipelex-cookbook/examples/a_quick_start"]):
        # Run the pipeline
        result = asyncio.run(run_summarize_with_structure())
