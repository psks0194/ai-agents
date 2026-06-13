"""A Conversation abstraction that wraps the message-list mess.

Every memory strategy (summarization, sliding window, scratchpad) will be
a method on this class. The abstraction earns its keep when you have 3+ strategies.
"""

from dataclasses import dataclass, field

from anthropic import Anthropic
from rich.console import Console

from week2_agent_patterns.config import settings


console = Console()


@dataclass
class Conversation:
    """Wraps the messages list with helpful methods."""

    model: str = "claude-haiku-4-5-20251001"
    system: str = "You are a helpful assistant."
    messages: list[dict] = field(default_factory=list)
    cumulative_input_tokens: int = 0
    cumulative_output_tokens: int = 0

    def __post_init__(self) -> None:
        self._client = Anthropic(api_key=settings.anthropic_api_key)

    @property
    def turn_count(self) -> int:
        """Number of complete user→assistant turns."""
        return len(self.messages) // 2

    @property
    def estimated_tokens(self) -> int:
        """Very rough estimate: 4 chars per token. Not exact, but useful for decisions."""
        total_chars = len(self.system)
        for m in self.messages:
            content = m["content"]
            if isinstance(content, str):
                total_chars += len(content)
            else:
                # content blocks (lists) — rough estimate
                for block in content:
                    if isinstance(block, dict) and "text" in block:
                        total_chars += len(block["text"])
        return total_chars // 4

    def send(self, user_message: str, max_tokens: int = 512) -> str:
        """Send a message, append response to history, return text."""
        self.messages.append({"role": "user", "content": user_message})

        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=self.system,
            messages=self.messages,
        )

        text = "".join(b.text for b in response.content if b.type == "text")
        self.messages.append({"role": "assistant", "content": text})

        self.cumulative_input_tokens += response.usage.input_tokens
        self.cumulative_output_tokens += response.usage.output_tokens

        return text

    def total_cost_usd(
        self, input_price_per_m: float = 1.00, output_price_per_m: float = 5.00
    ) -> float:
        """Calculate running cost. Defaults are Haiku 4.5 pricing."""
        return (
            self.cumulative_input_tokens * input_price_per_m
            + self.cumulative_output_tokens * output_price_per_m
        ) / 1_000_000

    def print_stats(self) -> None:
        """Print a one-line summary of the conversation's state."""
        console.print(
            f"[dim][turns={self.turn_count} | "
            f"history_msgs={len(self.messages)} | "
            f"est_tokens={self.estimated_tokens:,} | "
            f"cum_in={self.cumulative_input_tokens:,} | "
            f"cum_out={self.cumulative_output_tokens:,} | "
            f"cost=${self.total_cost_usd():.4f}][/dim]"
        )


# ============================================================
# Summarization strategy
# ============================================================

SUMMARIZER_SYSTEM = (
    "You are a conversation summarizer. Compress the messages provided "
    "into a concise summary that preserves the essential context for "
    "continuing the conversation. \n\n"
    "Capture: \n"
    " - Key facts established (names, decisions, technical choices)\n"
    " - The user's goals and constraints\n"
    " - Important tradeoffs that were discussed\n"
    " - Anything the assistant promised to remember\n\n"
    "Be specific. 'They discussed Python' is useless. "
    "'User is building a Python async CLI using httpx, chose asyncio.gather, "
    "implementing retries with exponential backoff' is useful. \n\n"
    "Aim for ~150 words. Write in third-person."
)


def _summarize_messages(messages: list[dict], client: Anthropic, model: str) -> str:
    """Compress a list of messages into a summary string."""
    # Render the messages as readable text
    rendered = []
    for m in messages:
        content = m["content"]
        if isinstance(content, str):
            text = content
        else:
            text = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
        rendered.append(f"{m['role'].upper()}: {text}")

    convo_text = "\n\n".join(rendered)

    response = client.messages.create(
        model=model,
        max_tokens=400,
        system=SUMMARIZER_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Summarize this conversation:\n\n{convo_text}\n\n"
                    "Produce the summary."
                ),
            }
        ],
    )

    return "".join(b.text for b in response.content if b.type == "text")


# Add as a method on Conversation (extend the class)
def summarize_oldest(
    self: Conversation,
    keep_recent_turns: int = 3,
) -> str | None:
    """Summarize the oldest messages, keeping the most recent N turns intact.

    Returns the summary text (or None if nothing to summarize).
    Modifies self.messages in place.
    """
    # Each turn is 2 messages (user + assistant)
    keep_msgs = keep_recent_turns * 2

    if len(self.messages) <= keep_msgs:
        return None  # nothing old to summarize yet

    old = self.messages[:-keep_msgs]
    recent = self.messages[-keep_msgs:]

    summary = _summarize_messages(old, self._client, self.model)

    # Replace old messages with a single user message containing the summary
    # We use 'user' role + system-style framing, because Anthropic doesn't
    # let us insert arbitrary 'system' messages mid-conversation.
    summary_message = {
        "role": "user",
        "content": (
            f"[SUMMARY OF EARLIER CONVERSATION]\n\n{summary}\n\n"
            "[END SUMMARY — continuing conversation now]"
        ),
    }
    summary_response = {
        "role": "assistant",
        "content": "Understood, I have the context.",
    }

    self.messages = [summary_message, summary_response] + recent
    return summary


# Attach the method to the class
Conversation.summarize_oldest = summarize_oldest
