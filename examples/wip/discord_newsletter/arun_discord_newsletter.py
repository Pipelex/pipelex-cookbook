import asyncio
from typing import List

from pipelex import pretty_print
from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex.tools.misc.json_utils import load_json_list_from_path

from examples.wip.discord_newsletter.structures.discord_newsletter__discord_channel_update import DiscordChannelUpdate
from examples.wip.discord_newsletter.structures.discord_newsletter__html_newsletter import HtmlNewsletter
from utils.results_utils import output_result

SAMPLE_NAME = "discord_newsletter"
DISCORD_EXTRACT_PATH = "assets/discord_newsletter/discord_extract.json"


async def write_discord_newsletter() -> HtmlNewsletter:
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
    discord_channel_updates: List[DiscordChannelUpdate] = [
        DiscordChannelUpdate.model_validate(channel_data) for channel_data in discord_channel_updates_data
    ]

    # Run the pipeline with the typed input
    # The pipeline will receive a list of DiscordChannelUpdate objects
    pipe_output = await execute_pipeline(
        pipe_code="write_discord_newsletter",
        inputs={
            "discord_channel_updates": discord_channel_updates,
        },
    )

    return pipe_output.main_stuff_as(content_type=HtmlNewsletter)


if __name__ == "__main__":
    with Pipelex.make(library_dirs=["examples/wip/discord_newsletter"]):
        # Run sample using asyncio
        html_newsletter = asyncio.run(write_discord_newsletter())

        # Display cost report (tokens used and cost)
        get_report_delegate().generate_report()

        # Output results
        pretty_print(html_newsletter, title="Discord Newsletter")
        output_result(
            sample_name=SAMPLE_NAME,
            title="Discord Newsletter",
            file_name="discord_newsletter.html",
            content=html_newsletter.model_dump_json(),
        )
