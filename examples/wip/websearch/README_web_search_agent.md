# Web Search Agent Pipeline

This pipeline creates an intelligent web search agent that performs web searches and generates comprehensive responses incorporating the top 3 search results.

## Overview

The web search agent pipeline consists of several components:

1. **Query Optimization**: Converts user questions into effective web search queries
2. **Web Search**: Performs actual web searches using the Serper API
3. **Result Parsing**: Extracts and structures information from search results
4. **Response Generation**: Creates comprehensive answers incorporating search findings

## Pipeline Structure

### Concepts

- `WebSearchQuery`: A web search query with configuration (query text, search type, number of results)
- `WebSearchResult`: A single web search result with title, URL, domain, and content
- `WebSearchResponse`: Response from web search with results and analysis
- `WebSearchAgentResponse`: Final response from the web search agent

### Pipes

- `create_search_query`: Converts user questions into optimized search queries
- `perform_web_search`: Executes web searches using the web_search module
- `parse_search_results`: Parses and structures web search results
- `generate_agent_response`: Creates comprehensive responses incorporating search results
- `web_search_agent`: Complete pipeline sequence

## Usage

### Basic Usage

```python
import asyncio
from pipelex import Pipelex
from pipelex.pipeline.execute import execute_pipeline
from pipelex.libraries.pipelines.web_search import WebSearchAgentResponse

# Initialize Pipelex
Pipelex.make()

async def search_and_answer(query: str):
    # Run the web search agent
    pipe_output = await execute_pipeline(
        pipe_code="web_search_agent",
        input_memory={
            "user_query": query,
        },
    )
    
    # Get the structured response
    response = pipe_output.main_stuff_as(content_type=WebSearchAgentResponse)
    return response

# Example usage
query = "What are the latest developments in artificial intelligence?"
response = asyncio.run(search_and_answer(query))

print(f"Query: {response.user_query}")
print(f"Answer: {response.comprehensive_answer}")
print(f"Sources: {response.sources}")
print(f"Confidence: {response.confidence_level}")
```

### Running the Examples

1. **Simple Test**: Run `python examples/simple_web_search_test.py` for a basic test
2. **Full Demo**: Run `python examples/web_search_agent_example.py` for multiple example queries

## Configuration

### Environment Setup

1. Copy the environment example file:
```bash
cp env.example .env
```

2. Edit the `.env` file and add your API keys:
```bash
# Required for web search functionality
SERPER_API_KEY=your_primary_serper_api_key_here
SERPER_API_KEY_FALLBACK=your_fallback_serper_api_key_here

# Required for LLM operations (choose one or more)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
```

### API Keys

The pipeline uses the Serper API for web searches. Configure your API keys:

```bash
export SERPER_API_KEY="your_primary_api_key"
export SERPER_API_KEY_FALLBACK="your_fallback_api_key"  # Optional
```

### Search Parameters

- **Search Type**: "search" (general) or "news" (fresh news)
- **Number of Results**: 1-20 (default: 3 for top results)
- **Location**: France (configurable in web_search.py)

## Features

- **Intelligent Query Optimization**: Automatically converts questions into effective search queries
- **Top 3 Results**: Focuses on the most relevant results for concise answers
- **Structured Output**: Returns well-organized responses with sources and confidence levels
- **Error Handling**: Graceful handling of API failures and rate limits
- **Source Attribution**: Always cites sources used in the response

## Output Structure

The `WebSearchAgentResponse` contains:

- `user_query`: Original user question
- `search_results_summary`: Summary of web search findings
- `comprehensive_answer`: Detailed answer incorporating search results
- `sources`: List of source URLs used
- `confidence_level`: Assessment of answer confidence ("high", "medium", "low")

## Error Handling

The pipeline handles various error scenarios:

- Missing API keys
- Rate limiting
- Network failures
- Invalid queries
- Empty search results

## Dependencies

### Core Dependencies
- `pipelex`: Core pipeline framework
- `httpx`: HTTP client for web requests
- `trafilatura`: HTML content extraction
- `python-dateutil`: Date parsing
- `limits`: Rate limiting
- `gradio`: Web interface (optional)

### Installation

The web search dependencies are automatically included when you install Pipelex. If you need to install them manually:

```bash
# Using uv (recommended)
uv add trafilatura python-dateutil limits gradio

# Using pip
pip install trafilatura python-dateutil limits gradio
```

## Rate Limits

The web search module includes rate limiting (360 requests per hour) to respect API limits and prevent abuse.

