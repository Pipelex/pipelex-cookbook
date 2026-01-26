import subprocess

import pytest


@pytest.mark.inference
@pytest.mark.dry_runnable
class TestQuickStart:
    def test_hello_world(self):
        result = subprocess.run(
            ["pipelex", "run", "examples/a_quick_start/hello_world.plx"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_summarize_with_structure(self):
        result = subprocess.run(
            [
                "pipelex",
                "run",
                "examples/a_quick_start/summarize.plx",
                "--pipe",
                "summarize_with_structure",
                "-i",
                "examples/a_quick_start/inputs.json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_summarize_by_steps(self):
        result = subprocess.run(
            ["pipelex", "run", "examples/a_quick_start/summarize.plx", "--pipe", "summarize_by_steps", "-i", "examples/a_quick_start/inputs.json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"
