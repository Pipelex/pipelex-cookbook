import asyncio

from pipelex import pretty_print
from pipelex.client.protocol import CompactMemory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex.tools.misc.json_utils import load_json_list_from_path

DISCORD_EXTRACT_PATH = "assets/discord_newsletter/discord_extract.json"


async def write_discord_newsletter(discord_extract_path: str) -> str:
    discord_articles_data = load_json_list_from_path(discord_extract_path)

    discord_articles = [DiscordArticle.model_validate(article_data) for article_data in discord_articles_data]

    pipe_output = await execute_pipeline(
        pipe_code="write_discord_newsletter",
        input_memory={
            "discord_articles": discord_articles,
        },
    )
    # Output the result
    return pipe_output.main_stuff_as_str


# start Pipelex
Pipelex.make()

# run sample using asyncio
gantt_chart = asyncio.run(write_discord_newsletter(discord_extract_path=DISCORD_EXTRACT_PATH))

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()
# output results
pretty_print(gantt_chart, title="Gantt Chart")
get_pipeline_tracker().output_flowchart()
