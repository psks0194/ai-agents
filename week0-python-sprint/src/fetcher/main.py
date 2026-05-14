"""CLI entry point for the fetcher."""

import asyncio
import time

from fetcher.client import fetch_many
from fetcher.models import Post


async def run() -> None:
    post_ids = list(range(1, 11))  # 1 through 10

    print(f"Fetching {len(post_ids)} posts...")
    start = time.perf_counter()

    results = await fetch_many(post_ids)

    elapsed = time.perf_counter() - start
    print(f"Done in {elapsed:.2f}s\n")

    successful = [r for r in results if isinstance(r, Post)]
    failed = [r for r in results if isinstance(r, Exception)]

    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}\n")

    for post in successful[:5]:  # show first 5
        print(f"  [{post.id}] {post.title}")


def main() -> None:
    """Entry point for the `fetcher` command."""
    asyncio.run(run())


if __name__ == "__main__":
    main()