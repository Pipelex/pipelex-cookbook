import runpy

import pytest

from examples.wip.advisory_board import advisory_board
from examples.wip.discord_newsletter import discord_newsletter
from examples.wip.write_tweet import write_tweet


@pytest.mark.inference
@pytest.mark.dry_runnable
class TestWip:
    def test_write_tweet(self):
        runpy.run_path(write_tweet.__file__, run_name="__main__")

    def test_advisory_board(self):
        runpy.run_path(advisory_board.__file__, run_name="__main__")

    def test_discord_newsletter(self):
        runpy.run_path(discord_newsletter.__file__, run_name="__main__")
