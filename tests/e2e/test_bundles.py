import importlib.util
import subprocess
from pathlib import Path

import pytest
from _pytest.mark import ParameterSet
from pipelex.system.environment import get_optional_env

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"

# Bundles without a main_pipe — list the pipe(s) to dry-run individually.
PIPES_OVERRIDES: dict[str, list[str]] = {
    "examples/a_quick_start/summarize.mthds": ["summarize_with_structure", "summarize_by_steps"],
}

# Extra CLI args by bundle path (e.g. -L for local libraries).
EXTRA_ARGS: dict[str, list[str]] = {}

# Bundles that must run without inputs, even though their folder holds an inputs.json meant for a
# sibling bundle (a_quick_start ships both hello_world, which declares no inputs, and summarize,
# which the inputs.json belongs to). Passing a pipe an input it does not declare is an error, so
# the folder-level lookup below would break these — this is also exactly how the READMEs run them.
NO_INPUTS: set[str] = {
    "examples/a_quick_start/hello_world.mthds",
}

# Folders excluded from auto-discovery (relative to repo root).
EXCLUDED_DIRS = ("examples/wip",)

# Bundles requiring an LLM provider key (skipped when key is missing).
NEEDS_OPENAI_KEY: set[str] = set()

# Bundles requiring an installed inference-backend plugin (skipped when the package is absent).
NEEDS_PLUGIN: dict[str, str] = {
    "examples/c_advanced/using_inference_plugins/hello_plugin.mthds": "hello_inference_plugin",
}

# Bundles tagged gha_disabled (skipped on GitHub Actions).
GHA_DISABLED: set[str] = set()


def _discover_test_cases() -> list[ParameterSet]:
    cases: list[ParameterSet] = []
    for mthds_path in sorted(EXAMPLES_DIR.rglob("*.mthds")):
        rel_path = mthds_path.relative_to(REPO_ROOT).as_posix()
        if any(rel_path.startswith(f"{excluded}/") for excluded in EXCLUDED_DIRS):
            continue
        pipes = PIPES_OVERRIDES.get(rel_path, [""])
        marks = [pytest.mark.gha_disabled] if rel_path in GHA_DISABLED else []
        for pipe in pipes:
            test_id = f"{rel_path}::{pipe}" if pipe else rel_path
            cases.append(pytest.param(rel_path, pipe, id=test_id, marks=marks))
    return cases


@pytest.mark.inference
@pytest.mark.dry_runnable
class TestBundles:
    @pytest.mark.parametrize(("bundle_path", "pipe"), _discover_test_cases())
    def test_dry_run(self, pipelex_cmd: str, bundle_path: str, pipe: str):
        if bundle_path in NEEDS_OPENAI_KEY and not get_optional_env("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY is not set")

        required_plugin = NEEDS_PLUGIN.get(bundle_path)
        if required_plugin and importlib.util.find_spec(required_plugin) is None:
            pytest.skip(f"plugin package '{required_plugin}' is not installed")

        cmd = [pipelex_cmd, "run", "bundle", bundle_path]

        if pipe:
            cmd.extend(["--pipe", pipe])

        inputs_rel = Path(bundle_path).parent / "inputs.json"
        if bundle_path not in NO_INPUTS and (REPO_ROOT / inputs_rel).is_file():
            cmd.extend(["-i", inputs_rel.as_posix()])

        cmd.extend(EXTRA_ARGS.get(bundle_path, []))

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        assert result.returncode == 0, f"Command failed for {bundle_path}: {result.stderr}"
