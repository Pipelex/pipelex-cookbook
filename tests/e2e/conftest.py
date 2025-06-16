import os

import pipelex.config
import pipelex.pipelex
import pytest
from pipelex.core.pipe_run_params import FORCE_DRY_RUN_MODE_ENV_KEY, PipeRunMode
from rich import print


@pytest.fixture(scope="function", autouse=True)
def reset_pipelex_instance_fixture():
    # Code to run before each test
    yield
    # Code to run after each test
    print("\n[magenta]pipelex instance teardown[/magenta]")
    pipelex.pipelex.Pipelex.get_instance().teardown()


@pytest.fixture(scope="function", autouse=True)
def pipe_run_mode_env(pipe_run_mode: PipeRunMode):
    """Fixture to set and clean up the FORCE_DRY_RUN_MODE_ENV_KEY environment variable."""
    # Set the environment variable
    os.environ[FORCE_DRY_RUN_MODE_ENV_KEY] = pipe_run_mode.value
    yield
    # Clean up by removing the environment variable
    os.environ.pop(FORCE_DRY_RUN_MODE_ENV_KEY, None)
