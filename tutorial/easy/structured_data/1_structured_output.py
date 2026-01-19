"""
Structured Output - Get structured data from LLMs

This shows how to get a structured object (BookIdea) instead of plain text.
"""

import asyncio

from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

from tutorial.easy.structured_data.structured_objects_struct import BookIdea

LIBRARY_DIRS = ["tutorial"]


async def main():
    pipe_output = await execute_pipeline(pipe_code="struct_generate_book_idea")
    book_idea = pipe_output.main_stuff_as(content_type=BookIdea)

    pretty_print(f"Title: {book_idea.title}", title="Generated Book Idea")
    print(f"Genre: {book_idea.genre}")
    print(f"Synopsis: {book_idea.synopsis}")
    print(f"Target Audience: {book_idea.target_audience}")


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        asyncio.run(main())
