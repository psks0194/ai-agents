"""Typed I/O models for the content-ops tools.

FastMCP converts these into output schemas, so clients receive structured,
addressable data — not opaque text. This is the typed-boundary discipline
from the agent weeks, applied at the protocol edge.
"""

from pydantic import BaseModel, Field


# ============================================================
# Card spec (output of generate_card_spec)
# ============================================================


class CardPalette(BaseModel):
    """The IntellAIgent brand palette, resolved into the spec."""

    bg: str = "#061015"
    bg2: str = "#0a1a22"
    line: str = "#15303a"
    ink: str = "#e8f4f4"
    muted: str = "#6f8a92"
    cyan: str = "#2fe6e0"
    magenta: str = "#ff4fd8"
    amber: str = "#ffb35a"


class CardSpec(BaseModel):
    """A complete 1600x900 branded card spec for the Playwright renderer."""

    width: int = 1600
    height: int = 900
    eyebrow: str = Field(description="Small uppercase label, e.g. 'Dispatch'")
    headline: str = Field(description="The main card headline")
    subtitle: str = Field(description="One-line supporting subtitle")
    accent_hex: str = Field(description="The chosen accent color, resolved to hex")
    grid_size_px: int = 64
    footer: str = "@intellaigent · Decode the Future 🔹"
    palette: CardPalette = Field(default_factory=CardPalette)


# ============================================================
# Voice report (output of check_voice)
# ============================================================


class VoiceIssue(BaseModel):
    """One flagged voice problem."""

    kind: str = Field(description="hype_word | hedge | intensifier | vague_abstraction")
    term: str = Field(description="The offending word or phrase found")
    suggestion: str = Field(description="What to do instead")


class VoiceReport(BaseModel):
    """Result of linting text against IntellAIgent voice rules."""

    passed: bool = Field(description="True if no critical voice issues were found")
    issue_count: int
    issues: list[VoiceIssue]
    note: str = Field(description="One-line summary of the verdict")


# ============================================================
# Thread draft (output of draft_thread)
# ============================================================


class ThreadDraft(BaseModel):
    """A drafted X thread in the IntellAIgent voice."""

    tweets: list[str] = Field(description="Ordered tweets, each standing alone")
    tweet_count: int
    angle: str = Field(description="The angle the thread was built around")
