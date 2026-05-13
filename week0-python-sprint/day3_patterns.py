"""Common async patterns you'll use constantly."""

import asyncio
import time


# A pretend "slow operation" that simulates an API call
async def slow_operation(name: str, seconds: float) -> str:
    print(f"  [{time.perf_counter():.2f}] {name} starting...")
    await asyncio.sleep(seconds)
    print(f"  [{time.perf_counter():.2f}] {name} done")
    return f"result of {name}"


async def pattern_sequential() -> None:
    """Each await blocks the next — total time = sum of all."""
    print("\n--- Pattern 1: Sequential ---")
    start = time.perf_counter()

    a = await slow_operation("A", 1.0)
    b = await slow_operation("B", 1.0)
    c = await slow_operation("C", 1.0)

    elapsed = time.perf_counter() - start
    print(f"Sequential elapsed: {elapsed:.2f}s")

# asyncio.run(pattern_sequential())

async def pattern_gather() -> None:
    """gather runs concurrently — total time = the slowest one."""
    print("\n--- Pattern 2: gather ---")
    start = time.perf_counter()

    results = await asyncio.gather(
        slow_operation("A", 1.0),
        slow_operation("B", 2.0),
        slow_operation("C", 1.5),
    )

    elapsed = time.perf_counter() - start
    print(f"Results: {results}")
    print(f"Gather elapsed: {elapsed:.2f}s")

# asyncio.run(pattern_gather())

async def pattern_as_completed() -> None:
    """Process results in the order they finish, not the order they started."""
    print("\n--- Pattern 3: as_completed ---")
    start = time.perf_counter()

    tasks = [
        slow_operation("A", 2.0),
        slow_operation("B", 1.0),
        slow_operation("C", 1.5),
    ]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        print(f"  First-finished-next: {result}")

    elapsed = time.perf_counter() - start
    print(f"as_completed elapsed: {elapsed:.2f}s")

# asyncio.run(pattern_as_completed())

async def maybe_fail(name: str, should_fail: bool) -> str:
    await asyncio.sleep(0.5)
    if should_fail:
        raise ValueError(f"{name} failed!")
    return f"{name} succeeded"


async def pattern_gather_with_errors() -> None:
    """gather with return_exceptions=True keeps successes even if some fail."""
    print("\n--- Pattern 4: gather with errors ---")

    results = await asyncio.gather(
        maybe_fail("A", should_fail=False),
        maybe_fail("B", should_fail=True),
        maybe_fail("C", should_fail=False),
        return_exceptions=True,
    )

    for r in results:
        if isinstance(r, Exception):
            print(f"  ❌ Error: {type(r).__name__}: {r}")
        else:
            print(f"  ✅ {r}")

# asyncio.run(pattern_gather_with_errors())

async def main() -> None:
    await pattern_sequential()
    await pattern_gather()
    await pattern_as_completed()
    await pattern_gather_with_errors()


if __name__ == "__main__":
    asyncio.run(main())
