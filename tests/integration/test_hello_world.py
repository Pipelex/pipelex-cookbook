import pytest
from pipelex.pipeline.execute import execute_pipeline


@pytest.mark.asyncio
@pytest.mark.inference
async def test_hello_world():
    """Test that the hello_world function runs successfully."""
    # Run the pipe
    pipe_output, _ = await execute_pipeline(
        pipe_code="hello_world",
    )

    assert pipe_output is not None
