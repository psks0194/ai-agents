"""Run both versions on the same topic, print a side-by-side comparison table.

This is the artifact for the Friday IntellAIgent post.
"""

from rich.console import Console
from rich.table import Table

from week3_langgraph_pydantic_ai import research_note_pai, research_note_lg


console = Console()


def main() -> None:
    topic = (
        "What's the current state of MCP (Model Context Protocol) adoption "
        "across major AI tools in mid-2026? Be specific about which tools "
        "support it and how."
    )

    console.print(f"[bold]Topic:[/bold] {topic}\n")
    console.print("=" * 70 + "\n")

    # Run Pydantic AI
    pai_note, pai_metrics = research_note_pai.run(topic)
    research_note_pai.display(pai_note, pai_metrics)

    console.print("\n" + "=" * 70 + "\n")

    # Run LangGraph
    lg_note, lg_metrics = research_note_lg.run(topic)
    research_note_lg.display(lg_note, lg_metrics)

    # Comparison table
    console.print("\n" + "=" * 70 + "\n")
    table = Table(title="Head-to-head — same topic, both frameworks")
    table.add_column("Metric", style="bold")
    table.add_column("Pydantic AI", style="cyan", justify="right")
    table.add_column("LangGraph", style="magenta", justify="right")

    table.add_row(
        "Wall time",
        f"{pai_metrics['elapsed_sec']:.2f}s",
        f"{lg_metrics['elapsed_sec']:.2f}s",
    )
    table.add_row(
        "Input tokens",
        f"{pai_metrics['input_tokens']:,}",
        f"{lg_metrics['input_tokens']:,}",
    )
    table.add_row(
        "Output tokens",
        f"{pai_metrics['output_tokens']:,}",
        f"{lg_metrics['output_tokens']:,}",
    )

    # Rough cost (Haiku 4.5 pricing: $1/M in, $5/M out)
    pai_cost = (
        pai_metrics["input_tokens"] / 1_000_000 * 1.00
        + pai_metrics["output_tokens"] / 1_000_000 * 5.00
    )
    lg_cost = (
        lg_metrics["input_tokens"] / 1_000_000 * 1.00
        + lg_metrics["output_tokens"] / 1_000_000 * 5.00
    )
    table.add_row(
        "Cost (¢)",
        f"{pai_cost * 100:.3f}",
        f"{lg_cost * 100:.3f}",
    )
    table.add_row(
        "Steps",
        f"{pai_metrics['requests']} requests",
        f"{lg_metrics['graph_steps']} graph steps",
    )

    console.print(table)

    # Lines of code (manual measure)
    console.print("\n[bold]Lines of code (agent file only):[/bold]")

    pai_lines = sum(1 for _ in open(research_note_pai.__file__))
    lg_lines = sum(1 for _ in open(research_note_lg.__file__))
    console.print(f"  Pydantic AI: {pai_lines} lines")
    console.print(f"  LangGraph:   {lg_lines} lines")
    console.print(f"  Ratio: {lg_lines / pai_lines:.2f}x")


if __name__ == "__main__":
    main()
