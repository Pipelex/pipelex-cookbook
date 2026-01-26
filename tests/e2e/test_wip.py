import subprocess

import pytest


@pytest.mark.inference
@pytest.mark.dry_runnable
class TestWip:
    def test_write_tweet(self):
        result = subprocess.run(
            ["pipelex", "run", "examples/wip/write_tweet/tech_tweet.plx"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_advisory_board(self):
        result = subprocess.run(
            [
                "pipelex",
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
        result = subprocess.run(
            ["pipelex", "run", "examples/wip/discord_newsletter/bundle.plx", "-i", "examples/wip/discord_newsletter/inputs.json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"
