"""In-memory tests for the IntellAIgent content-ops server.

Pass the server object to Client() and it connects in-memory — no subprocess,
no network. These test the deterministic tools and resources. The LLM-backed
and network tools are marked 'integration' and skipped by default.
"""

import pytest
from fastmcp import Client

from intellaigent_mcp.models import CardPalette
from intellaigent_mcp.server import mcp


# ============================================================
# Discovery
# ============================================================


async def test_tools_are_registered():
    """All four tools should be discoverable."""
    async with Client(mcp) as client:
        tools = await client.list_tools()
        names = {t.name for t in tools}
        assert {
            "fetch_feed",
            "generate_card_spec",
            "check_voice",
            "draft_thread",
        } <= names


# ============================================================
# generate_card_spec (deterministic)
# ============================================================


async def test_card_spec_resolves_accent():
    """The chosen accent should resolve to the brand hex."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "generate_card_spec",
            {
                "headline": "The harness, not the model",
                "subtitle": "when it's worth it",
                "accent": "cyan",
            },
        )
        # result.data is the deserialized structured output.
        spec = result.data
        assert spec.accent_hex == CardPalette().cyan
        assert spec.width == 1600 and spec.height == 900


async def test_card_spec_rejects_long_headline():
    """A too-long headline should raise a tool error the model can read."""
    async with Client(mcp) as client:
        with pytest.raises(Exception) as exc:
            await client.call_tool(
                "generate_card_spec",
                {"headline": "x" * 100, "subtitle": "s", "accent": "cyan"},
            )
        assert "under 90" in str(exc.value)


# ============================================================
# check_voice (deterministic)
# ============================================================


async def test_check_voice_flags_hype():
    """Hype words should be flagged and passed should be False."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_voice",
            {
                "text": "This will revolutionize your workflow and seamlessly unlock synergy."
            },
        )
        report = result.data
        assert report.passed is False
        flagged = {issue.term for issue in report.issues}
        assert "revolutionize" in flagged
        assert "unlock" in flagged


async def test_check_voice_passes_clean_text():
    """Clean, concrete text should pass."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "check_voice",
            {
                "text": "I measured it. The harness cost 7x tokens and saved 40 files of context."
            },
        )
        report = result.data
        assert report.passed is True
        assert report.issue_count == 0


# ============================================================
# Resources
# ============================================================


async def test_voice_resource_returns_guide():
    """The voice guide resource should return the rules."""
    async with Client(mcp) as client:
        result = await client.read_resource("voice://intellaigent")
        text = result[0].text
        assert "practitioner-contrarian" in text.lower()


async def test_card_template_resolves_by_name():
    """The card-template resource template should resolve a known name."""
    async with Client(mcp) as client:
        result = await client.read_resource("card-template://matrix")
        text = result[0].text
        assert "comparison" in text.lower()


async def test_card_template_unknown_name_errors():
    """An unknown template name should error with the available list."""
    async with Client(mcp) as client:
        with pytest.raises(Exception) as exc:
            await client.read_resource("card-template://nonexistent")
        assert "available" in str(exc.value).lower()


# ============================================================
# Integration tests — network / LLM. Skipped by default.
# Run with: uv run pytest -m integration
# ============================================================


@pytest.mark.integration
async def test_fetch_feed_live():
    """Hits a real feed — network required."""
    async with Client(mcp) as client:
        result = await client.call_tool(
            "fetch_feed", {"feed_url": "https://tldr.tech/api/rss/tech", "limit": 3}
        )
        items = result.data
        assert len(items) <= 3
