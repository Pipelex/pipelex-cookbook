import sys
from pathlib import Path

# Add script directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

import asyncio


from structures.discord_newsletter__discord_channel_update import DiscordChannelUpdate
from structures.discord_newsletter__html_newsletter import HtmlNewsletter

from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline


async def run_write_discord_newsletter() -> HtmlNewsletter:
    pipe_output = await execute_pipeline(
        pipe_code="write_discord_newsletter",
        inputs={
            "discord_channel_updates": {
            "concept": "discord_newsletter.DiscordChannelUpdate",
            "content": [DiscordChannelUpdate(name="name_value", position=0, messages=["DiscordMessage()"])],
        },
        },
    )
    return pipe_output.main_stuff_as(content_type=HtmlNewsletter)


if __name__ == "__main__":
    # Initialize Pipelex
    with Pipelex.make(library_dirs=["/Users/thomashebrardevotis/dev/pipelex/pipelex-cookbook/examples/wip/discord_newsletter"]):
        # Run the pipeline
        result = asyncio.run(run_write_discord_newsletter())
