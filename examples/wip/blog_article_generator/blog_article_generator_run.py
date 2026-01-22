import asyncio

from pipelex import pretty_print
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex.hub import get_report_delegate

from examples.constants import LIBRARY_DIRS
from utils.results_utils import output_result

from examples.wip.blog_article_generator.blog_article_struct import UserPrompt, BlogArticle

SAMPLE_NAME = "blog_article_generator"


async def run_blog_generator():
    print("\n📝 BLOG ARTICLE GENERATOR\n")

    topic = input("Enter blog topic: ")
    audience = input("Target audience: ")
    tone = input("Tone (professional/casual): ")
    length = input("Length (Short/Medium/Long): ")

    user_prompt = UserPrompt(topic=topic, audience=audience, tone=tone, length=length)

    pipe_output = await execute_pipeline(
        pipe_code="generate_blog_article",
        inputs={"user_prompt": user_prompt},
    )

    # Get structured output correctly
    blog: BlogArticle = pipe_output.working_memory.get_stuff_as(name="article", content_type=BlogArticle)

    pretty_print(blog, title="Generated Blog Article")

    # Save output
    output_result(
        sample_name=SAMPLE_NAME,
        title="Blog Article",
        file_name="blog.md",
        content=blog.content,
    )

    # Show cost report
    get_report_delegate().generate_report()


if __name__ == "__main__":
    with Pipelex.make(library_dirs=LIBRARY_DIRS):
        asyncio.run(run_blog_generator())
