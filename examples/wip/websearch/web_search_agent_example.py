import asyncio

from pipelex import pretty_print
from pipelex.hub import get_pipeline_tracker, get_report_delegate
from pipelex.libraries.pipelines.web_search import WebSearchAgentResponse
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline

SAMPLE_NAME = "web_search_agent"


async def run_web_search_agent(user_query: str) -> WebSearchAgentResponse:
    """
    Run the web search agent pipeline.

    Args:
        user_query: The user's question or query to search for

    Returns:
        WebSearchAgentResponse: Comprehensive response with search results
    """
    # Run the pipeline
    pipe_output = await execute_pipeline(
        pipe_code="web_search_agent",
        input_memory={
            "user_query": user_query,
        },
    )

    # Return the structured response
    return pipe_output.main_stuff_as(content_type=WebSearchAgentResponse)


def main():
    """Main function to demonstrate the web search agent."""
    # Initialize Pipelex
    Pipelex.make()

    # Example queries to test
    test_queries = [
        "What are the latest developments in artificial intelligence?",
        "How does climate change affect global weather patterns?",
        "What are the best practices for Python web development?",
    ]

    print("=== Web Search Agent Demo ===\n")

    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 50)

        try:
            # Run the web search agent
            response = asyncio.run(run_web_search_agent(query))

            # Display results
            pretty_print(response, title=f"Response to Query {i}")

        except Exception as e:
            print(f"Error processing query {i}: {e}")

        print("\n" + "=" * 80 + "\n")

    # Display cost report
    get_report_delegate().generate_report()

    # Output pipeline flowchart
    get_pipeline_tracker().output_flowchart()


if __name__ == "__main__":
    main()
