"""Async version: fetch 3 URLs concurrently and time it."""

import time
import asyncio
import httpx

URLS = [
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/3",
]


async def fetch_url(url: str) -> int:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        return response.status_code


async def main() -> None:
    start = time.perf_counter()

    tasks = [fetch_url(url) for url in URLS]
    statuses = await asyncio.gather(*tasks)

    for status in statuses:
        print(status)

    end = time.perf_counter()
    print(f"Async total time: {end - start:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
