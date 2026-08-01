import pytest
from pipelex.pipeline.runner import PipelexMTHDSProtocol
from pipelex.system.pipe_run_mode import PipeRunMode


@pytest.mark.asyncio
@pytest.mark.inference
@pytest.mark.dry_runnable
async def test_hello_world(pipe_run_mode: PipeRunMode):
    """Test that the hello_world function runs successfully."""
    # Run the pipe
    runner = PipelexMTHDSProtocol(pipe_run_mode=pipe_run_mode)
    response = await runner.execute(
        pipe_code="hello_world",
    )
    pipe_output = response.pipe_output

    assert pipe_output is not None
