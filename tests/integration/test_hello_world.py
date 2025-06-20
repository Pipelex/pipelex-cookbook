import pytest
from pipelex.core.pipe_run_params import PipeRunMode
from pipelex.pipeline.execute import execute_pipeline


@pytest.mark.asyncio
@pytest.mark.inference
@pytest.mark.dry_runnable
async def test_hello_world(pipe_run_mode: PipeRunMode):
    """Test that the hello_world function runs successfully."""
    # Run the pipe
    pipe_output, _ = await execute_pipeline(
        pipe_code="hello_world",
        pipe_run_mode=pipe_run_mode,
    )

    assert pipe_output is not None
