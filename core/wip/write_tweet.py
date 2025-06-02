# ruff: noqa: E501
import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_content import TextContent
from pipelex.core.stuff_factory import StuffFactory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code
from pipelex.tools.environment import get_optional_env
from pipelex.tools.misc.file_utils import load_text_from_path

from pipelex_libraries.pipelines.examples.tech_tweet import OptimizedTweet
from utils.input_utils import optional_sample_text_from_path

SAMPLE_NAME = "write_tweet"


async def optimize_tweet(draft_tweet_str: str, writing_style_str: str) -> OptimizedTweet:
    # Create the draft tweet stuff
    draft_tweet = StuffFactory.make_stuff(
        concept_code="tech_tweet.DraftTweet",
        content=TextContent(text=draft_tweet_str),
        name="draft_tweet",
    )
    writing_style = StuffFactory.make_stuff(
        concept_code="tech_tweet.WritingStyle",
        content=TextContent(text=writing_style_str),
        name="writing_style",
    )

    # Create working memory
    working_memory = WorkingMemoryFactory.make_from_multiple_stuffs(
        [
            draft_tweet,
            writing_style,
        ]
    )

    # Run the sequence pipe
    pipe_output = await run_pipe_code(
        pipe_code="optimize_tweet_sequence",
        working_memory=working_memory,
    )

    # Get the optimized tweet
    optimized_tweet = pipe_output.main_stuff_as(content_type=OptimizedTweet)
    return optimized_tweet


# start Pipelex
Pipelex.make()


# get sample data
SAMPLE_DRAFT_TWEET = """
We're seeing a revolution in game AI with LLMs enabling NPCs to have dynamic, contextual conversations. Our tests show that players engage 3x longer with AI-driven characters vs traditional scripted ones. The key is fine-tuning models on game-specific dialogue while maintaining character consistency.
"""
draft_tweet = optional_sample_text_from_path(filename="draft_tweet.md") or SAMPLE_DRAFT_TWEET

SAMPLE_WRITING_STYLE = """
🚀 Just shipped v2.0 of our API!

• 50% faster response times
• Better error messages
• Full OpenAPI docs

Try it out and let me know what you think! #DevTools
"""
writing_style = optional_sample_text_from_path(filename="writing_style.md") or SAMPLE_WRITING_STYLE


# run sample using asyncio
optimized_tweet = asyncio.run(
    optimize_tweet(
        draft_tweet_str=draft_tweet,
        writing_style_str=writing_style,
    )
)

# output results
print(optimized_tweet.text)
pretty_print(optimized_tweet.text, title="Optimized Tweet")
