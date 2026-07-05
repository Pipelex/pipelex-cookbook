import subprocess
from pathlib import Path

import pytest
from _pytest.mark import ParameterSet

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Roots whose every .mthds bundle is release-gated by static validation: the tutorials and the
# examples. `pipelex validate --all` only checks the configured library pipelines, so without
# this gate a breaking MTHDS language change sails through green here and only fails in a
# reader's terminal.
VALIDATED_ROOTS = ("tutorial", "examples")

# Folders excluded from the gate, keyed by repo-relative prefix, each with the reason it is
# skipped. Excluded bundles are still discovered and reported as SKIP (with this reason) so an
# exclusion never silently reads as "everything passes".
EXCLUDED_DIRS: dict[str, str] = {
    "examples/wip": (
        "work-in-progress: advisory_board is a multi-file bundle and validate_expense_data is a "
        "PipeFunc bundle whose Python functions are only registered at runtime, so neither is "
        "statically validatable in this gate"
    ),
}


def _exclusion_reason(rel_path: str) -> str | None:
    for excluded_prefix, reason in EXCLUDED_DIRS.items():
        if rel_path.startswith(f"{excluded_prefix}/"):
            return reason
    return None


def _discover_bundles() -> list[ParameterSet]:
    cases: list[ParameterSet] = []
    for root in VALIDATED_ROOTS:
        root_dir = REPO_ROOT / root
        if not root_dir.is_dir():
            continue
        for mthds_path in sorted(root_dir.rglob("*.mthds")):
            rel_path = mthds_path.relative_to(REPO_ROOT).as_posix()
            reason = _exclusion_reason(rel_path)
            marks = [pytest.mark.skip(reason=reason)] if reason else []
            cases.append(pytest.param(rel_path, id=rel_path, marks=marks))
    return cases


class TestValidateBundles:
    """Static-validate every shipped .mthds bundle so a breaking MTHDS language change fails
    loudly in CI instead of in a reader's terminal.

    `pipelex validate bundle` runs both blueprint validation and an internal dry run, so this
    catches authoring-time breaks (e.g. an invalid PipeParallel output) and runtime-shape breaks
    (e.g. a composite whose fields cannot hold the branch outputs) without any inputs or LLM keys.
    It makes no inference calls, which is why this gate is deliberately not marked `inference` and
    therefore runs in CI's `make gha-tests` (which excludes inference tests — the sibling dry-run
    suite in test_bundles.py is marked `inference` and so does not gate CI).

    A multi-file bundle can cross-reference concepts across sibling files, so each bundle is
    validated with `-L <its parent dir>` to resolve those references.
    """

    @pytest.mark.parametrize("bundle_path", _discover_bundles())
    def test_validate(self, pipelex_cmd: str, bundle_path: str):
        library_dir = Path(bundle_path).parent.as_posix()
        cmd = [pipelex_cmd, "validate", "bundle", bundle_path, "-L", library_dir]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        assert result.returncode == 0, f"Validation failed for {bundle_path}:\n{result.stdout}\n{result.stderr}"
