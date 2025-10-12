import pipelex.config
import pipelex.pipelex
import pytest
from pipelex.config import get_config
from rich import print
from rich.console import Console
from rich.traceback import Traceback

pytest_plugins = [
    "pipelex.test_extras.shared_pytest_plugins",
]


@pytest.fixture(scope="function", autouse=True)
def pretty():
    # Code to run before each test
    print("\n")
    yield
    # Code to run after each test
    print("\n")
