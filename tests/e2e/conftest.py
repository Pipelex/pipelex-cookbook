import pipelex.config
import pipelex.pipelex
import pytest
from pipelex import pretty_print
from pipelex.config import get_config
from rich import print
from rich.console import Console
from rich.traceback import Traceback


@pytest.fixture(scope="function", autouse=True)
def reset_pipelex_instance_fixture():
    # Code to run before each test
    yield
    # Code to run after each test
    print("\n[magenta]pipelex instance teardown[/magenta]")
    pipelex.pipelex.Pipelex.get_instance().teardown()
