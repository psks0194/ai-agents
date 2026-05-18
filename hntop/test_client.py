"""Quick check: does fetching actually work?"""

import asyncio
from hntop.client import fetch_top_stories


async def main() -> None:
    """Fetch and print the top HN stories."""
    stories = await fetch_top_stories(count=5)
    for i, story in enumerate(stories, 1):
        print(f"{i}. {story.title} ({story.score})")


if __name__ == "__main__":
    asyncio.run(main())
