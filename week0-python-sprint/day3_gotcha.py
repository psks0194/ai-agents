"""Async traps. Knowing what NOT to do."""

import asyncio


async def get_data() -> str:
    await asyncio.sleep(0.5)
    return "hello"


async def trap1() -> None:
    # WRONG: forgot the await
    result = get_data()
    print(f"Trap 1 result: {result}")
    print(f"Trap 1 type: {type(result)}")


# asyncio.run(trap1())

import time


async def trap2() -> None:
    print("Trap 2: starting...")
    # WRONG: time.sleep is sync — it blocks the entire event loop
    time.sleep(2)
    print("Trap 2: done after 2 sync seconds")


# asyncio.run(trap2())

# WRONG in a .py file:
# result = await get_data()


async def trap4() -> None:
    print("This will never print")


# WRONG: just calling the function does nothing — no event loop is running
# trap4()

# RIGHT:
asyncio.run(trap4())
