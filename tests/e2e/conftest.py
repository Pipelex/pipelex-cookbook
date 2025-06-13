import pipelex.config
import pipelex.pipelex
import pytest
from rich import print


@pytest.fixture(scope="function", autouse=True)
def reset_pipelex_instance_fixture():
    # Code to run before each test
    yield
    # Code to run after each test
    print("\n[magenta]pipelex instance teardown[/magenta]")
    pipelex.pipelex.Pipelex.get_instance().teardown()
