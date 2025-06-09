import pytest
from pipelex import pretty_print
from pipelex.core.pipe_run_params import PipeRunMode
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipeline.execute import execute_pipeline
from pipelex.tools.misc.file_utils import load_text_from_path


@pytest.fixture(scope="class")
def file_path():
    return "assets/sample_text_3.txt"


@pytest.mark.inference
@pytest.mark.llm
@pytest.mark.asyncio(loop_scope="class")
class TestSummarize:
    async def test_summarize_by_steps(
        self,
        pipe_run_mode: PipeRunMode,
        file_path: str,
    ):
        text = load_text_from_path(file_path)
        # Load the working memory with the text
        working_memory = WorkingMemoryFactory.make_from_text(text=text)

        # Run the pipe
        pipe_output, _ = await execute_pipeline(
            pipe_code="test_summarize_by_steps",
            working_memory=working_memory,
            pipe_run_mode=pipe_run_mode,
        )

        summary_text = pipe_output.main_stuff_as_text
        # Display cost report (tokens used and cost)
        get_report_delegate().generate_report()
        # output results
        pretty_print(summary_text, title="Summarized by steps")

        get_pipeline_tracker().output_flowchart()
        return summary_text
