import asyncio
from pathlib import Path
from typing import List

from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.runner import PipelexMTHDSProtocol
from pipelex.tools.misc.json_utils import load_json_list_from_path

from examples.wip.discord_newsletter.structures.discord_newsletter__discord_channel_update import discord_newsletter__DiscordChannelUpdate
from examples.wip.discord_newsletter.structures.discord_newsletter__html_newsletter import discord_newsletter__HtmlNewsletter
from utils.results_utils import output_result

SAMPLE_NAME = "discord_newsletter"
DISCORD_EXTRACT_PATH = Path("assets/discord_newsletter/discord_extract.json")


async def write_discord_newsletter() -> discord_newsletter__HtmlNewsletter:
    """
    Generate a newsletter from Discord channel data.

    This function demonstrates the pattern of:
    1. Loading an arbitrary JSON file (not a pipelex inputs.json)
    2. Converting it to a list of StructuredContent objects
    3. Passing those objects as typed input to the pipeline
    """
    # Load channel update list in json format
    discord_channel_updates_data = load_json_list_from_path(DISCORD_EXTRACT_PATH)

    # Make it a list of structured content by validating against our models
    # This converts raw JSON dicts into typed Pydantic objects
    discord_channel_updates: List[discord_newsletter__DiscordChannelUpdate] = [
        discord_newsletter__DiscordChannelUpdate.model_validate(channel_data) for channel_data in discord_channel_updates_data
    ]

    # Run the pipeline with the typed input
    # The pipeline will receive a list of discord_newsletter__DiscordChannelUpdate objects
    runner = PipelexMTHDSProtocol()
    response = await runner.execute(
        pipe_code="write_discord_newsletter",
        inputs={
            "discord_channel_updates": discord_channel_updates,
        },
    )
    pipe_output = response.pipe_output

    return pipe_output.main_stuff_as(content_type=discord_newsletter__HtmlNewsletter)


if __name__ == "__main__":
    with Pipelex.make(library_dirs=["examples/wip/discord_newsletter"]):
        # Run sample using asyncio
        html_newsletter = asyncio.run(write_discord_newsletter())

        # Output results
        pretty_print(html_newsletter, title="Discord Newsletter")
        output_result(
            sample_name=SAMPLE_NAME,
            title="Discord Newsletter",
            file_name="discord_newsletter.html",
            content=html_newsletter.model_dump_json(),
        )
