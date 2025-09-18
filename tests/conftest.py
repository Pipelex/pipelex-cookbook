import pytest
from rich import print

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
