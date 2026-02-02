import runpy
import subprocess

import pytest

from examples.wip.discord_newsletter import run_discord_newsletter


@pytest.mark.inference
@pytest.mark.dry_runnable
class TestWip:
    def test_write_tweet(self, pipelex_cmd: str):
        result = subprocess.run(
            [pipelex_cmd, "run", "examples/wip/write_tweet/tech_tweet.plx", "-i", "examples/wip/write_tweet/inputs.json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_advisory_board(self, pipelex_cmd: str):
        result = subprocess.run(
            [
                pipelex_cmd,
                "run",
                "examples/wip/advisory_board/bundle.plx",
                "-i",
                "examples/wip/advisory_board/inputs.json",
                "-L",
                "examples/wip/advisory_board",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_discord_newsletter(self):
        runpy.run_path(run_discord_newsletter.__file__, run_name="__main__")
