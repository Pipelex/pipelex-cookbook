import asyncio
from typing import Any, List

from pipelex import pretty_print
from pipelex.client.protocol import CompactMemory
from pipelex.core.stuff_factory import StuffFactory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex.tools.misc.json_utils import load_json_list_from_path

from pipelex_libraries.pipelines.examples.discord_newsletter.models import DiscordChannelUpdate

# DISCORD_EXTRACT_PATH = "assets/discord_newsletter/discord_extract.json"
DISCORD_EXTRACT_PATH = "assets/discord_newsletter/discord_sample.json"


async def write_discord_newsletter(discord_extract_path: str) -> Any:
    # Load channel update list in json format
    discord_channel_updates_data = load_json_list_from_path(discord_extract_path)
    # Make it a list of structured content
    discord_channel_updates: List[DiscordChannelUpdate] = [
        DiscordChannelUpdate.model_validate(article_data) for article_data in discord_channel_updates_data
    ]
    pipe_output = await execute_pipeline(
        pipe_code="write_discord_newsletter",
        input_memory={
            "discord_channel_updates": discord_channel_updates,
        },
    )

    # Output the result
    # return pipe_output.main_stuff_as_str
    return pipe_output.main_stuff


# start Pipelex
Pipelex.make()

# run sample using asyncio
newsletter = asyncio.run(write_discord_newsletter(discord_extract_path=DISCORD_EXTRACT_PATH))

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()
# output results
pretty_print(newsletter, title="Discord Newsletter")
get_pipeline_tracker().output_flowchart()
