import asyncio

from pipelex import pretty_print
from pipelex.hub import get_inference_manager, get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from examples.using_inference_plugins.llm_plugin_example_using_openai import LLMPluginExampleUsingOpenAI


async def hello_plugin():
    """
    This function demonstrates the use of a super simple Pipelex pipeline to generate text.
    """
    # Run the pipe
    pipe_output = await execute_pipeline(
        pipe_code="hello_plugin",
    )

    # Print the output
    pretty_print(pipe_output, title="Pipelex output using an LLM Plugin")


# start Pipelex
Pipelex.make()
# register external plugin
get_inference_manager().set_llm_worker_from_external_plugin(
    llm_handle="llm_plugin_example_using_openai",
    llm_worker_class=LLMPluginExampleUsingOpenAI,
)
# run sample using asyncio
asyncio.run(hello_plugin())

# Display cost report (tokens used and cost)
# TODO: costs are currently not handled for external plugins
get_report_delegate().generate_report()
