# ==============================================================================
# SerpAPI Service - Google Search Results
# ==============================================================================

from typing import Optional

import httpx

from ..types import SerpResult

_api_key: Optional[str] = None


def init_serpapi(api_key: str) -> None:
    """Initialize the SerpAPI service with API key."""
    global _api_key
    _api_key = api_key


def _get_api_key() -> str:
    """Get the API key (raises if not initialized)."""
    if _api_key is None:
        raise RuntimeError("SerpAPI not initialized. Call init_serpapi(api_key) first.")
    return _api_key


async def execute_search(query: str, num_results: int = 10) -> list[SerpResult]:
    """Execute a Google search using SerpAPI."""
    api_key = _get_api_key()

    params = {
        "api_key": api_key,
        "q": query,
        "engine": "google",
        "num": str(min(num_results, 100)),
    }

    async with httpx.AsyncClient() as client:
        response = await client.get("https://serpapi.com/search.json", params=params)
        data = response.json()

    if "error" in data:
        raise RuntimeError(f"SerpAPI Error: {data['error']}")

    organic_results = data.get("organic_results", [])

    return [
        SerpResult(
            title=item.get("title", ""),
            link=item.get("link", ""),
            snippet=item.get("snippet", ""),
            position=item.get("position", 0),
        )
        for item in organic_results
    ]


async def execute_multi_platform_search(
    dorks: dict[str, str],
    results_per_platform: int = 10,
) -> dict[str, list[SerpResult]]:
    """Execute multiple searches for different platforms."""
    import asyncio

    results: dict[str, list[SerpResult]] = {}

    for platform, dork in dorks.items():
        if dork:
            try:
                results[platform] = await execute_search(dork, results_per_platform)
                # Add delay to avoid rate limiting
                await asyncio.sleep(0.2)
            except Exception as e:
                print(f"Search failed for {platform}: {e}")
                results[platform] = []

    return results
