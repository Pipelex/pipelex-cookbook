import asyncio
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import trafilatura
from dateutil import parser as dateparser
from limits import parse
from limits.aio.storage import MemoryStorage
from limits.aio.strategies import MovingWindowRateLimiter

from .analytics import last_n_days_avg_time_df, last_n_days_df, record_request

# Configuration
# Prefer environment variables; fall back to legacy hardcoded default if present.
# Secondary key can be provided via SERPER_API_KEY_FALLBACK, SERPER_SECONDARY_API_KEY or SERPER_API_KEY_2
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "xxxxx")
SERPER_API_KEY_FALLBACK = (
    os.getenv("SERPER_API_KEY_FALLBACK", "xxxxxx") or os.getenv("SERPER_SECONDARY_API_KEY") or os.getenv("SERPER_API_KEY_2") or ""
)
SERPER_SEARCH_ENDPOINT = "https://google.serper.dev/search"
SERPER_NEWS_ENDPOINT = "https://google.serper.dev/news"
SERPER_LOCATION = "France"
SERPER_GL = "fr"  # country
SERPER_HL = "fr"  # language


def _build_serper_headers(api_key: str) -> Dict[str, str]:
    return {"X-API-KEY": api_key, "Content-Type": "application/json"}


# Friendly browser-like headers for target site fetching to reduce 403s
REQUEST_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com",
}


def _robust_extract_main_text(html: str, url: str) -> str:
    """Attempt trafilatura.extract with helpful options, fallback to naive cleanup.

    Based on trafilatura core functions and options documented in the project docs
    (see: https://trafilatura.readthedocs.io/en/latest/corefunctions.html#extract)
    """
    if not isinstance(html, str) or not html.strip():
        return ""
    text: str = ""
    try:
        text = (
            trafilatura.extract(
                html,
                url=url or None,
                include_comments=False,
                include_formatting=False,
                favor_recall=True,
                include_links=False,
                include_tables=True,
            )
            or ""
        )
    except Exception:
        text = ""
    if text and text.strip():
        return text.strip()
    # Fallback: naive tag stripping
    try:
        import re

        text_only = re.sub(r"<[^>]+>", " ", html)
        text_only = re.sub(r"\s+", " ", text_only).strip()
        return text_only
    except Exception:
        return ""


# Rate limiting
storage = MemoryStorage()
limiter = MovingWindowRateLimiter(storage)
rate_limit = parse("360/hour")


async def search_web(
    query: str,
    search_type: str = "search",
    num_results: Optional[int] = 4,
    api_key: Optional[str] = None,
    fallback_api_key: Optional[str] = None,
    use_fallback: bool = True,
) -> str:
    """
    Search the web for information or fresh news, returning extracted content.

    This tool can perform two types of searches:
    - "search" (default): General web search for diverse, relevant content from various sources
    - "news": Specifically searches for fresh news articles and breaking stories

    Use "news" mode when looking for:
    - Breaking news or very recent events
    - Time-sensitive information
    - Current affairs and latest developments
    - Today's/this week's happenings

    Use "search" mode (default) for:
    - General information and research
    - Technical documentation or guides
    - Historical information
    - Diverse perspectives from various sources

    Args:
        query (str): The search query. This is REQUIRED. Examples: "apple inc earnings",
                    "climate change 2024", "AI developments"
        search_type (str): Type of search. This is OPTIONAL. Default is "search".
                          Options: "search" (general web search) or "news" (fresh news articles).
                          Use "news" for time-sensitive, breaking news content.
        num_results (int): Number of results to fetch. This is OPTIONAL. Default is 4.
                          Range: 1-20. More results = more context but longer response time.
        api_key (str, optional): Primary Serper API key to use for the request. If not
                           provided, falls back to environment variable SERPER_API_KEY.
        fallback_api_key (str, optional): Secondary Serper API key. Used automatically
                           when primary fails with auth/rate-limit. If not provided,
                           falls back to SERPER_API_KEY_FALLBACK / SERPER_SECONDARY_API_KEY / SERPER_API_KEY_2.
        use_fallback (bool): Whether to attempt the fallback key automatically on 401/403/429/402
                           or network errors. Default True.

    Returns:
        str: Formatted text containing extracted content with metadata (title,
             source, date, URL, and main text) for each result, separated by dividers.
             Returns error message if API key is missing or search fails.

    Examples:
        - search_web("OpenAI GPT-5", "news") - Get 5 fresh news articles about OpenAI
        - search_web("python tutorial", "search") - Get 4 general results about Python (default count)
        - search_web("stock market today", "news", 10) - Get 10 news articles about today's market
        - search_web("machine learning basics") - Get 4 general search results (all defaults)
    """
    start_time = time.time()

    # Prepare key order
    keys_in_order: List[str] = []
    if api_key:
        keys_in_order.append(api_key)
    elif SERPER_API_KEY:
        keys_in_order.append(SERPER_API_KEY)
    # Include fallback if requested
    fb_key = fallback_api_key if fallback_api_key else SERPER_API_KEY_FALLBACK
    if use_fallback and fb_key:
        # Avoid duplicate if same as primary
        if fb_key not in keys_in_order:
            keys_in_order.append(fb_key)

    if not keys_in_order:
        await record_request(0.0, num_results)  # Record even failed requests
        return (
            "Error: No SERPER API key configured. Provide api_key parameter or set "
            "SERPER_API_KEY. Optionally set SERPER_API_KEY_FALLBACK for automatic fallback."
        )

    # Validate and constrain num_results
    if num_results is None:
        num_results = 4
    num_results = max(1, min(20, num_results))

    # Validate search_type
    if search_type not in ["search", "news"]:
        search_type = "search"

    try:
        # Check rate limit
        if not await limiter.hit(rate_limit, "global"):
            print(f"[{datetime.now().isoformat()}] Rate limit exceeded")
            duration = time.time() - start_time
            await record_request(duration, num_results)
            return "Error: Rate limit exceeded. Please try again later (limit: 360 requests per hour)."

        # Select endpoint based on search type
        endpoint = SERPER_NEWS_ENDPOINT if search_type == "news" else SERPER_SEARCH_ENDPOINT

        # Prepare payload with FR location/language
        payload = {
            "q": query,
            "num": num_results,
            "location": SERPER_LOCATION,
            "gl": SERPER_GL,
            "hl": SERPER_HL,
        }
        if search_type == "news":
            payload["type"] = "news"
            payload["page"] = 1

        # Make request with primary, optionally fallback to secondary on auth/rate-limit errors
        resp = None
        last_error: Optional[str] = None
        fallback_statuses = {400, 401, 403, 429, 402, 500, 502, 503, 504}
        async with httpx.AsyncClient(timeout=15) as client:
            for idx, key in enumerate(keys_in_order):
                try:
                    current_headers = _build_serper_headers(key)
                    r = await client.post(endpoint, headers=current_headers, json=payload)
                    # Success
                    if r.status_code == 200:
                        resp = r
                        break
                    # Log fallback attempt
                    print(f"[{datetime.now().isoformat()}] API key {idx + 1} returned status {r.status_code} for query: '{query[:50]}...'")
                    # Decide whether to try next key
                    if not use_fallback or idx == len(keys_in_order) - 1:
                        resp = r
                        break
                    if r.status_code not in fallback_statuses:
                        # Do not fallback on unrelated errors like 404, 422
                        print(f"[{datetime.now().isoformat()}] Not falling back on status {r.status_code} (not in fallback list)")
                        resp = r
                        break
                    else:
                        print(f"[{datetime.now().isoformat()}] Falling back to next API key due to status {r.status_code}")
                except Exception as ex:
                    last_error = str(ex)
                    print(f"[{datetime.now().isoformat()}] Exception with API key {idx + 1}: {ex}")
                    if not use_fallback or idx == len(keys_in_order) - 1:
                        resp = None
                        break

        if not resp:
            duration = time.time() - start_time
            await record_request(duration, num_results)
            return f"Error: Search request failed. Details: {last_error or 'unknown error'}."

        if resp.status_code != 200:
            duration = time.time() - start_time
            await record_request(duration, num_results)
            return f"Error: Search API returned status {resp.status_code}. Please check your API key and try again."

        # Extract results based on search type
        if search_type == "news":
            results = resp.json().get("news", [])
        else:
            results = resp.json().get("organic", [])

        if not results:
            duration = time.time() - start_time
            await record_request(duration, num_results)
            return f"No {search_type} results found for query: '{query}'. Try a different search term or search type."

        # Fetch HTML content concurrently
        urls = [r["link"] for r in results]
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=REQUEST_HEADERS) as client:
            tasks = [client.get(u) for u in urls]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Extract and format content
        chunks = []
        successful_extractions = 0

        for meta, response in zip(results, responses):
            if isinstance(response, Exception):
                continue

            # Extract main text content with content-type gating and robust fallback
            content_type = ""
            try:
                content_type = (response.headers.get("Content-Type", "") or "").lower()
            except Exception:
                content_type = ""
            body = None
            try:
                looks_like_html = "text/html" in content_type or "<html" in response.text[:1000].lower()
                if looks_like_html:
                    body = _robust_extract_main_text(response.text, meta.get("link", ""))
            except Exception:
                body = None

            if not body:
                continue

            successful_extractions += 1
            print(f"[{datetime.now().isoformat()}] Successfully extracted content from {meta['link']}")

            # Format the chunk based on search type
            if search_type == "news":
                # News results have date and source
                try:
                    date_str = meta.get("date", "")
                    if date_str:
                        date_iso = dateparser.parse(date_str, fuzzy=True).strftime("%Y-%m-%d")
                    else:
                        date_iso = "Unknown"
                except Exception:
                    date_iso = "Unknown"

                chunk = (
                    f"## {meta['title']}\n"
                    f"**Source:** {meta.get('source', 'Unknown')}   "
                    f"**Date:** {date_iso}\n"
                    f"**URL:** {meta['link']}\n\n"
                    f"{body.strip()}\n"
                )
            else:
                # Search results don't have date/source but have domain
                domain = meta["link"].split("/")[2].replace("www.", "")

                chunk = f"## {meta['title']}\n**Domain:** {domain}\n**URL:** {meta['link']}\n\n{body.strip()}\n"

            chunks.append(chunk)

        if not chunks:
            duration = time.time() - start_time
            await record_request(duration, num_results)
            return f"Found {len(results)} {search_type} results for '{query}', but couldn't extract readable content from any of them. The websites might be blocking automated access."

        result = "\n---\n".join(chunks)
        summary = f"Successfully extracted content from {successful_extractions} out of {len(results)} {search_type} results for query: '{query}'\n\n---\n\n"

        print(f"[{datetime.now().isoformat()}] Extraction complete: {successful_extractions}/{len(results)} successful for query '{query}'")

        # Record successful request with duration
        duration = time.time() - start_time
        await record_request(duration, num_results)

        return summary + result

    except Exception as e:
        # Record failed request with duration
        duration = time.time() - start_time
        return f"Error occurred while searching: {str(e)}. Please try again or check your query."


async def search_web_structured(
    query: str,
    search_type: str = "search",
    num_results: Optional[int] = 4,
    include_html: bool = True,
    api_key: Optional[str] = None,
    fallback_api_key: Optional[str] = None,
    use_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Search the web and return structured results containing raw HTML and cleaned text.

    Args:
        query: Search query string
        search_type: "search" or "news"
        num_results: Number of results to fetch (1-20)
        include_html: Whether to include raw HTML in the response
        api_key: Primary Serper API key (overrides env if provided)
        fallback_api_key: Secondary Serper API key to try automatically on auth/rate-limit
        use_fallback: Whether to attempt fallback key on 401/403/429/402 or network errors

    Returns:
        Dict with keys: {"query", "search_type", "results", "summary", "serper_text_joined"}
        where results is a list of dicts each containing:
        - title, url, domain, date (if available)
        - raw_html (optional), cleaned_text (extracted main content)
        - serper_style_text (a Serper-style block used for chunking)
        - status_code, error (if any), fetched_at
    """
    start_time = time.time()

    results_out: List[Dict[str, Any]] = []

    # Quick validation
    fetch_num = max(1, min(20, num_results or 4))
    if search_type not in ["search", "news"]:
        search_type = "search"

    # Prepare key order
    keys_in_order: List[str] = []
    if api_key:
        keys_in_order.append(api_key)
    elif SERPER_API_KEY:
        keys_in_order.append(SERPER_API_KEY)
    fb_key = fallback_api_key if fallback_api_key else SERPER_API_KEY_FALLBACK
    if use_fallback and fb_key:
        if fb_key not in keys_in_order:
            keys_in_order.append(fb_key)

    try:
        # Check rate limit
        if not await limiter.hit(rate_limit, "global"):
            duration = time.time() - start_time
            await record_request(duration, fetch_num)
            return {
                "query": query,
                "search_type": search_type,
                "results": [],
                "summary": "Rate limit exceeded",
                "error": "rate_limit_exceeded",
            }

        # Choose endpoint
        endpoint = SERPER_NEWS_ENDPOINT if search_type == "news" else SERPER_SEARCH_ENDPOINT

        payload = {
            "q": query,
            "num": fetch_num,
            "location": SERPER_LOCATION,
            "gl": SERPER_GL,
            "hl": SERPER_HL,
        }
        if search_type == "news":
            payload["type"] = "news"
            payload["page"] = 1

        # Make request with primary, optionally fallback on auth/rate-limit errors
        resp = None
        last_error: Optional[str] = None
        fallback_statuses = {400, 401, 403, 429, 402, 500, 502, 503, 504}
        async with httpx.AsyncClient(timeout=15) as client:
            for idx, key in enumerate(keys_in_order):
                try:
                    current_headers = _build_serper_headers(key)
                    r = await client.post(endpoint, headers=current_headers, json=payload)
                    # Success
                    if r.status_code == 200:
                        resp = r
                        break
                    # Log fallback attempt
                    print(f"[{datetime.now().isoformat()}] API key {idx + 1} returned status {r.status_code} for query: '{query[:50]}...'")
                    # Decide whether to try next key
                    if not use_fallback or idx == len(keys_in_order) - 1:
                        resp = r
                        break
                    if r.status_code not in fallback_statuses:
                        print(f"[{datetime.now().isoformat()}] Not falling back on status {r.status_code} (not in fallback list)")
                        resp = r
                        break
                    else:
                        print(f"[{datetime.now().isoformat()}] Falling back to next API key due to status {r.status_code}")
                except Exception as ex:
                    last_error = str(ex)
                    print(f"[{datetime.now().isoformat()}] Exception with API key {idx + 1}: {ex}")
                    if not use_fallback or idx == len(keys_in_order) - 1:
                        resp = None
                        break

        if not resp:
            duration = time.time() - start_time
            await record_request(duration, fetch_num)
            return {
                "query": query,
                "search_type": search_type,
                "results": [],
                "summary": f"Request error: {last_error or 'unknown error'}",
                "error": "request_failed",
            }

        if resp.status_code != 200:
            duration = time.time() - start_time
            await record_request(duration, fetch_num)
            return {
                "query": query,
                "search_type": search_type,
                "results": [],
                "summary": f"Search API status {resp.status_code}",
                "error": f"api_status_{resp.status_code}",
            }

        # Parse SERPER results
        if search_type == "news":
            serper_items = resp.json().get("news", [])
        else:
            serper_items = resp.json().get("organic", [])

        if not serper_items:
            duration = time.time() - start_time
            await record_request(duration, fetch_num)
            return {
                "query": query,
                "search_type": search_type,
                "results": [],
                "summary": f"No {search_type} results for '{query}'",
                "error": "no_results",
            }

        # Fetch raw pages concurrently
        urls: List[str] = [it.get("link") for it in serper_items if it.get("link")]
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=REQUEST_HEADERS) as client:
            fetches = [client.get(u) for u in urls]
            responses = await asyncio.gather(*fetches, return_exceptions=True)

        successful_extractions = 0
        serper_blocks: List[str] = []
        for meta, response in zip(serper_items, responses):
            # Prepare base item
            item: Dict[str, Any] = {}
            item["title"] = meta.get("title", "")
            item["url"] = meta.get("link", "")
            item["domain"] = ""
            item["date"] = meta.get("date", "") if search_type == "news" else ""
            item["source"] = meta.get("source", "") if search_type == "news" else ""
            item["status_code"] = None
            item["fetched_at"] = datetime.now().isoformat()
            # Ensure web_text_for_chunking appears before cleaned_text in item order
            # Ensure web_text_for_chunking appears before cleaned_text
            item["web_text_for_chunking"] = ""
            item["cleaned_text"] = ""
            # Backward-compatible alias used elsewhere
            item["serper_style_text"] = ""
            try:
                if not isinstance(response, Exception):
                    item["status_code"] = response.status_code
                    # Domain
                    try:
                        item["domain"] = item["url"].split("/")[2].replace("www.", "") if item["url"] else ""
                    except Exception:
                        item["domain"] = ""

                    # Raw HTML (optional)
                    if include_html:
                        try:
                            item["raw_html"] = response.text
                        except Exception:
                            item["raw_html"] = ""

                    # Cleaned text (main content) with robust gating and fallback
                    cleaned = None
                    try:
                        content_type = (response.headers.get("Content-Type", "") or "").lower()
                    except Exception:
                        content_type = ""
                    try:
                        is_html = "text/html" in content_type or "<html" in (response.text[:1000].lower() if isinstance(response.text, str) else "")
                        if is_html:
                            cleaned = _robust_extract_main_text(response.text, item.get("url", ""))
                    except Exception:
                        cleaned = None
                    if not cleaned or not str(cleaned).strip():
                        # Fallback: naive HTML tag removal or raw text normalization
                        import re

                        try:
                            text_src = response.text if isinstance(response.text, str) else ""
                            text_only = re.sub(r"<[^>]+>", " ", text_src)
                            text_only = re.sub(r"\s+", " ", text_only).strip()
                        except Exception:
                            text_only = ""
                        cleaned = text_only
                    if cleaned:
                        cleaned = cleaned.strip()
                        item["cleaned_text"] = cleaned
                        successful_extractions += 1

                    # Build Serper-style block
                    serper_block = f"## {item['title']}\n**Domain:** {item['domain']}\n**URL:** {item['url']}\n\n{item['cleaned_text']}\n"
                    # Primary field used downstream by chunking scripts
                    item["web_text_for_chunking"] = serper_block
                    # Alias retained for compatibility
                    item["serper_style_text"] = serper_block
                    serper_blocks.append(serper_block)
                else:
                    item["error"] = str(response)
            except Exception as ex:
                item["error"] = str(ex)

            results_out.append(item)

        duration = time.time() - start_time
        await record_request(duration, fetch_num)

        summary = f"Fetched {len(results_out)} results; successfully extracted content from {successful_extractions}"
        return {
            "query": query,
            "search_type": search_type,
            "results": results_out,
            # Joined Serper-style text for direct chunking consumption
            "serper_text_joined": "\n---\n".join(serper_blocks) if serper_blocks else "",
            "summary": summary,
        }

    except Exception as e:
        duration = time.time() - start_time
        # Do not await record_request here since limiter/storage might be unavailable in error states
        return {
            "query": query,
            "search_type": search_type,
            "results": [],
            "summary": f"Error: {str(e)}",
            "error": "exception",
        }
