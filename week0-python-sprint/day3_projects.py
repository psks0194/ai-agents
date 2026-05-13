"""
Fetch posts from JSONPlaceholder concurrently, validate with Pydantic,
print a summary. This is the shape of real agent code.
"""

import asyncio
import httpx
from pydantic import BaseModel, Field, ValidationError
import time 

class Post(BaseModel):
    userId: int
    id: int
    title: str
    body: str

async def fetch_post(client: httpx.AsyncClient, post_id: int) -> Post:
    """Fetch and validate a single post."""
    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    response = await client.get(url, timeout=5.0)
    response.raise_for_status()
    return Post.model_validate(response.json())

async def main() -> None:
    post_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    print(f"Fetching {len(post_ids)} posts concurrently...")
    start = time.perf_counter()

    async with httpx.AsyncClient(timeout=10.0) as client:
        posts = await asyncio.gather(
            *[fetch_post(client, pid) for pid in post_ids],
            return_exceptions=True,
        )

    elapsed = time.perf_counter() - start
    print(f"\nDone in {elapsed:.2f}s\n")

    # Process results
    successful = [p for p in posts if isinstance(p, Post)]
    failed = [p for p in posts if isinstance(p, Exception)]

    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}\n")

    print("Titles:")
    for post in successful:
        print(f"  [{post.id}] (user {post.userId}) {post.title}")


if __name__ == "__main__":
    asyncio.run(main())