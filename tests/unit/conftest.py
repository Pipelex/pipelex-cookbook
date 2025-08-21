import pipelex.config
import pipelex.pipelex
import pytest
from pipelex import pretty_print
from pipelex.config import get_config
from rich import print
from rich.console import Console
from rich.traceback import Traceback


@pytest.fixture(scope="module", autouse=True)
def reset_pipelex_config_fixture():
    # Code to run before each test
    print("\n[magenta]pipelex setup[/magenta]")
    pipelex_instance: pipelex.pipelex.Pipelex
    try:
        try:
            pipelex_instance = pipelex.pipelex.Pipelex.get_instance()
            pipelex_instance.teardown()
        except Exception as e:
            pipelex_instance = pipelex.pipelex.Pipelex.make(relative_config_folder_path="../../pipelex_libraries", from_file=True)
            print(f"Error getting instance: {e}")

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
