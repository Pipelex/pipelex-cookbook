import pipelex.config
import pipelex.pipelex
import pytest
from pipelex.test_extras.shared_pytest_plugins import is_inference_disabled_in_pipelex
from rich import print
from rich.console import Console
from rich.traceback import Traceback


@pytest.fixture(scope="module", autouse=True)
def reset_pipelex_config_fixture(request: pytest.FixtureRequest):
    # Code to run before each test
    print("\n[magenta]pipelex setup[/magenta]")
    try:
        pipelex_instance = pipelex.pipelex.Pipelex.make(
            disable_inference=is_inference_disabled_in_pipelex(request),
        )
    except Exception as exc:
        Console().print(Traceback())
        pytest.exit(f"Critical Pipelex setup error: {exc}")
    yield
    # Code to run after each test
    print("\n[magenta]pipelex teardown[/magenta]")
    pipelex_instance.teardown()
