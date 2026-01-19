import asyncio

from pipelex import pretty_print
from pipelex.core.stuffs.stuff import Stuff
from pipelex.hub import get_inference_manager
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.c_advanced.using_inference_plugins.llm_plugin_example_using_openai import LLMPluginExampleUsingOpenAI
from examples.constants import LIBRARY_DIRS
from utils.results_utils import output_result

SAMPLE_NAME = "hello_plugin"


async def hello_plugin() -> Stuff | None:
    """This function demonstrates the use of a super simple Pipelex pipeline to generate text."""
    # Run the pipe
    pipe_output = await execute_pipeline(
        pipe_code="hello_plugin",
    )

    # Print the output
    pretty_print(pipe_output, title="Pipelex output using an LLM Plugin")
    return pipe_output.main_stuff


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        # register external plugin
        get_inference_manager().set_llm_worker_from_external_plugin(
            llm_handle="llm_plugin_example_using_openai",
            llm_worker_class=LLMPluginExampleUsingOpenAI,
        )
        # run sample using asyncio
        result = asyncio.run(hello_plugin())
        if result is None:
            print("No result found")
        else:
            output_result(
                sample_name=SAMPLE_NAME,
                title="Hello Plugin",
                file_name="hello_plugin.json",
                content=result.content.rendered_json(),
            )
