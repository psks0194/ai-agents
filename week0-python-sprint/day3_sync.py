"""Sync version: fetch 3 URLs sequentially and time it."""

import time
import httpx

URLS = [
    "https://httpbin.org/delay/1",
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/3",
]


def fetch_url(url: str) -> int:
    response = httpx.get(url, timeout=10.0)
    return response.status_code


def main() -> None:
    start = time.perf_counter()
    for url in URLS:
        status_code = fetch_url(url)
        print(status_code)
    end = time.perf_counter()
    print(f"Sync total time: {end - start:.2f}s")


if __name__ == "__main__":
    main()
