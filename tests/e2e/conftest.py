import os

import pipelex.pipelex
import pytest
from pipelex.pipe_run.pipe_run_params import FORCE_DRY_RUN_MODE_ENV_KEY, PipeRunMode
from rich import print


@pytest.fixture(scope="function", autouse=True)
def reset_pipelex_instance_fixture():
    # Code to run before each test
    yield
    # Code to run after each test
    print("\n[magenta]pipelex instance teardown[/magenta]")
    if pipelex_instance := pipelex.pipelex.Pipelex.get_optional_instance():
        pipelex_instance.teardown()


@pytest.fixture(scope="function", autouse=True)
def pipe_run_mode_env(pipe_run_mode: PipeRunMode):
    """Fixture to set and clean up the FORCE_DRY_RUN_MODE_ENV_KEY environment variable."""
    # Set the environment variable
    os.environ[FORCE_DRY_RUN_MODE_ENV_KEY] = pipe_run_mode.value
    yield
    # Clean up by removing the environment variable
    os.environ.pop(FORCE_DRY_RUN_MODE_ENV_KEY, None)
