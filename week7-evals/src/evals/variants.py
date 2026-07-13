"""Version-swappable drafting for A/B eval.

To compare prompt variants cleanly, we call the same model with the same inputs
and vary ONLY the system prompt. Isolating the single variable is the whole
point — otherwise you can't attribute a score change to the change you made.

These mirror the server's draft_thread logic so the comparison is honest; the
server itself stays untouched.
"""

from __future__ import annotations

import re

from anthropic import AsyncAnthropic

from evals.config import settings


# Variant A: the current server prompt (the baseline).
PROMPT_A = (
    "You write X threads as IntellAIgent: a practitioner-contrarian voice. "
    "Rules: concrete over abstract; NO hype words (unlock, leverage, "
    "revolutionize, seamless, game-changer); pick a defensible side; "
    "measure honestly including costs and failures; short punchy sentences. "
    "Each tweet must stand alone. Output EXACTLY one tweet per line, each "
    "line prefixed with its number and a slash, like '1/'. No other text."
)

# Variant B: a candidate change. Adds an explicit "open with a concrete number
# or specific claim" instruction — a plausible improvement worth testing.
PROMPT_B = (
    "You write X threads as IntellAIgent: a practitioner-contrarian voice. "
    "Rules: concrete over abstract; NO hype words (unlock, leverage, "
    "revolutionize, seamless, game-changer); pick a defensible side; "
    "measure honestly including costs and failures; short punchy sentences. "
    "OPEN the first tweet with a concrete number, measurement, or specific "
    "claim — never a generic setup line. Each tweet must stand alone. Output "
    "EXACTLY one tweet per line, each prefixed with its number and a slash, "
    "like '1/'. No other text."
)


async def draft_with_prompt(system_prompt: str, inputs: dict) -> list[str]:
    """Draft a thread using a given system prompt. Returns the list of tweets."""
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    user = (
        f"Source headline: {inputs['source_title']}\n"
        f"Source summary: {inputs['source_summary']}\n"
        f"Angle to build around: {inputs['angle']}\n"
        f"Write a {inputs['num_tweets']}-tweet thread."
    )
    resp = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1200,
        system=system_prompt,
        messages=[{"role": "user", "content": user}],
    )
    raw = resp.content[0].text.strip()
    tweets = [
        ln.strip()
        for ln in raw.splitlines()
        if ln.strip() and re.match(r"^\d+\s*/", ln.strip())
    ]
    return tweets or [ln.strip() for ln in raw.splitlines() if ln.strip()]
