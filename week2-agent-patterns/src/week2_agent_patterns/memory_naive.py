"""The naive approach: keep appending messages, send the whole history every turn.

This is what every Day 1 chat does. Watch what happens to the token count
as the conversation grows.
"""

from anthropic import Anthropic
from rich.console import Console
from rich.table import Table

from week2_agent_patterns.config import settings


console = Console()
MODEL = "claude-haiku-4-5-20251001"
SYSTEM = (
    "You are a helpful Python expert. Keep answers concise but complete. "
    "Reference earlier parts of the conversation when relevant."
)


def run_conversation_with_metrics(turns: list[str]) -> None:
    """Run a fixed conversation and print per-turn token cost growth."""
    client = Anthropic(api_key=settings.anthropic_api_key)
    messages: list[dict] = []

    metrics = []
    cumulative_input = 0
    cumulative_output = 0

    for i, user_msg in enumerate(turns, start=1):
        messages.append({"role": "user", "content": user_msg})

        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=SYSTEM,
            messages=messages,
        )

        assistant_text = "".join(b.text for b in response.content if b.type == "text")
        messages.append({"role": "assistant", "content": assistant_text})

        cumulative_input += response.usage.input_tokens
        cumulative_output += response.usage.output_tokens

        metrics.append(
            {
                "turn": i,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cumulative_input": cumulative_input,
                "cumulative_output": cumulative_output,
                "history_size": len(messages),
            }
        )

        console.print(
            f"[dim]Turn {i}: {response.usage.input_tokens} in / "
            f"{response.usage.output_tokens} out[/dim]"
        )

    # Display the cost curve
    table = Table(title="Per-turn token cost — naive accumulation")
    table.add_column("Turn", justify="right")
    table.add_column("In", justify="right", style="cyan")
    table.add_column("Out", justify="right", style="magenta")
    table.add_column("Cum. In", justify="right", style="cyan")
    table.add_column("History size", justify="right", style="dim")

    for m in metrics:
        table.add_row(
            str(m["turn"]),
            f"{m['input_tokens']:,}",
            f"{m['output_tokens']:,}",
            f"{m['cumulative_input']:,}",
            str(m["history_size"]),
        )
    console.print(table)

    # Pricing — Haiku 4.5 in May 2026
    cost_usd = (cumulative_input * 1.00 + cumulative_output * 5.00) / 1_000_000
    console.print(
        f"\n[bold]Total cost:[/bold] ${cost_usd:.4f} "
        f"([cyan]{cumulative_input:,}[/cyan] in / [magenta]{cumulative_output:,}[/magenta] out)"
    )


def main() -> None:
    # A multi-turn conversation that builds on itself
    turns = [
        "I'm building a Python CLI that fetches data from 3 APIs concurrently.",
        "Should I use httpx or requests for this?",
        "I picked httpx. What's the right async pattern for fanning out 3 calls?",
        "Got it — using asyncio.gather. How do I handle errors gracefully?",
        "Now I want to add a retry with exponential backoff for failures. Pattern?",
        "How would I add a timeout on top of the retry?",
        "If a call fails after all retries, should I raise or return None?",
        "I'm going to add structured logging. What library should I use?",
        "Should the logger be passed in or imported as a module-level singleton?",
        "Last question: how do I write tests for this whole async flow?",
    ]
    run_conversation_with_metrics(turns)


if __name__ == "__main__":
    main()
