from datetime import datetime
from typing import List, Optional

from pydantic import Field

from pipelex.core.stuffs.stuff_content import StructuredContent


class WebSearchQuery(StructuredContent):
    """A web search query with configuration"""

    query_text: str = Field(description="The search query to perform")
    search_type: str = Field(default="search", description="Type of search: 'search' or 'news'")
    num_results: int = Field(default=3, description="Number of results to fetch (1-20)")
    api_key: Optional[str] = Field(None, description="Optional API key override")


class WebSearchResult(StructuredContent):
    """A single web search result"""

    title: str = Field(description="Title of the webpage")
    url: str = Field(description="URL of the webpage")
    domain: str = Field(description="Domain of the webpage")
    content: str = Field(description="Extracted main content from the webpage")
    date: Optional[str] = Field(None, description="Publication date if available")
    source: Optional[str] = Field(None, description="Source name if available")


class WebSearchResponse(StructuredContent):
    """Response from web search with results and analysis"""

    query: str = Field(description="Original search query")
    search_type: str = Field(description="Type of search performed")
    results: List[WebSearchResult] = Field(default_factory=list, description="List of search results")
    summary: str = Field(description="Summary of search results")
    generated_response: str = Field(description="LLM-generated response incorporating search results")
    search_timestamp: datetime = Field(default_factory=datetime.now, description="When the search was performed")


class WebSearchAgentResponse(StructuredContent):
    """Final response from the web search agent"""

    user_query: str = Field(description="Original user query")
    search_results_summary: str = Field(description="Summary of web search findings")
    comprehensive_answer: str = Field(description="Comprehensive answer incorporating web search results")
    sources: List[str] = Field(default_factory=list, description="List of source URLs used")
    confidence_level: str = Field(description="Confidence level in the answer: 'high', 'medium', or 'low'")
