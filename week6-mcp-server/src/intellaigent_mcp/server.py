"""IntellAIgent content-ops MCP server.

Exposes the IntellAIgent content pipeline as MCP tools, resources, and prompts
so any MCP client (Claude Code, Claude Desktop) can drive it. Day 1: the first
tool — fetch and parse a feed into LLM-friendly items.

Run locally:      uv run fastmcp run src/intellaigent_mcp/server.py
Dev + Inspector:  uv run fastmcp dev inspector src/intellaigent_mcp/server.py
Install into CC:  uv run fastmcp install claude-code src/intellaigent_mcp/server.py
"""

from dataclasses import dataclass

import feedparser
import httpx
import re
from fastmcp import FastMCP, Context
from typing import Literal
from fastmcp.exceptions import ToolError
from intellaigent_mcp.models import (
    CardSpec,
    CardPalette,
    VoiceReport,
    VoiceIssue,
    ThreadDraft,
)
from anthropic import AsyncAnthropic
from intellaigent_mcp.config import settings

# The server object. `fastmcp install` auto-discovers an object named
# mcp, server, or app — so naming it `mcp` keeps install frictionless.
mcp = FastMCP("IntellAIgent_Content_Ops")


@dataclass
class FeedItem:
    """One parsed feed entry, trimmed to what's useful for ideation."""

    title: str
    summary: str
    link: str
    published: str


@mcp.tool
def fetch_feed(feed_url: str, limit: int = 8) -> list[dict]:
    """Fetch an RSS/Atom feed and return recent items as structured data.

    Use this to pull source material for content ideation — for example a
    TLDR newsletter feed. Returns the most recent items with title, summary,
    link, and publish date.

    Args:
        feed_url: The full URL of an RSS or Atom feed.
        limit: Maximum number of items to return (default 8, max 25).
    """
    limit = max(1, min(limit, 25))

    # Fetch with an explicit UA — some feeds 403 a missing/blank agent.
    resp = httpx.get(
        feed_url,
        headers={"User-Agent": "intellaigent-content-ops/0.1"},
        timeout=15.0,
        follow_redirects=True,
    )
    resp.raise_for_status()

    parsed = feedparser.parse(resp.content)
    if parsed.bozo and not parsed.entries:
        raise ValueError(
            f"Could not parse a valid feed at {feed_url}. "
            f"Check the URL points to an RSS/Atom feed."
        )

    items: list[FeedItem] = []
    for entry in parsed.entries[:limit]:
        items.append(
            FeedItem(
                title=entry.get("title", "").strip(),
                summary=entry.get("summary", "").strip()[:500],
                link=entry.get("link", "").strip(),
                published=entry.get("published", entry.get("updated", "")).strip(),
            )
        )

    # Return plain dicts — FastMCP serializes these to JSON for the client.
    return [item.__dict__ for item in items]


@mcp.tool
def generate_card_spec(
    headline: str,
    subtitle: str,
    accent: Literal["cyan", "magenta", "amber"] = "cyan",
    eyebrow: str = "Dispatch",
) -> CardSpec:
    """Generate a structured 1600x900 IntellAIgent card spec for rendering.

    Produces a complete, brand-consistent card specification that the
    Playwright/Chromium renderer can turn into a PNG. Use this whenever you
    need a branded visual for a post — it resolves the IntellAIgent palette,
    grid, and footer so every card is consistent.

    Args:
        headline: The main card headline. Keep it tight — under ~10 words.
        subtitle: One supporting line under the headline.
        accent: Which brand accent to feature — cyan, magenta, or amber.
        eyebrow: Small uppercase label top-left (default 'Dispatch').
    """
    palette = CardPalette()
    accent_map = {
        "cyan": palette.cyan,
        "magenta": palette.magenta,
        "amber": palette.amber,
    }

    # Guard the headline length — long headlines break the 1600x900 layout.
    if len(headline) > 90:
        raise ToolError(
            f"Headline is {len(headline)} chars; keep it under 90 so it fits "
            f"the card layout. Tighten it and try again."
        )

    return CardSpec(
        eyebrow=eyebrow.upper(),
        headline=headline.strip(),
        subtitle=subtitle.strip(),
        accent_hex=accent_map[accent],
        palette=palette,
    )


# The voice rules, encoded. These mirror the IntellAIgent voice constraints:
# concrete over abstract, no hype, pick a side, measure honestly.
_HYPE_WORDS = {
    "unlock",
    "leverage",
    "revolutionize",
    "revolutionary",
    "game-changer",
    "game-changing",
    "seamless",
    "seamlessly",
    "cutting-edge",
    "supercharge",
    "elevate",
    "paradigm",
    "synergy",
    "disruptive",
    "delve",
    "unleash",
    "transformative",
    "next-level",
    "best-in-class",
}
_HEDGES = {
    "i think",
    "i guess",
    "sort of",
    "kind of",
    "maybe just",
    "arguably",
    "it could be argued",
    "in my humble opinion",
    "just my two cents",
}
_INTENSIFIERS = {"very", "really", "truly", "deeply", "incredibly", "extremely"}


@mcp.tool
def check_voice(text: str) -> VoiceReport:
    """Lint text against the IntellAIgent voice rules and return violations.

    Flags hype words (unlock, leverage, revolutionize...), hedging phrases,
    and empty intensifiers (very, really, truly...). Use this on any draft
    post or thread before shipping to keep the practitioner-contrarian voice:
    concrete over abstract, no hype, measured claims.

    Args:
        text: The draft text to check.
    """
    if not text.strip():
        raise ToolError("No text provided to check.")

    lowered = text.lower()
    issues: list[VoiceIssue] = []

    for word in sorted(_HYPE_WORDS):
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            issues.append(
                VoiceIssue(
                    kind="hype_word",
                    term=word,
                    suggestion=f"Cut '{word}' — say concretely what happens instead.",
                )
            )

    for phrase in sorted(_HEDGES):
        if phrase in lowered:
            issues.append(
                VoiceIssue(
                    kind="hedge",
                    term=phrase,
                    suggestion=f"Drop '{phrase}' — state the claim directly or don't.",
                )
            )

    for word in sorted(_INTENSIFIERS):
        if re.search(rf"\b{word}\b", lowered):
            issues.append(
                VoiceIssue(
                    kind="intensifier",
                    term=word,
                    suggestion=f"'{word}' adds no information — cut it or use a number.",
                )
            )

    passed = len(issues) == 0
    note = (
        "Clean — no voice violations found."
        if passed
        else f"Found {len(issues)} issue(s). Tighten before shipping."
    )

    return VoiceReport(
        passed=passed,
        issue_count=len(issues),
        issues=issues,
        note=note,
    )


@mcp.tool
async def draft_thread(
    source_title: str,
    source_summary: str,
    angle: str,
    num_tweets: int = 6,
    ctx: Context = None,
) -> ThreadDraft:
    """Draft an X thread in the IntellAIgent voice from source material.

    Takes a source item (e.g. a headline + summary from fetch_feed) and a
    chosen angle, and drafts a thread in the practitioner-contrarian voice:
    concrete over abstract, no hype words, picks a defensible side, measures
    honestly. Use after selecting an angle from feed material.

    Args:
        source_title: Headline of the source item.
        source_summary: Short summary of the source.
        angle: The specific angle to build the thread around.
        num_tweets: How many tweets in the thread (3-10, default 6).
    """
    num_tweets = max(3, min(num_tweets, 10))

    if not settings.anthropic_api_key:
        raise ToolError(
            "ANTHROPIC_API_KEY is not configured for this server. "
            "Set it in the server's .env and reinstall."
        )

    if ctx:
        await ctx.info(f"Drafting a {num_tweets}-tweet thread on: {angle}")
        await ctx.report_progress(1, 3, "Loading voice constraints")

    system = (
        "You write X threads as IntellAIgent: a practitioner-contrarian voice. "
        "Rules: concrete over abstract; NO hype words (unlock, leverage, "
        "revolutionize, seamless, game-changer); pick a defensible side; "
        "measure honestly including costs and failures; short punchy sentences. "
        "Each tweet must stand alone. Output EXACTLY one tweet per line, each "
        "line prefixed with its number and a slash, like '1/'. No other text."
    )
    user = (
        f"Source headline: {source_title}\n"
        f"Source summary: {source_summary}\n"
        f"Angle to build around: {angle}\n"
        f"Write a {num_tweets}-tweet thread."
    )

    if ctx:
        await ctx.report_progress(2, 3, "Calling the model")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    resp = await client.messages.create(
        model=settings.default_model,
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw = resp.content[0].text.strip()

    # Parse "N/ ..." lines into individual tweets; fall back to non-empty lines.
    tweets = [
        line.strip()
        for line in raw.splitlines()
        if line.strip() and re.match(r"^\d+\s*/", line.strip())
    ]
    if not tweets:
        tweets = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    if ctx:
        await ctx.report_progress(3, 3, "Done")

    return ThreadDraft(
        tweets=tweets,
        tweet_count=len(tweets),
        angle=angle,
    )


@mcp.resource("voice://intellaigent")
def voice_guide() -> str:
    """The IntellAIgent voice guide — the practitioner-contrarian rules.

    Read-only reference the client can pull before drafting or reviewing any
    content, so the voice stays consistent across tools and sessions.
    """
    return """# IntellAIgent Voice Guide

## Core stance
Practitioner-contrarian. You've built the thing you're writing about and you
measured it. You pick a defensible side and defend it. You are not a
thought-leader narrating trends from the outside.

## Rules
- Concrete over abstract. Name the tool, the number, the specific tradeoff.
- No hype words: unlock, leverage, revolutionize, seamless, game-changer,
  cutting-edge, supercharge, paradigm, synergy.
- No empty intensifiers: very, really, truly, deeply, incredibly.
- Measure honestly. State the cost and the failure, not just the win.
- Short, punchy sentences. Cut hedging. Say the claim or don't.
- Walk back your own verdict when the evidence says so — that earns trust.

## Structure for a post
Hook that reframes → the concrete evidence → the honest cost → the thesis
landing on judgment, not tooling.

## The thesis spine
"The moat moved up the stack." The model is the commodity; the craft is what
you build around it, and the judgment of when it's worth the overhead.

## Footer
@intellaigent · Decode the Future 🔹
"""


# Card template structures, keyed by name. In a real setup these might live
# in a file or DB; inlined here for clarity.
_CARD_TEMPLATES = {
    "dispatch": {
        "name": "dispatch",
        "eyebrow_style": "uppercase, amber, bordered pill, top-left",
        "headline_size_px": 52,
        "layout": "headline top, subtitle below, single accent, grid overlay",
        "use_for": "single-claim posts, hot takes, theses",
    },
    "matrix": {
        "name": "matrix",
        "eyebrow_style": "uppercase, amber, bordered pill, top-left",
        "headline_size_px": 46,
        "layout": "headline, then stacked comparison rows (condition | pick)",
        "use_for": "decision matrices, comparisons, 'which X for Y' posts",
    },
    "stack": {
        "name": "stack",
        "eyebrow_style": "uppercase, amber, bordered pill, top-left",
        "headline_size_px": 46,
        "layout": "headline, then vertical layered rows, one row emphasized",
        "use_for": "layered concepts, hierarchies, 'the X, not the Y' posts",
    },
}


@mcp.resource("card-template://{name}")
def card_template(name: str) -> dict:
    """Return the structure spec for a named IntellAIgent card template.

    Available templates: dispatch (single-claim), matrix (comparison),
    stack (layered concept). The client can pull the right one before
    calling generate_card_spec so the layout matches the post type.

    Args:
        name: The template name — 'dispatch', 'matrix', or 'stack'.
    """
    template = _CARD_TEMPLATES.get(name.lower())
    if template is None:
        available = ", ".join(sorted(_CARD_TEMPLATES))
        raise ValueError(f"No card template named '{name}'. Available: {available}.")
    return template


@mcp.prompt
def angle_from_headline(headline: str, summary: str = "") -> str:
    """Generate IntellAIgent angles from a headline. Surfaces as a slash command.

    Args:
        headline: The source headline to find angles on.
        summary: Optional short summary for more context.
    """
    return (
        f"Read the IntellAIgent voice guide at voice://intellaigent first.\n\n"
        f"Source headline: {headline}\n"
        f"{f'Summary: {summary}' if summary else ''}\n\n"
        f"Give me 3 sharp, practitioner-contrarian angles on this. For each: "
        f"one declarative sentence stating the angle, then one sentence on why "
        f"it lands with a builder audience. No hype words. Pick defensible, "
        f"specific takes — not 'X is the future'."
    )


@mcp.prompt
def thread_from_notes(notes: str, num_tweets: int = 6) -> str:
    """Draft an IntellAIgent X thread from rough notes. Surfaces as a slash command.

    Args:
        notes: Your rough notes or bullet points for the thread.
        num_tweets: How many tweets (default 6).
    """
    return (
        f"Read the IntellAIgent voice guide at voice://intellaigent first, then "
        f"draft a {num_tweets}-tweet X thread from these notes.\n\n"
        f"Notes:\n{notes}\n\n"
        f"Rules: each tweet stands alone; concrete over abstract; no hype words; "
        f"measure honestly including costs; short punchy sentences. Number each "
        f"tweet like '1/'. After drafting, run check_voice on the result and "
        f"fix anything it flags."
    )


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
