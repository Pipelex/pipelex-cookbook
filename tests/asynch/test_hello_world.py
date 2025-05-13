# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import pytest
from pipelex.run import run_pipe_code


@pytest.mark.asyncio
@pytest.mark.llm
@pytest.mark.inference
async def test_hello_world():
    """Test that the hello_world function runs successfully."""
    # Run the pipe
    pipe_output = await run_pipe_code(
        pipe_code="hello_world",
    )

    assert pipe_output is not None
