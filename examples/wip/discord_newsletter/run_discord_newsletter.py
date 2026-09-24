import asyncio
from pathlib import Path

from pipelex import pretty_print
from pipelex.core.stuffs.text_content import TextContent
from pipelex.pipelex import Pipelex
from pipelex.pipeline.runner import PipelexMTHDSProtocol
from pipelex.tools.misc.json_utils import load_json_list_from_path

from utils.results_utils import output_result

SAMPLE_NAME = "discord_newsletter"
METHOD_DIR = Path("methods/discord_newsletter")
DISCORD_EXTRACT_PATH = Path("assets/discord_newsletter/discord_extract.json")


async def write_discord_newsletter() -> TextContent:
    """
    Generate a newsletter from Discord channel data.

    This function demonstrates the pattern of:
    1. Loading an arbitrary JSON file (not a pipelex inputs.json)
    2. Passing its items as the content of an input that names their concept
    3. Letting the runtime validate each item against the concept's structure, declared in the bundle
    """
    # Load channel update list in json format
    discord_channel_updates_data = load_json_list_from_path(DISCORD_EXTRACT_PATH)

    # Run the pipeline with the raw JSON dicts, named as DiscordChannelUpdate items:
    # the runtime validates each one against the structure the bundle declares for that concept
    runner = PipelexMTHDSProtocol()
    response = await runner.execute(
        pipe_code="write_discord_newsletter",
        inputs={
            "discord_channel_updates": {
                "concept": "discord_newsletter.DiscordChannelUpdate",
                "content": discord_channel_updates_data,
            },
        },
    )
    pipe_output = response.pipe_output

    return pipe_output.main_stuff_as_text


if __name__ == "__main__":
    with Pipelex.make(library_dirs=[str(METHOD_DIR)]):
        # Run sample using asyncio
        html_newsletter = asyncio.run(write_discord_newsletter())

        # Output results
        pretty_print(html_newsletter, title="Discord Newsletter")
        output_result(
            sample_name=SAMPLE_NAME,
            title="Discord Newsletter",
            file_name="discord_newsletter.html",
            content=html_newsletter.text,
        )
