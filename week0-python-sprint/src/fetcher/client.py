"""HTTP client functions for fetching posts."""

import asyncio
import httpx

from fetcher.models import Post


BASE_URL = "https://jsonplaceholder.typicode.com"


async def fetch_post(client: httpx.AsyncClient, post_id: int) -> Post:
    """Fetch a single post by ID and validate as a Post."""
    response = await client.get(f"{BASE_URL}/posts/{post_id}")
    response.raise_for_status()
    return Post.model_validate(response.json())


async def fetch_many(post_ids: list[int]) -> list[Post | Exception]:
    """Fetch multiple posts concurrently. Returns successes and failures."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        results = await asyncio.gather(
            *[fetch_post(client, pid) for pid in post_ids],
            return_exceptions=True,
        )
    return results