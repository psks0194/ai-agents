"""Same long conversation as memory_naive — but with periodic summarization.

Watch what happens to per-turn input tokens as the conversation grows.
Should grow until threshold is hit, drop sharply after summarization,
then grow again.
"""

from rich.console import Console
from rich.table import Table

from week2_agent_patterns.conversation import Conversation


console = Console()


SUMMARIZE_THRESHOLD_TOKENS = 1500  # trigger summary when estimated tokens exceed this


def run_with_summarization(turns: list[str]) -> None:
    convo = Conversation(
        model="claude-haiku-4-5-20251001",
        system=(
            "You are a helpful Python expert. Keep answers concise but complete. "
            "Reference earlier parts of the conversation when relevant."
        ),
    )

    metrics = []
    for i, user_msg in enumerate(turns, start=1):
        # Check if we need to summarize BEFORE sending the next message
        if convo.estimated_tokens > SUMMARIZE_THRESHOLD_TOKENS:
            console.print(
                f"\n[yellow]>> est_tokens={convo.estimated_tokens} > "
                f"threshold={SUMMARIZE_THRESHOLD_TOKENS}, summarizing oldest...[/yellow]"
            )
            summary = convo.summarize_oldest(keep_recent_turns=3)
            if summary:
                console.print(f"[dim italic]Summary: {summary[:200]}...[/dim italic]\n")

        convo.send(user_msg)
        metrics.append(
            {
                "turn": i,
                "history_size": len(convo.messages),
                "est_tokens": convo.estimated_tokens,
                "cum_in": convo.cumulative_input_tokens,
                "cum_out": convo.cumulative_output_tokens,
            }
        )

        console.print(
            f"[dim]Turn {i}: history={len(convo.messages)} msgs, "
            f"est={convo.estimated_tokens} tokens[/dim]"
        )

    # Display the curve
    table = Table(title="Per-turn growth — WITH summarization")
    table.add_column("Turn", justify="right")
    table.add_column("History msgs", justify="right")
    table.add_column("Est. tokens", justify="right", style="cyan")
    table.add_column("Cum. In", justify="right", style="dim")

    for m in metrics:
        table.add_row(
            str(m["turn"]),
            str(m["history_size"]),
            f"{m['est_tokens']:,}",
            f"{m['cum_in']:,}",
        )
    console.print(table)
    console.print(f"\n[bold]Total cost:[/bold] ${convo.total_cost_usd():.4f}")


def main() -> None:
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
    run_with_summarization(turns)


if __name__ == "__main__":
    main()
