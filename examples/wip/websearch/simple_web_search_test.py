import asyncio

from pipelex import pretty_print
from pipelex.libraries.pipelines.web_search import WebSearchAgentResponse
from pipelex.pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline


async def test_web_search_agent():
    """Simple test of the web search agent pipeline."""
    # Initialize Pipelex
    Pipelex.make()

    # Test query
    test_query = "What is the current weather in Paris?"

    print(f"Testing web search agent with query: {test_query}")
    print("-" * 60)

    try:
        # Run the pipeline
        pipe_output = await execute_pipeline(
            pipe_code="web_search_agent",
            input_memory={
                "user_query": test_query,
            },
        )

        # Get the structured response
        response = pipe_output.main_stuff_as(content_type=WebSearchAgentResponse)

        # Display results
        print("✅ Pipeline executed successfully!")
        print(f"User Query: {response.user_query}")
        print(f"Confidence Level: {response.confidence_level}")
        print(f"Number of Sources: {len(response.sources)}")
        print(f"Answer Length: {len(response.comprehensive_answer)} characters")

        # Show a preview of the answer
        answer_preview = response.comprehensive_answer[:200] + "..." if len(response.comprehensive_answer) > 200 else response.comprehensive_answer
        print(f"Answer Preview: {answer_preview}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_web_search_agent())
    if success:
        print("\n🎉 Web search agent test completed successfully!")
    else:
        print("\n💥 Web search agent test failed!")
