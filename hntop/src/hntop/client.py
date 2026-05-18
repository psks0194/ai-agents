"""HTTP client for the Hacker News API."""

import asyncio
import httpx

from hntop.models import Story

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


async def fetch_top_story_ids(client: httpx.AsyncClient, limit: int = 50) -> list[int]:
    """Fetch the top story IDs from the HN API."""
    url = f"{HN_API_BASE}/topstories.json"
    res = await client.get(url)
    res.raise_for_status()
    return res.json()[:limit]


async def fetch_story_by_id(client: httpx.AsyncClient, story_id: int) -> Story:
    """Fetch a story by its ID."""
    url = f"{HN_API_BASE}/item/{story_id}.json"
    res = await client.get(url)
    res.raise_for_status()
    return Story.model_validate(res.json())


async def fetch_stories(ids: list[int], timeout: float = 10.0) -> list[Story]:
    """Fetch multiple stories concurrently."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [fetch_story_by_id(client, story_id) for story_id in ids]
        return await asyncio.gather(*tasks, return_exceptions=True)


async def fetch_top_stories(count: int = 50, timeout: float = 10.0) -> list[Story]:
    """Fetch the top HN stories."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        ids = await fetch_top_story_ids(client, limit=count)

    results = await fetch_stories(ids, timeout=timeout)
    return [s for s in results if isinstance(s, Story)]
