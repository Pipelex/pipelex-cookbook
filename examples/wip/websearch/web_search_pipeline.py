import asyncio
from threading import Thread
from typing import Any, Dict, Optional

from pipelex.core.memory.working_memory import WorkingMemory
from .web_search import WebSearchQuery
from pipelex.tools.func_registry import func_registry
from websearch.web_search import search_web


def _run_coro_in_thread(coro) -> str:
    holder: Dict[str, Any] = {"value": None, "error": None}

    def _target():
        try:
            holder["value"] = asyncio.run(coro)
        except Exception as e:
            holder["error"] = e

    t = Thread(target=_target, daemon=True)
    t.start()
    t.join()
    if holder["error"] is not None:
        raise holder["error"]
    return holder["value"]


def perform_web_search(working_memory: WorkingMemory) -> str:
    # Expect a 'query' stuff of concept WebSearchQuery
    q = working_memory.get_stuff("query").content  # StructuredContent (WebSearchQuery)
    query_text: str = getattr(q, "query_text", "")
    search_type: str = getattr(q, "search_type", "search")
    num_results: int = getattr(q, "num_results", 3)
    api_key: Optional[str] = getattr(q, "api_key", None)

    if not query_text:
        return "Error: No query text provided"

    coro = search_web(
        query=query_text,
        search_type=search_type,
        num_results=num_results,
        api_key=api_key,
    )
    return _run_coro_in_thread(coro)


# Register under the fully-qualified name used in TOML
func_registry.register_function(perform_web_search, name="web_search_pipeline.perform_web_search")
