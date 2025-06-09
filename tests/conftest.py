from typing import Any

import pipelex.config
import pipelex.pipelex
import pytest
from pipelex import log, pretty_print
from pipelex.config import get_config
from pipelex.core.pipe_run_params import PipeRunMode
from pipelex.libraries.library_config import LibraryConfig
from pipelex.tools.runtime_manager import RunMode, runtime_manager
from pytest import FixtureRequest, Parser
from rich import print
from rich.console import Console
from rich.traceback import Traceback

pytest_plugins = [
    "pipelex.test_extras.shared_pytest_plugins",
]


@pytest.fixture(scope="module", autouse=True)
def reset_pipelex_config_fixture():
    # Code to run before each test
    print("\n[magenta]pipelex setup[/magenta]")
    try:
        pipelex_instance = pipelex.pipelex.Pipelex.make()
        config = get_config()
        pretty_print(config, title="Test config")
        assert isinstance(config, pipelex.config.PipelexConfig)
        assert config.project_name == "pipelex-cookbook"
    except Exception as exc:
        Console().print(Traceback())
        pytest.exit(f"Critical Pipelex setup error: {exc}")
    yield
    # Code to run after each test
    print("\n[magenta]pipelex teardown[/magenta]")
    pipelex_instance.teardown()


@pytest.fixture(scope="function", autouse=True)
def pretty():
    # Code to run before each test
    print("\n")
    yield
    # Code to run after each test
    print("\n")
