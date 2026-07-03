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
from fastmcp import FastMCP

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


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
