# The smoke check: every method validates on production, runs once on its sample and returns output of the shape its contract declares.
#
# It spends inference credit, so it runs only under `make check-smoke`, which sets COOKBOOK_SMOKE=1 and selects the `smoke` marker that `addopts`
# deselects everywhere else. Without COOKBOOK_SMOKE=1 it reads no file and skips. It needs nothing per method: every package the cookbook loads is
# run on its own `inputs.json` and held to its own `contract.json`. COOKBOOK_SMOKE_METHOD narrows it to the methods it names, and
# COOKBOOK_SMOKE_ROUTE=address runs each page's address at its tag instead of the package's files.

import os
from pathlib import Path

import pytest

from scripts.cookbook import Cookbook, load_cookbook
from scripts.exceptions import CookbookError
from scripts.hosted import (
    AddressState,
    HostedClient,
    HostedRun,
    RunRoute,
    check_address,
    client_from_env,
    run_address,
    run_package,
    validate_package,
)
from scripts.shape import shape_problems

REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_ENV = "COOKBOOK_SMOKE"
METHOD_ENV = "COOKBOOK_SMOKE_METHOD"
ROUTE_ENV = "COOKBOOK_SMOKE_ROUTE"
# The one test id the check has when it is not enabled, so that a `pytest -m smoke` without COOKBOOK_SMOKE=1 reads no file and says why it skips.
DISABLED = "disabled"


def _enabled() -> bool:
    return os.environ.get(SMOKE_ENV) == "1"


def _selected_names(cookbook: Cookbook) -> list[str]:
    """The methods COOKBOOK_SMOKE_METHOD names, separated by commas or spaces, or every method when it names none."""
    names = [package.name for package in cookbook.packages]
    wanted = os.environ.get(METHOD_ENV, "").replace(",", " ").split()
    unknown = sorted(set(wanted) - set(names))
    if unknown:
        pytest.fail(f"{METHOD_ENV} names no method under methods/: {', '.join(unknown)}. The methods are {', '.join(names)}", pytrace=False)
    return [name for name in names if name in wanted] if wanted else names


def _route() -> RunRoute:
    raw = os.environ.get(ROUTE_ENV, "").strip() or RunRoute.FILES
    try:
        return RunRoute(raw)
    except ValueError:
        pytest.fail(f"{ROUTE_ENV}={raw} names no route: it is `files`, the default, or `address`", pytrace=False)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "method_name" in metafunc.fixturenames:
        names = _selected_names(load_cookbook(REPO_ROOT)) if _enabled() else [DISABLED]
        metafunc.parametrize("method_name", names, ids=names)


def _run(*, client: HostedClient, cookbook: Cookbook, method_name: str, route: RunRoute) -> HostedRun:
    """Validate the method on production by the route asked for, then run it once on its sample: the run spends credit."""
    [package] = [package for package in cookbook.packages if package.name == method_name]
    match route:
        case RunRoute.FILES:
            verdict = validate_package(client=client, package=package)
            if not verdict.is_valid:
                pytest.fail(f"{method_name} is not valid on production:\n{verdict.report}", pytrace=False)
            return run_package(client=client, cookbook=cookbook, package=package)
        case RunRoute.ADDRESS:
            address_verdict = check_address(client=client, cookbook=cookbook, package=package)
            match address_verdict.state:
                case AddressState.UNRELEASED:
                    pytest.skip(f"{address_verdict.address} is not released yet: {address_verdict.report}")
                case AddressState.FAILED:
                    pytest.fail(f"{address_verdict.address} does not validate on production:\n{address_verdict.report}", pytrace=False)
                case AddressState.VALID:
                    return run_address(client=client, cookbook=cookbook, address=address_verdict.address, inputs=package.inputs)


@pytest.mark.smoke
class TestSmoke:
    def test_the_method_runs_on_its_sample_and_returns_output_of_its_contract_shape(self, method_name: str):
        if not _enabled():
            pytest.skip(f"the smoke check spends inference credit, so it runs only under `make check-smoke`, which sets {SMOKE_ENV}=1")
        cookbook = load_cookbook(REPO_ROOT)
        contract = next(package.contract for package in cookbook.packages if package.name == method_name)
        if contract is None:
            pytest.fail(f"{method_name} has no contract.json to hold its output to: run `make refresh` first", pytrace=False)
        try:
            run = _run(client=client_from_env(), cookbook=cookbook, method_name=method_name, route=_route())
        except CookbookError as exc:
            pytest.fail(f"{method_name}: {exc}", pytrace=False)
        print(f"\n· {method_name}: {run.summary()}")
        problems = shape_problems(contract=contract, output=run.main_stuff)
        assert not problems, f"the output of {method_name}, from run {run.run_id}, is not of its contract's shape:\n" + "\n".join(
            f"- {problem}" for problem in problems
        )
